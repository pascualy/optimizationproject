import json
import sys
from jsonschema import validate, ValidationError
from pathlib import Path

schema = {
    "required": ["location", "budget", "products"],
    "properties": {
        "location": {
            "type": "string"
        },
        "budget": {
            "required": ["initial", "monthly"],
            "properties": {
                "initial": {
                    "type": "number"
                },
                "monthly": {
                    "type": "number"
                }
            }
        },
        "products": {
            "type": "array",
            "items": {"$ref": "#/$defs/product"}
        }
    },
    "$defs": {
        "product": {
            "type": "object",
            "required": ["name", "utility_type", "energy_type", "opening_cost", "incremental_cost",
                         "maintenance_cost", "capacity", "amortization"],
            "properties": {
                "name": {
                    "type": "string"
                },
                "utility_type": {
                    "type": "string",
                    "enum": ["electricity", "heat"],
                    "error_msg": "Only supported utility types are [electricity, heat]"
                },
                "energy_type": {
                    "type": "string",
                    "enum": ['solar', 'wind', 'geothermal', 'biomass', 'storage'],
                    "error_msg": "Only supported energy types are [solar, wind, geothermal, biomass, storage]"
                },
                "opening_cost": {
                    "type": "number"
                },
                "incremental_cost": {
                    "type": "number"
                },
                "maintenance_cost": {
                    "type": "number"
                },
                "capacity": {
                    "type": "number"
                },
                "amortization": {
                    "type": "number"
                },
            },
            "anyOf": [
                {
                  "properties": {
                    "energy_type": {"const": "solar"}
                  },
                  "required": ["capacity"]
                },
                {
                  "properties": {
                    "energy_type": {"const": "wind"}
                  },
                  "required": ["capacity"]
                },
                {
                    "properties": {
                        "energy_type": {"const": "storage"}
                    },
                    "required": ["capacity"]
                },
                {
                  "properties": {
                    "energy_type": {"const": "geothermal"}
                  },
                }
              ]
        }
    }
}


class ConfigError(Exception):
    pass


def load_and_validate(config_path):
    with open(config_path) as fp:
        config = json.load(fp)

    return validate_config(config)


def validate_config(config):
    validate(instance=config, schema=schema)

    return config


def get_location_options():
    capacity_data = Path(__file__).parent.parent / 'data' / 'capacity_data'
    return list(set([','.join([word.capitalize() for word in path.stem.split('_')[2:-1]] +
                              [word.upper() for word in path.stem.split('_')[-1:]]
                              ) for path in capacity_data.glob('./*')]))

def get_config_options():
    capacity_data = Path(__file__).parent.parent / 'configs'
    return list(set([' '.join([word.capitalize() for word in path.stem.split('_')]
                              ) for path in capacity_data.glob('./*')]))

