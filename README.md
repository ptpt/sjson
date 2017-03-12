# sjson

SJSON is a shorthand JSON notation that helps you write complex JSON
in a simple way.

## Installation

Clone the repo and put `sjson.py` in your `$PATH`.

## Examples

Arrays and primitive types except strings are similar to
JSON. Quotation marks around a string are optional.

```sh
python3 sjson.py '[1, 2e3, hello, "world", null, false, true]'
```
```json
[1, 2000.0, "hello", "world", null, false, true]
```

A member in the SJSON object can have multiple segments (separated by
dots) to specify the path of the value.

```sh
python3 sjson.py 'foo.bar.hello:12 foo.bar.world:"12"'
# which is equivalent to
python3 sjson.py 'foo.bar:{hello:12 world:"12"}'
```
```json
{"foo": {"bar": {"hello": 12, "world": "12"}}}
```

Construct a GeoJSON feature:
```sh
python3 sjson.py '
type: Feature
geometry: {type:Point coordinates:[13.2, 43.12]}
id:1001
properties.stats:{population:123e03 area: 3323} properties.name:/dev/null'
```
```json
{
  "type": "Feature",
  "geometry": {
    "type": "Point",
    "coordinates": [
      13.2,
      43.12
    ]
  },
  "id": 1001,
  "properties": {
    "stats": {
      "population": 123000,
      "area": 3323
    },
    "name": "/dev/null"
  }
}
```

In ElasticSearch when you need to construct complex query in JSON, you
can use `sjson` to help:

```sh
python3 sjson.py "
aggs.histogram:{
    aggs.users.terms:{field:date size:3}
    data_histogram:{field:date format:yyyy-MM-dd interval:1M}
}

query.constant_score.bool.must:[
    geo_shape.geom.indexed_shape:{id:1001 index:countries path:shape type:countries},
    range.date:{gte:2017-01-22 lt:2017-01-23}
]
" # | curl localhost:80/els/users -d@-
```

```json
{
  "aggs": {
    "histogram": {
      "aggs": {
        "users": {
          "terms": {
            "field": "date",
            "size": 3
          }
        }
      },
      "data_histogram": {
        "field": "date",
        "format": "yyyy-MM-dd",
        "interval": "1M"
      }
    }
  },
  "query": {
    "constant_score": {
      "bool": {
        "must": [
          {
            "geo_shape": {
              "geom": {
                "indexed_shape": {
                  "id": 1001,
                  "index": "countries",
                  "path": "shape",
                  "type": "countries"
                }
              }
            }
          },
          {
            "range": {
              "date": {
                "gte": "2017-01-22",
                "lt": "2017-01-23"
              }
            }
          }
        ]
      }
    }
  }
}
```
