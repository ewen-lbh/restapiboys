from typing import *
from restapiboys import log
import re
from restapiboys.utils import (
    get_path,
    is_list_uniformely_typed,
    replace_whitespace_in_keys,
    yaml,
)
from restapiboys.fields import (
    ResourceFieldConfig,
    resolve_synonyms,
    ResourceFieldConfigError,
    resolve_field_name_shortcuts,
)

NATIVE_FIELD_TYPES = [
    "integer",
    "string",
    "number",
    "datetime",
    "time",
    "date",
    "boolean",
    "slug",
]

NATIVE_TYPES_MAPPING = {int: "integer", str: "string", float: "number", bool: "boolean"}


def get_custom_types() -> Dict[str, List[ResourceFieldConfig]]:
    """
    Gets all custom types and resolve their fields' config
    """
    types = {}
    types_configs: Dict[str, Dict[str, Dict[str, Any]]] = yaml.load_file(
        get_path("types.yaml")
    )
    for name, fields in types_configs.items():
        resolved_fields = []
        for field_name, field_config in fields.items():
            # print(f"Resolving type field {field_name!r}")
            # First replace whitespace from keys with underscores
            field_config = replace_whitespace_in_keys(field_config)
            # Then resolve synonyms
            field_config = resolve_synonyms(field_config)
            # Then convert the dict into a ResourceFieldConfig
            field = ResourceFieldConfig(name=field_name, **field_config)
            # Raise error if this field's type is custom
            if field.type not in NATIVE_FIELD_TYPES:
                raise ResourceFieldConfigError(
                    f"In type {name!r}: fields of custom types should be of native types only. Field {field.name!r} has type {field.type!r}."
                )
            # Then resolve field name shortcuts
            field = resolve_field_name_shortcuts(field)
            # Append to the fields list
            resolved_fields.append(field)

        types[name] = resolved_fields

    return types


def resolve_custom_types(
    fields: List[ResourceFieldConfig],
) -> List[ResourceFieldConfig]:
    """
    Replaces a custom type by a native one
    in each field.
    A list of fields is required because custom
    types consisting of multiple fields are resolved
    by appending _new_ fields in the field list, eg:
    ```yaml
    my_type:
      start:
        is: date
      end:
        is: date
    ---
    my_object:
        is: my_type
    ```
    
    is resolved as:
    ```yaml
    my_object.start:
      is: date
    my_object.end:
      is: date
    ```
    """
    ARRAYED_TYPE_MARKER_PATTERN = re.compile(r"^(.+)\[\]$")
    resolved_fields = []
    for field in fields:
        # Start by resolving arrays-of notation (typename[])
        if ARRAYED_TYPE_MARKER_PATTERN.match(field.type):
            type_name = ARRAYED_TYPE_MARKER_PATTERN.search(field.type).groups()[0]
            field = field._replace(multiple=True, type=type_name)

        # print(f"Resolving types for field {field.name!r}")
        # Is a native type
        if field.type in NATIVE_FIELD_TYPES:
            resolved_fields.append(field)
            continue

        # Is a relational type
        RELATIONAL_TYPE_DECLARATION_PATTERN = re.compile(r"^<([^>]+)>(\[\])?$")
        if RELATIONAL_TYPE_DECLARATION_PATTERN.match(field.type):
            referenced_endpoint = RELATIONAL_TYPE_DECLARATION_PATTERN.search(
                field.type
            ).groups()
            # print(f"    Is a relational type to endpoint {referenced_endpoint!r}.")
            # Incomprehensible
            # ImportError: cannot import name 'get_endpoints_routes' from 'restapiboys.endpoints' (/mnt/d/projects/restapiboys/restapiboys/endpoints.py)
            # if '/' + referenced_endpoint not in get_endpoints_routes():
            #     raise ResourceFieldConfigError(f"{field.name!r} defines a relation with an undefined endpoint ({referenced_endpoint!r}). Create the endpoint in `endpoints/{referenced_endpoint}.yaml`")
            resolved_fields.append(field)
            continue

        # Is an unknown type
        custom_types = get_custom_types()
        if field.type not in custom_types.keys():
            raise ResourceFieldConfigError(
                f"{field.name!r}'s declared type ({field.type!r}) is not known. Please define it in `types.yaml`"
            )

        # Is a custom type
        type_config = custom_types[field.type]
        # Single-field type
        if len(type_config) == 1 and type_config[0].name == "_":
            field = ResourceFieldConfig(
                **{
                    **type_config[0]._asdict(),  # Attributes of the type as a base
                    **field._asdict(),  # Attributes defined by the field to override the type's
                }
            )
            # The previous statement also overrides the field.type, so we need to set it to the custom field's "_".type
            field._replace(type=type_config[0].type)
            # Add to list
            resolved_fields.append(field)
        # Multi-field type
        else:
            # print(f"    Custom type has subfields: {type_config!r}")
            # Each field defined by the custom type
            for subfield in type_config:
                # Create the new field name: field.subfield
                generated_field_name = field.name + "." + subfield.name
                # If the name "field.subfield" is already defined, we don't add it (overriden by the endpoint's fields config)
                if generated_field_name in [f.name for f in fields]:
                    continue
                # Add this field of this custom type to the endpoint's fields config
                resolved_fields.append(subfield._replace(name=generated_field_name))
    return resolved_fields


def infer_field_type(field_config: Dict[str, Any]) -> Optional[str]:
    # If the field has a whitelist with all elements of the same type
    # we can infer that the field's type is the one from these elements
    if field_config.get("whitelist"):
        whitelist = field_config["whitelist"]
        if is_list_uniformely_typed(whitelist):
            python_type = type(whitelist[0])
            infered_type = NATIVE_TYPES_MAPPING.get(python_type)
            return infered_type
    if field_config.get("max_length") or field_config.get("min_length"):
        return "string"
    if field_config.get("minimum") or field_config.get("maximum"):
        return "number"
    if field_config.get("default"):
        python_type = type(field_config["default"])
        infered_type = NATIVE_TYPES_MAPPING.get(python_type)
        return infered_type
    return None
