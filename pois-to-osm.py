"""
Reads NPS POI data as newline-delimited GeoJSON features from STDIN, converts
attributes to OSM-compatible tags, and writes the resulting GeoJSON features
to STDOUT.
"""

import sys
import json


def squeeze(string):
    """Replace any runs of whitespace in string with a single space"""
    return " ".join(string.split())


def trailhead_to_osm(props):
    tags = {}

    tags["highway"] = "trailhead"

    name = squeeze(props.get("POINAME").strip())
    if name:
        if name.endswith("Trail"):
            name = name + "head"
        elif not name.endswith("Trailhead"):
            name = name + " Trailhead"
        elif name == "Trailhead":
            name = None
    
        
    tags["name"] = name

    return tags


def properties_to_osm(props):
    """Converts a feature properties dict to OSM tags"""
    tags = None
    
    match props.get("POITYPE"):
        case "Trailhead":
            tags = trailhead_to_osm(props)
        # TODO: other POI types...

    if tags:
        tags["operator"] = "National Park Service"
    
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
