# Fetch Open Ski Map data

A script to fetch & sanitize open ski map KML.

Everything here is thanks to the volunteers & hard work at [Skimap.org](https://skimap.org).

## Pre-reqs

* Python 3
* urllib, lxml, BeautifulSoup4

Suggest using a `virtualenv` for the Python 3 & packages. [There's a guide for that](https://gist.github.com/sarah-j-smith/1a054d5efa3ee7f32c1ee52f17a8a0f1).

```bash
pip install urllib
pip install lxml
pip install BeautifulSoup4
```

# Usage

```bash
python3 ski-run-browser.py
```

Produces files `osm-ski-area-{$ID}.kml`

## Hosting

Main index file is available at [https://s3-ap-southeast-2.amazonaws.com/skimap/ski_areas.kml](https://s3-ap-southeast-2.amazonaws.com/skimap/ski_areas.kml).

For example:

https://s3-ap-southeast-2.amazonaws.com/skimap/osm-1-2017-03-27.kml

This lists all the `ID` numbers of the ski areas.  Once an ID number is selected the filtered, sanitized KML is available at:

https://s3-ap-southeast-2.amazonaws.com/skimap/osm-ski-area-{$ID}.kml

The original unfiltered, but still sanitized KML is available at:

https://s3-ap-southeast-2.amazonaws.com/skimap/unfilt-osm-ski-area-{$ID}.kml

If you're me, and have access to write the S3 bucket:

```bash
mkdir -p osm
cp -f *.kml osm/. && aws s3 sync osm s3://skimap/  --acl public-read
```
