"""
Reads NPS Trail data as newline-delimited GeoJSON features from STDIN, converts
attributes to OSM-compatible tags, and writes the resulting GeoJSON features to
STDOUT.
"""

import json
import re
import sys


def squeeze(string):
    """Replace any runs of whitespace in string with a single space"""
    return " ".join(string.split())


def tokenize(string):
    return re.findall(r"\s|[\w\'.]+|[^\w\'.]+", string)


def highway_tags(props):
    trailtype = props["TRLTYPE"]
    match trailtype:
        case "Standard Terra Trail" | "Standard/Terra Trail" | "Trail":
            return {"highway": "path"}
        case "Sidewalk":
            return {"highway": "footway", "footway": "sidewalk"}
        case "Pedestrian Path":
            return {"highway": "footway"}
        case "Steps":
            return {"highway": "steps"}
        case _:
            return None


def status(props):
    match props["TRLSTATUS"]:
        case "Existing" | "1" | "Maintained":
            return {}
        case "Temporarily Closed":
            return {"access": "no"}
        case "Decommissioned":
            return {"access": "no", "disused": "yes"}
        case "Unmaintained":
            return {"maintained": "no"}
        case "Proposed":
            raise ValueError("Proposed status")


ABBREVIATIONS = {
    "N": "North",
    "S": "South",
    "SO": "South",
    "E": "East",
    "W": "West",
    "CG": "Campground",
    "TR": "Trail",
}

BAD_NAMES = {
    "Pathway",
    "Mutli-Use Path",
    "Bike Path",
    "Horse Trail",
    "Horse Riding Trail",
    "Park Trail",
    "Field Trail",
    "Campground Trail",
    "Beach Trail",
    "Forest Trail",
    "Utility Area Trails",
    "Trail",
    "Summit",
}

BAD_NAME_PATTERNS = {"Campsite Spur", "sidewalk", "Walkways", "Pathways"}

SPECIAL_CASES = {}


def name(props):
    name = props["TRLNAME"]

    if not name or name in BAD_NAMES:
        return None

    if any(re.search(regex, name) for regex in BAD_NAME_PATTERNS):
        return None

    name = squeeze(name.replace("/", " / ")).strip()

    if name.isnumeric():
        return None

    words = []
    for token in tokenize(name):
        if token.isspace() or re.match("^[()-/]$", token):
            words.append(token)
            continue

        word = token  # .upper()
        if word == "-":
            words.append(word)
            continue

        abbr = ABBREVIATIONS.get(word.upper()) or ABBREVIATIONS.get(
            word.upper().replace(".", "")
        )
        if abbr:
            word = abbr
        elif word in SPECIAL_CASES:
            word = SPECIAL_CASES[word]
        elif re.match("[\w']+", word):
            word = word.capitalize()

        words.append(word)

    if not words:
        return None

    if not any(
        val in words
        for val in [
            "Road",
            "Trail",
            "Path",
            "Route",
            "Connector",
            "Tie",
            "Loop",
            "Spur",
        ]
    ):
        words += [" ", "Trail"]

    if words[0].islower():
        words[0] = words[0].capitalize()
    if words[-1].islower():
        words[-1] = words[-1].capitalize()

    return "".join(words)


def operator(props):
    match props["MAINTAINER"]:
        case "National Park Service" | "NPS" | "Unknown":
            # half of trails in dataset have MAINTAINER = "Unknown";
            # let's assume NPS for these
            return "National Park Service"
        case "Forest Service":
            return "US Forest Service"
        case "Bureau of Land Management":
            return "US Bureau of Land Management"
        case _:
            return None


def informal(props):
    if name := props["TRLNAME"]:
        return "social trail" in name.lower()
    else:
        return False


SURFACE_MAP = {
    "Asphalt": "asphalt",
    "Brick": "bricks",
    "Concrete": "concrete",
    "Earth": "earth",
    "Gravel": "gravel",
    "Metal": "metal",
    "Native Material": "ground",
    "Native": "ground",
    "Paver": "paving_stones",
    "Sand": "sand",
    "Soil": "soil",
    "Wood Chips": "woodchips",
    "Wood": "wood",
}


def surface(props):
    return SURFACE_MAP.get(props["TRLSURFACE"])


def _any_term_in_str(terms, str):
    return any(term in str for term in terms)


def foot(props):
    use = props["TRLUSE"].lower()
    terms = ["hike", "hiking", "pedestrian", "walking"]
    return "designated" if _any_term_in_str(terms, use) else "no"


def bicycle(props):
    use = props["TRLUSE"].lower()
    terms = ["bike", "bicycle"]
    return "designated" if _any_term_in_str(terms, use) else "no"


def horse(props):
    use = props["TRLUSE"].lower()
    terms = ["horse", "saddle", "equestrian"]
    return "designated" if _any_term_in_str(terms, use) else "no"


def atv(props):
    use = props["TRLUSE"].lower()
    terms = ["atv", "all-terrain vehicle"]
    return "designated" if _any_term_in_str(terms, use) else "no"


def motorcycle(props):
    use = props["TRLUSE"].lower()
    terms = ["motorcycle"]
    return "designated" if _any_term_in_str(terms, use) else "no"


def properties_to_osm(props):
    """Converts a feature properties dict to OSM tags"""
    tags = None

    if highway := highway_tags(props):
        tags = highway

        try:
            tags |= status(props)
        except Exception:
            return None

        tags["name"] = name(props)
        tags["surface"] = surface(props)

        if informal(props):
            tags["informal"] = "yes"
        else:
            tags["operator"] = operator(props)

        tags["foot"] = foot(props)
        tags["bicycle"] = bicycle(props)
        tags["horse"] = horse(props)
        tags["atv"] = atv(props)
        tags["motorcycle"] = motorcycle(props)

        tags["TRLNAME"] = props["TRLNAME"]
        tags["TRLUSE"] = props["TRLUSE"]

    return tags


def feature_to_osm(feature):
    """Converts a single GeoJSON feature to OSM-compatible form"""
    if tags := properties_to_osm(feature["properties"]):
        feature["properties"] = tags
        return feature
    else:
        return None


if __name__ == "__main__":
    for line in sys.stdin:
        feature = json.loads(line)
        try:
            result = feature_to_osm(feature)
        except Exception as e:
            print(feature["properties"])
            raise e

        if result:
            print(json.dumps(result))
