import json
import sys
from jsonschema import validate, ValidationError

schema = {
    "required": ["demand", "budget", "grid", "products"],
    "properties": {
        "demand": {
            "required": ["monthly_electricity_demand", "monthly_heat_demand"],
            "properties": {
                "monthly_electricity_demand": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    }
                },
                "monthly_heat_demand": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    }
                }
            }
        },
        "budget": {
            "required": ["initial", "monthly"],
            "properties": {
                "inital":{
                    "type": "number"
                },
                "monthly": {
                    "type": "number"
                }
            }
        },
        "grid": {
            "required": ["grid_cost_kwh", "grid_cost_env"],
            "properties": {
                "grid_cost_kwh":{
                    "type": "number"
                },
                "grid_cost_env": {
                    "type": "number"
                }
            }
        },
        "products": {
            "type": "array",
            "items": { "$ref": "#/$defs/product" }
        }
    },
    "$defs": {
        "product": {
            "type": "object",
            "required": ["name", "utility_type", "energy_type", "opening_cost", "incremental_cost",
                         "maintenance_cost", "monthly_capacity", "amoritization"],
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
                    "enum": ['solar', 'wind', 'geothermal', 'biomass'],
                    "error_msg": "Only supported energy types are [solar, wind, geothermal, biomass]"
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
                "monthly_capacity": {
                    "type": "array",
                    "items": {
                        "type": "number"
                    }
                },
                "amoritization": {
                    "type": "number"
                },

            }
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
    error_string = None
    try:
        validate(instance=config, schema=schema)
    except ValidationError as e:
        error_string = e.schema["error_msg"]

    if error_string:
        print('Failed to parse configuration file:')
        print(error_string)
        sys.exit(1)



    return config