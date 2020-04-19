from typing import *
import re

# Incomprehensible ImportError: cannot import name 'get_endpoints_routes' from 'restapiboys.endpoints' (/mnt/d/projects/restapiboys/restapiboys/endpoints.py)
# from restapiboys.endpoints import get_endpoints_routes
from restapiboys.utils import replace_whitespace_in_keys

CONFIG_KEYS_SYNONYMS = {
    "type": ["is"],
    "whitelist": ["one_of"],
    "blacklist": ["prohibit"],
    "max_length": ["maximum_length"],
    "min_length": ["minimum_length"],
    "maximum": ["max"],
    "minimum": ["min"],
    "defaults_to": ["default", "defaults", "initial_value"],
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
    defaults_to: Any = None
    allow_empty: bool = True
    read_only: bool = False
    positive: Optional[
        bool
    ] = None  # only positive if True, only negative if False, either if True


def resolve_synonyms(field_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolves synonyms in field configuration keys, as defined
    by `CONFIG_KEYS_SYNONYMS`.
    """
    resolved = {}
    print(f"    Resolving synonyms. Before: {field_config!r}")
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
    print(f"    Synonyms resolved to {resolved!r}")
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
        field._replace(required=True)

    if COMPUTED_FIELD_PATTERN.match(field.name):
        real_field_name = COMPUTED_FIELD_PATTERN.search(field.name).groups()[0]
        field._replace(computed=True)
        field._replace(read_only=True)

    # Remove shortcuts from the field name
    field._replace(name=real_field_name)

    return field


from restapiboys.types import infer_field_type, resolve_custom_types


def resolve_fields_config(
    fields_config: Dict[str, Dict[str, Any]]
) -> List[ResourceFieldConfig]:
    fields = []
    for field_name, field_config in fields_config.items():
        print(f"Resolving field {field_name!r}")
        # First replace whitespace from keys with underscores
        field_config = replace_whitespace_in_keys(field_config)
        # Then resolve synonyms
        field_config = resolve_synonyms(field_config)
        # Then convert the dict into a ResourceFieldConfig
        if "type" not in field_config.keys():
            # Try to infer type
            infered_type = infer_field_type(field_config)
            if infered_type:
                field_config["type"] = infered_type
            else:
                raise ResourceFieldConfigError(
                    f"The field {field_name!r} does not declare a type"
                )
        # TODO #1: check for unknown config keys
        field = ResourceFieldConfig(name=field_name, **field_config)
        # Then resolve field name shortcuts
        field = resolve_field_name_shortcuts(field)
        # Append to the fields list
        fields.append(field)
    # Then resolve custom types
    fields = resolve_custom_types(fields)
    #
    return fields
