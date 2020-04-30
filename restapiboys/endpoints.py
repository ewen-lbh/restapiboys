from datetime import datetime
from enum import Enum
from restapiboys.directives import RESOURCE_DIRECTIVES_SYNONYMS
from typing import *
from restapiboys import log
import os
import re
import slugify
from restapiboys.http import RequestMethod
from restapiboys.fields import (
    ResourceFieldConfig,
    ResourceFieldConfigError,
    resolve_fields_config,
)
from restapiboys.utils import (
    flatten_dict,
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
                yield subendpoint._replace(route="/" + directory + subendpoint.route)
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
            identifier=string_to_identifier(filetitle).replace("_", "-"),
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


def add_default_fields_to_request_data(
    resource: ResourceConfig, data: Dict[str, Any]
) -> Dict[str, Any]:
    data = flatten_dict(data)
    for field in resource.fields:
        # Required field must be already set
        # Computed field are handled by another function
        if field.required or field.computed:
            continue
        # If the field is already set
        if field.name in data.keys():
            continue
        # If the default value is computed, compute it
        if is_default_value_computed(field):
            # Get the code to run
            code = field.default.replace("= ", "", 1)
            default = compute_computed_fields(code)
        # Else the default is a static value, just grab it
        else:
            default = field.default
        # Add to the returned dict
        data[field.name] = default
    return data


def add_computed_values_to_request_data(
    resource: ResourceConfig,
    new_data: Dict[str, Any],
    old_data: Dict[str, Any],
    exec_context_data: Dict[str, Any],
) -> Dict[str, Any]:
    new_data = flatten_dict(new_data)
    computed_fields = [f for f in resource.fields if f.computed]
    for field in computed_fields:
        if value_needs_recomputation(field, new_data, old_data):
            # TODO: check if "set" key is in "computation"
            code = field.computation["set"]
            computed = compute_computed_fields(code, context=exec_context_data)
            log.debug("Computed value of field {}: {}", field.name, f"{computed!r}")
            new_data[field.name] = computed
    return new_data


def compute_computed_fields(code: str, context: Optional[Dict[str, Any]] = None) -> Any:
    # Set the default value of the argumet `context`
    context = context or {}
    # Create the locals dict
    context = {
        "now": lambda: datetime.now().isoformat(timespec="seconds"),
        "slugify": slugify.slugify,
        **context,  # The context passed as an arg overrides "base" context entries
    }
    # Run the code and get the returned value
    exec(f"global __computed__; __computed__ = {code}", globals(), context)
    # Return the value
    global __computed__
    return __computed__


def is_default_value_computed(field: ResourceFieldConfig) -> Any:
    return type(field.default) is str and field.default.startswith("= ")


def value_needs_recomputation(
    field: ResourceFieldConfig, new_data: Dict[str, Any], old_data: Dict[str, Any]
) -> bool:
    react_on = field.computation["react"]
    # Handle react's special value '*'
    if react_on == "*":
        return True
    # Handle one-item shortcut
    if type(react_on) is not list:
        react_on = [react_on]
    # If any of the fields to react on has its value different in the `new_data`
    # compared to the `old_data`, we need to recompute the field
    # Get the map of field_name: value changed?
    changes = {key: new_data.get(key) != old_data.get(key) for key in react_on}
    log.debug("\tValues that changed:")
    for key, changed in changes.items():
        if changed:
            log.debug(
                "\t- {}: {} ~> {}",
                key,
                f"{new_data.get(key)!r}",
                f"{old_data.get(key)!r}",
            )
    return any(changes.values())
