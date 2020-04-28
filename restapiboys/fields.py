from typing import *
from restapiboys import log
import re
from restapiboys.utils import (
    get_path,
    is_list_uniformely_typed,
    replace_whitespace_in_keys,
    resolve_synonyms_in_dict,
    yaml,
)

CONFIG_KEYS_SYNONYMS = {
    "type": ["is"],
    "whitelist": ["one_of"],
    "blacklist": ["prohibit"],
    "max_length": ["maximum_length"],
    "min_length": ["minimum_length"],
    "maximum": ["max"],
    "minimum": ["min"],
    "default": ["defaults_to", "defaults", "in`itial_value"],
    "allow_empty": ["can_be_empty", "empty_allowed", "empty"],
    "read_only": ["read-only", "readonly"],
}


class ResourceFieldConfigError(ValueError):
    """ Used when the field's config is wrong """

    pass


class ResourceFieldComputationConfig(NamedTuple):
    set: str
    react: Union[str, list] = "*"
    when: List[str] = []


# MAYBE: treat max/min as max/min _length when is: string ?
class ResourceFieldConfig(NamedTuple):
    name: str  # The field name
    type: str
    computation: Optional[ResourceFieldComputationConfig] = None
    serialization: Optional[str] = None
    whitelist: List[Any] = []
    blacklist: List[Any] = []
    validation: Dict[str, str] = {}
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    minimum: Union[int, float, None] = None
    maximum: Union[int, float, None] = None
    computed: bool = False  # autoset
    required: bool = False  # autoset
    default: Any = None
    allow_empty: bool = False
    read_only: bool = False
    positive: Optional[
        bool
    ] = None  # only positive if True, only negative if False, either if True
    multiple: bool = False  # Can be defined by the shortcut typename[] on the `type` property.


def resolve_synonyms(field_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolves synonyms in field configuration keys, as defined
    by `CONFIG_KEYS_SYNONYMS`.
    """
    return resolve_synonyms_in_dict(CONFIG_KEYS_SYNONYMS, field_config)


def resolve_field_name_shortcuts(field: ResourceFieldConfig) -> ResourceFieldConfig:
    """
    Resolves syntactic shortcuts in the field name to
    regular config keys.
    Example:
    ```yaml
    required_field*:
        is: string
    computed_field():
        is: number
    ```
    becomes
    ```yaml
    required_field:
        required: true
        is: string
    computed_field:
        computed: true
        read-only: yes
        is: number
    ```
    """
    # Extracts field_name from field_name*
    REQUIRED_FIELD_PATTERN = re.compile(r"^([^*]+)\*$")
    # Extracts field_name from field_name()
    COMPUTED_FIELD_PATTERN = re.compile(r"^([^(]+)\(\)$")

    real_field_name = field.name

    # Really whish that I could use the := operator...
    if REQUIRED_FIELD_PATTERN.match(field.name):
        real_field_name = REQUIRED_FIELD_PATTERN.search(field.name).groups()[0]
        field = field._replace(required=True)

    if COMPUTED_FIELD_PATTERN.match(field.name):
        real_field_name = COMPUTED_FIELD_PATTERN.search(field.name).groups()[0]
        field = field._replace(computed=True)
        field = field._replace(read_only=True)

    # Remove shortcuts from the field name
    field = field._replace(name=real_field_name)

    return field


def resolve_fields_config(
    fields_config: Dict[str, Dict[str, Any]]
) -> List[ResourceFieldConfig]:
    resolved_fields = []
    for field_name, field_config in fields_config.items():
        orig_field_config = field_config
        log.debug("Resolving field {}", field_name)
        # First replace whitespace from keys with underscores
        field_config = replace_whitespace_in_keys(field_config)
        # Then resolve synonyms
        field_config = resolve_synonyms(field_config)
        log.debug(
            "\tResolved synonyms: {} ~> {}",
            orig_field_config.keys(),
            field_config.keys(),
        )
        # Then convert the dict into a ResourceFieldConfig
        if "type" not in field_config.keys():
            # Try to infer type
            infered_type = infer_field_type(field_config)
            if infered_type:
                field_config["type"] = infered_type
                log.debug("\tType infered to {}", infered_type)
            else:
                raise ResourceFieldConfigError(
                    f"The field {field_name!r} does not declare a type"
                )
        # TODO #1: check for unknown config keys
        field = ResourceFieldConfig(name=field_name, **field_config)
        # Then resolve field name shortcuts
        field = resolve_field_name_shortcuts(field)
        # Append to the fields list
        resolved_fields.append(field)
    # Then resolve custom types
    fields = resolve_custom_types(resolved_fields)
    #
    return fields


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
    log.debug("Resolving custom types on fields {}", [f.name for f in fields])
    for field in fields:
        # Start by resolving array-of notation (typename[])
        if ARRAYED_TYPE_MARKER_PATTERN.match(field.type):
            type_name = ARRAYED_TYPE_MARKER_PATTERN.search(field.type).groups()[0]
            field = field._replace(multiple=True, type=type_name)

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
                    # Attributes of the type as a base
                    **type_config[0]._asdict(),
                    # Attributes defined by the field to override the type's
                    **{
                        # Don't override field properties set to `None`
                        k: v for k, v in field._asdict().items() if v is not None 
                    },
                }
            )
            # The previous statement also overrides the field.type, so we need to set it to the custom field's "_".type
            field = field._replace(type=type_config[0].type)
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

# TODO: Resolve allow_empty: False to min_length = 1
# TODO: Resolve allow_empty: True and type is sizable to min_length=0
