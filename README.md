# Slovenia - bus routes in OpenStreetMap

[![Update](https://github.com/openstreetmap-si/bus-routes-osm-lpp/actions/workflows/update.yaml/badge.svg)](https://github.com/openstreetmap-si/bus-routes-osm-lpp/actions/workflows/update.yaml)

## Ljubljana - Ljubljanski Potniški Promet (LPP)

Fetches the data from [LPP bus schedule](https://www.lpp.si/sites/default/files/lpp_vozniredi/iskalnik/index.php) and saves it into [data/lpp](./data/lpp/):

* [`lines.csv`: Bus lines](data/lpp/lines.csv)
* [`stops.csv`: Bus stops](data/lpp/stops.csv)
* [`lines_stops.csv`: Bus stops on all bus lines](data/lpp/lines_stops.csv)

```mermaid
erDiagram
          lines ||--o{ lines_stops : "has stops"
          lines {
              int id PK "3-4-digit bus line ID"
              string line "Line number on buses"
              string lineExtra "Extra line descriptor (seasonal, temporary)"
              string nameFrom "Start stop name"
              string nameTo "End stop name"
          }
          stops ||--o{ lines_stops : "for lines"
          stops {
              int id PK "6-digit bus stop ID"
              string name "Bus stop name"
          }
          lines_stops {
              int lineId FK "3-4-digit bus line ID"
              int direction "1=forward, 2=backwards"
              int sequence "Stop number in the given direction"
              int stopId FK "6-digit bus stop ID"
          }
```

## Maribor - Marprom

Fetches data from [Marprom WEBMap](https://www.marprom.si/webmap/website/webmap.php) and saves it into [data/marprom](./data/marprom/):

* [`mainlines.geojson`: Bus lines](data/marprom/mainlines.geojson)
* [`stops.geojson`: Bus stops](data/marprom/stops.geojson)

## Development

1. `python3 -m venv venv` or `virtualenv -p python3 venv`
2. `source venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python update.py`
