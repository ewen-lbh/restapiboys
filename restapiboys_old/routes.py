import re
import os
import keyword
from restapiboys.fields import FIELD_TYPES_MAPPING
import warnings
from typing import List, Dict, Any, NamedTuple, Union, Optional
from restapiboys.utils import get_path, yaml
from restapiboys.http import RequestMethod
from restapiboys.fields import ResourceFieldConfig
from restapiboys.endpoints import ResourceConfig

RESOURCE_FIELD_CONFIG_KEY_SYNONYMS = {
    "type": ["is"],
    "whitelist": ["one_of"],
    "blacklist": ["prohibit"],
    "max_length": ["maximum_length"],
    "min_length": ["minimum_length"],
    "maximum": ["max"],
    "minimum": ["min"],
    "defaults_to": ["default", "defaults", "initial_value"],
}
SPECIAL_ROUTES_PATTERN = re.compile(r"^__.+__$")
ENDPOINT_DIRECTIVE_KEY_PATTERN = re.compile(r"^\$(.+)$")
ENDPOINT_REQUIRED_FIELD_PATTERN = re.compile(r"^([^*]+)\*$")
ENDPOINT_COMPUTED_FIELD_PATTERN = re.compile(r"^([^(]+)\(\)$")


def get_route_names(in_folder="endpoints", parent="") -> List[str]:
    directory = get_path(in_folder)
    route_names = list()
    for fileordirectory in os.listdir(directory):
        if os.path.isdir(fileordirectory):
            route_names += get_route_names(
                in_folder=os.path.join(in_folder, fileordirectory),
                parent=fileordirectory,
            )
        else:
            filetitle, ext = os.path.splitext(fileordirectory)
            if ext in (".yaml", ".yml") and not SPECIAL_ROUTES_PATTERN.match(filetitle):
                route_names.append(f"{parent}/{filetitle}")
    return route_names


def get_route_config(route) -> ResourceConfig:
    """
    Gets the `route`'s configuration, resolving:
    - field name shorthands (field*, field())
    - custom types
    - synonyms for field config keys
    """
    # Remove initial slash from route when getting the path
    filepath = get_path("endpoints", route.replace("/", "", 1) + ".yaml")
    fields_config = yaml.load_file(filepath)
    types = yaml.load_file(get_path("types.yaml"))
    route_indentifier = route_to_indentifier(route)
    resolved_fields_config = {}
    allowed_methods = ResourceConfig(
        endpoint="", identifier=""
    ).allowed_methods  # Get the default value
    for field_name, field_config in fields_config.items():
        # Remove whitespace from keys
        field_config = normalize_keys(field_config)
        # Resolve synonyms
        field_config = resolve_field_config_keys_synonyms(field_config)

        if ENDPOINT_DIRECTIVE_KEY_PATTERN.match(field_name):
            field_name = ENDPOINT_REQUIRED_FIELD_PATTERN.search(field_name).groups()[0]
            if field_name == "allowed_methods":
                allowed_methods = [m.upper() for m in field_config]
            continue

        if ENDPOINT_REQUIRED_FIELD_PATTERN.match(field_name):
            field_name = ENDPOINT_REQUIRED_FIELD_PATTERN.search(field_name).groups()[0]
            field_config["required"] = True

        if ENDPOINT_COMPUTED_FIELD_PATTERN.match(field_name):
            field_name = ENDPOINT_COMPUTED_FIELD_PATTERN.search(field_name).groups()[0]
            field_config["computed"] = True

        # Infer type from one_of values
        if (
            "type" not in field_config.keys()
            and field_config.get("whitelist")
            and list_has_uniform_type(field_config["whitelist"])
        ):
            # TODO: handle single-valued whitelist/blacklists
            # Get the native python type
            field_type = type(field_config["whitelist"][0])
            # Translate to a field type, if possible
            if field_type in FIELD_TYPES_MAPPING.keys():
                field_config["type"] = FIELD_TYPES_MAPPING[field_type]

        custom_type = types.get(field_config["type"])
        # TODO: multi-valued (object) custom types
        if custom_type and custom_type.get("_"):
            # TODO: clean custom_type separately
            del field_config["type"]
            field_config = {**custom_type["_"], **field_config}
            # Remove whitespace from keys
            field_config = normalize_keys(field_config)
            # Resolve synonyms
            field_config = resolve_field_config_keys_synonyms(field_config)

        resolved_fields_config[field_name] = field_config

    resolved_fields_config = [
        ResourceFieldConfig(**config, name=name)
        for name, config in resolved_fields_config.items()
    ]

    return ResourceConfig(
        fields=resolved_fields_config,
        identifier=route_indentifier,
        allowed_methods=allowed_methods,
        endpoint=route,
    )


# TODO: Move to helpers
def list_has_uniform_type(obj: list) -> bool:
    """
    Checks if the values of a list are all of the same type.
    """
    types = set([type(v) for v in obj])
    return len(types) == 1


def resolve_field_config_keys_synonyms(field_config: Dict[str, Any]) -> dict:
    """
    Resolves synonyms of field configuration keys
    into their "primary" key, as defined by
    `RESOURCE_FIELD_CONFIG_KEY_SYNONYMS`.
    """
    resolved = {}
    for key, value in field_config.items():
        was_synonym = False
        for primary, synonyms in RESOURCE_FIELD_CONFIG_KEY_SYNONYMS.items():
            if key in synonyms or key == primary:
                resolved[primary] = value
                was_synonym = True
        if not was_synonym:
            resolved[key] = value
    return resolved


# TODO: move to helpers
def normalize_keys(field_config: Dict[str, Any]) -> dict:
    """
    Removes whitespace from config keys
    """
    normalized = {}
    PATTERN = re.compile(r"")
    for key, value in field_config.items():
        key = re.sub(r"\s", "_", key)
        normalized[key] = value
    return normalized


def route_to_indentifier(route: str) -> str:
    # Replace invalid characters with an underscore
    route = re.sub(r"[^0-9a-zA-Z_]", "_", route)

    # Remove leading characters until we find a letter or underscore
    route = re.sub(r"^[^a-zA-Z]+", "", route)

    # Check if its not a python keyword.
    # If it is, add a '_' in front.
    if keyword.iskeyword(route):
        warnings.warn(
            f"You have an endpoint that conflicts with a python keyword ({route}). Reference that endpoint in python code by prepending the endpoint with an underscore."
        )
        route = "_" + route

    return route
