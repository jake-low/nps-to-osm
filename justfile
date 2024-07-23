# extent := "-124.733 45.543 -116.917 49.005" # WA
extent := "-114.052 36.998 -109.041 42.002" # UT

all: pois

pois:
    ogr2ogr -f GeoJSON -if GeoJSON -spat_srs EPSG:4326 -spat {{extent}} \
        POIs.geojson \
        ~/Downloads/NPS_-_Points_of_Interest_\(POIs\)_-_Geographic_Coordinate_System.geojson

    jq -c '.features[]' POIs.geojson > POIs.ndjson
    python pois-to-osm.py < POIs.ndjson > POIs.osm.ndjson
    jq -cs '{ type: "FeatureCollection", features: . }' POIs.osm.ndjson > POIs.osm.geojson
