Python scripts to convert US National Park Service POI data to an OSM-compatible schema.

Supported feature types:
- Trailheads
- (more to come soon)

## Data sources

You can download the required datasets from the following URL in GeoJSON format.
https://public-nps.opendata.arcgis.com/datasets/nps-points-of-interest-pois-geographic-coordinate-system/explore

## Running

The `justfile` in this repo can be used to run the conversion using the [`just`](https://github.com/casey/just) command runner. Or you can just paste the same series of commands into your shell.

The input files are assumed to be in `~/Downloads`; edit the script to change this path if required.

The code requires GDAL (for the `ogr2ogr` command), `jq`, and a fairly recent version of Python (3.10+).

## License

This code is available under the ISC license. See the LICENSE file for details.
