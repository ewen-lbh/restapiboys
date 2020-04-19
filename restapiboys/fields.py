from restapiboys.endpoints import get_endpoints_names
from restapiboys.utils import get_path, yaml, replace_whitespace_in_keys
from typing import *
import re

CONFIG_KEYS_SYNONYMS = {
    "type": ["is"],
    "whitelist": ["one_of"],
    "blacklist": ["prohibit"],
    "max_length": ["maximum_length"],
    "min_length": ["minimum_length"],
    "maximum": ["max"],
    "minimum": ["min"],
    "defaults_to": ["default", "defaults", "initial_value"],
}

NATIVE_FIELD_TYPES = [
    "integer",
    "string",
    "number",
    "datetime",
    "time",
    "date",
    "boolean",
]


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
    defaults_to: Any = None


def resolve_synonyms(field_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolves synonyms in field configuration keys, as defined
    by `CONFIG_KEYS_SYNONYMS`.
    """
    resolved = {}
    print(f'    Resolving synonyms. Before: {field_config!r}')
    # Iterate over the configuration key-value pairs for this field
    for key, value in field_config.items():
        was_in_synonyms = False
        # Iterate over the synonyms
        for primary, synonyms in CONFIG_KEYS_SYNONYMS.items():
            # If the current config kv-pair for this field is a synonym
            if key == primary or key in synonyms:
                was_in_synonyms = True
                # Assign the "primary" key to the value
                resolved[primary] = value
        # If the current kv-pair does not have synonyms defined
        if not was_in_synonyms:
            # Assign the kv's key to its value
            resolved[key] = value
    print(f'    Synonyms resolved to {resolved!r}')
    return resolved


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
        field._replace(required=True)

    if COMPUTED_FIELD_PATTERN.match(field.name):
        real_field_name = COMPUTED_FIELD_PATTERN.search(field.name).groups()[0]
        field._replace(computed=True)

    # Remove shortcuts from the field name
    field._replace(name=real_field_name)

    return field


# TODO: move to types.py
def get_custom_types() -> Dict[str, Dict[str, ResourceFieldConfig]]:
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
            print(f'Resolving type field {field_name!r}')
            # First replace whitespace from keys with underscores
            field_config = replace_whitespace_in_keys(field_config)
            # Then resolve synonyms
            field_config = resolve_synonyms(field_config)
            # Then convert the dict into a ResourceFieldConfig
            field = ResourceFieldConfig(name=field_name, **field_config)
            # Raise error if this field's type is custom
            if field.type not in NATIVE_FIELD_TYPES:
                raise ResourceFieldConfigError(f"In type {name!r}: fields of custom types should be of native types only. Field {field.name!r} has type {field.type!r}.")
            # Then resolve field name shortcuts
            field = resolve_field_name_shortcuts(field)
            # Append to the fields list
            resolved_fields.append(field)
        
        types[name] = fields
        
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
    resolved_fields = []
    for field in fields:
        print(f'Resolving types for field {field.name!r}')
        # Is a native type
        if field.type in NATIVE_FIELD_TYPES:
            resolved_fields.append(field)

        # Is an unknown type
        custom_types = get_custom_types()
        if field.type not in custom_types.keys():
            raise ResourceFieldConfigError(
                f"{field.name!r}'s declared type ({field.type!r}) is not known. Please define it in `types.yaml`"
            )
            
        # Is a relational type
        RELATIONAL_TYPE_DECLARATION_PATTERN = re.compile(r'^<([^>]+)>(\[\])?$')
        if RELATIONAL_TYPE_DECLARATION_PATTERN.match(field.type):
            referenced_endpoint, multiple_marker = RELATIONAL_TYPE_DECLARATION_PATTERN.search(field.type).groups()
            is_multiple = multiple_marker == '[]'
            if '/' + referenced_endpoint not in get_endpoint_names():
                raise ResourceFieldConfigError(f"{field.name!r} defines a relation with an undefined endpoint ({referenced_endpoint!r}). Create the endpoint in `endpoints/{referenced_endpoint}.yaml`")
            resolved_fields.append(field)

        # Is a custom type
        type_config = custom_types[field.type]
        # Single-field type
        if len(type_config.keys()) == 1 and list(type_config.keys())[0] == "_":
            field = ResourceFieldConfig(
                **type_config["_"],  # Attributes of the type as a base
                **field._asdict(),  # Attributes defined by the field to override the type's
            )
            # The previous statement also overrides the field.type, so we need to set it to the custom field's "_".type
            field.type = type_config["_"].type
            # Add to list
            resolved_fields.append(field)
        # Multi-field type
        else:
            print(f'    Custom type has subfields: {type_config.keys()!r}')
            # Each field defined by the custom type
            for subfield_name, subfield_config in type_config.items():
                # Create the new field name: field.subfield
                generated_field_name = field.name + "." + subfield_name
                # If the name "field.subfield" is already defined, we don't add it (overriden by the endpoint's fields config)
                if generated_field_name in [f.name for f in fields]:
                    continue
                # Add this field of this custom type to the endpoint's fields config
                resolved_fields.append(
                    subfield_config._replace(name=generated_field_name)
                )
    return resolved_fields

def resolve_fields_config(
    fields_config: Dict[str, Dict[str, Any]]
) -> List[ResourceFieldConfig]:
    fields = []
    for field_name, field_config in fields_config.items():
        print(f'Resolving field {field_name!r}')
        # First replace whitespace from keys with underscores
        field_config = replace_whitespace_in_keys(field_config)
        # Then resolve synonyms
        field_config = resolve_synonyms(field_config)
        # Then convert the dict into a ResourceFieldConfig
        field = ResourceFieldConfig(name=field_name, **field_config)
        # Then resolve field name shortcuts
        field = resolve_field_name_shortcuts(field)
        # Append to the fields list
        fields.append(field)
    # Then resolve custom types
    fields = resolve_custom_types(fields)
    #
    return fields
