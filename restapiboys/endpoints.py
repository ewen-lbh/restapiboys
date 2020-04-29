from enum import Enum
from restapiboys.directives import RESOURCE_DIRECTIVES_SYNONYMS
from typing import *
from restapiboys import log
import os
import re
from restapiboys.http import RequestMethod
from restapiboys.fields import (
    ResourceFieldConfig,
    ResourceFieldConfigError,
    resolve_fields_config,
)
from restapiboys.utils import (
    replace_whitespace_in_keys,
    resolve_synonyms_in_dict,
    resolve_synonyms_to_primary,
    string_to_identifier,
    yaml,
    get_path,
)


class ResourceConfig(NamedTuple):
    route: str
    identifier: str
    python_identifier: str
    fields: List[ResourceFieldConfig] = []
    allowed_methods: List[RequestMethod] = [
        RequestMethod.POST,
        RequestMethod.GET,
        RequestMethod.PATCH,
        RequestMethod.DELETE,
    ]
    inherits: Optional[str] = None


def get_endpoints_routes(parent: str = "") -> Iterable[str]:
    folder = get_path("endpoints", parent)
    for filename in os.listdir(folder):
        if os.path.isdir(filename):
            parent = os.path.join(folder, filename)
            for endpoint in get_endpoints_routes(parent):
                yield endpoint

        filetitle, extension = os.path.splitext(filename)
        if extension != ".yaml":
            continue

        if is_special_endpoint(filetitle):
            continue

        yield filetitle


def get_endpoints(directory="endpoints") -> Iterable[ResourceConfig]:
    for filename in os.listdir(get_path(directory)):
        # Get the full path
        filepath = get_path(directory, filename)
        # If its a directory, recursively get endpoints
        if os.path.isdir(filepath):
            # Get the sub endpoints
            subendpoints = get_endpoints(filepath)
            for subendpoint in subendpoints:
                # Prepend the current directory
                yield subendpoint._replace(
                    route="/" + directory + subendpoint.route
                )
        # Get the extension and file title (same as the endpoint)
        filetitle, extension = os.path.splitext(filename)
        if extension != ".yaml":
            continue
        if is_special_endpoint(filetitle):
            continue
        # Load the config file to get the fields from the endpoint
        # This file can either have:
        # - 1 document, in this case we have no directives
        # - 2 documents, the first one defines directives & the second one fields.
        documents: Tuple[Dict[str, Any], Dict[str, Any]] = yaml.load_file(
            filepath, multiple_documents=True
        )
        if len(documents) == 1:
            fields, directives = documents[0], {}
        elif len(documents) == 2:
            directives, fields = documents
        else:
            raise ResourceFieldConfigError(
                f"The endpoint defined in {filename} defines more than 2 documents."
            )
        # Remove whitespace from directives
        directives = replace_whitespace_in_keys(directives)
        # Resolve synonyms
        directives = resolve_synonyms_in_dict(RESOURCE_DIRECTIVES_SYNONYMS, directives)
        # Turn it into a ResourceFieldConfig list
        fields = resolve_fields_config(fields)
        # Create a ResourceConfig
        endpoint = ResourceConfig(
            route=f"/{filetitle}",
            fields=list(fields),
            identifier=string_to_identifier(filetitle).replace('_', '-'),
            python_identifier=string_to_identifier(filetitle),
            **directives,
        )
        # Inherit values from __default__
        endpoint = inherit_default_endpoint(endpoint)
        # yield it
        yield endpoint


def get_endpoint_defaults_fields() -> Optional[List[ResourceFieldConfig]]:
    """
    Gets the `ResourceConfig` object defined in `endpoints/__default__.yaml`,
    or `None` if no such file is found.
    """
    filepath = get_path("endpoints", "__default__.yaml")
    if not os.path.isfile(filepath):
        return None
    contents = yaml.load_file(filepath)
    return resolve_fields_config(contents)


def is_special_endpoint(endpoint):
    """
    Checks if the endpoint file is to be treated as a special one
    (uses python's double undescore, __special-file__.yaml)
    """
    PATTERN = re.compile(r"^__(.+)__$")
    return PATTERN.match(endpoint)


def inherit_default_endpoint(endpoint: ResourceConfig) -> ResourceConfig:
    """
    Adds fields from the __default__ endpoint (endpoints/__default__.yaml)
    """
    # Get the fields from __default__
    default_fields = get_endpoint_defaults_fields()
    # If the __default__ file is not found, no defaults are defined, nothing to inherit from
    if default_fields is None:
        return endpoint
    # Get all the field names defined by the endpoint
    endpoint_field_names = [field.name for field in endpoint.fields]
    # Add fields from __default__ when they aren't overriden by the endpoint
    merged_fields = [
        field for field in default_fields if field.name not in endpoint_field_names
    ]
    # Add the fields from the endpoint
    merged_fields += endpoint.fields
    # Return the ResourceConfig
    return ResourceConfig(**{**endpoint._asdict(), "fields": merged_fields})


def get_resource_config_of_route(route: str) -> Optional[ResourceConfig]:
    resources = get_endpoints()
    for resource in resources:
        if resource.route == route:
            return resource
    return None


def get_resource_headers(resource: ResourceConfig) -> dict:
    return {"Access-Control-Allow-Methods": ", ".join(resource.allowed_methods)}
