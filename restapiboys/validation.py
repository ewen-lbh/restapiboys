from json.decoder import JSONDecodeError
from restapiboys.fields import NATIVE_TYPES_MAPPING
from restapiboys.endpoints import get_endpoints, get_resource_config_of_route
from restapiboys.http import Request, RequestMethod, BODYLESS_REQUEST_METHODS
from restapiboys import log
from typing import *
import json
from restapiboys.utils import swap_keys_and_values
import arrow
from slugify import slugify


def validate_request_data(req: Request) -> Optional[Tuple[str, Dict[str, Any]]]:
    log.debug("Starting validation")
    resource = get_resource_config_of_route(req.route)
    fields_by_name = {field.name: field for field in resource.fields}
    # If the request has no associated resource config, this is a custom route.
    # Skip traditional validation, go straigth to custom validators
    if not resource:
        return None
    if req.method in BODYLESS_REQUEST_METHODS:
        return None
    # 1. Check if its well-formed JSON
    try:
        req_data: dict = json.loads(req.body)
    except JSONDecodeError:
        return "The JSON request body is malformed", {}
    log.debug("Request is well-formed JSON")

    # 3. For inserting NEW objects, check if the required fields are there.
    if req.method in ("POST", "PUT"):
        missing_fields = []
        required_fields = [f for f in resource.fields if f.required]
        log.debug(
            "Got required fields to test for: {}", [f.name for f in required_fields]
        )
        for field in required_fields:
            # TODO: handle fieldname.subfieldname (nested objects)
            if field.name not in req_data.keys():
                missing_fields.append(field.name)

        if missing_fields:
            return "Some fields are missing", {"missing_fields": missing_fields}

    # 4. Check the type of each field
    log.debug("Checking types")
    fields_with_wrong_types = []
    unknown_fields = []
    for name, value in req_data.items():
        # Get the field configuration
        field = fields_by_name.get(name)
        if field is None:
            log.debug("    Request field {} is unknown", name)
            unknown_fields.append(name)
            continue
        # Check the type
        log.debug(
            "    Checking if type of {0} (with value {1}) is {2}",
            field.name,
            repr(value),
            field.type,
        )
        # Check for `multiple` types
        if field.multiple:
            if type(value) is not list:
                validated = False
            else:
                validated = all((validate_type(item, field.type) for item in value))
        else:
            validated = validate_type(value, field.type)

        if not validated:
            fields_with_wrong_types.append(field)
    if fields_with_wrong_types:
        return (
            "Some fields' values are of the wrong type",
            {
                "correct_types_for_fields": {
                    field.name: field.type + ("[]" if field.multiple else "")
                    for field in fields_with_wrong_types
                }
            },
        )
    if unknown_fields:
        return ("Unknown fields in request", {"unknown_fields": unknown_fields,})

    # 5. Check max/min (length)
    for name, value in req_data.items():
        # Get the field configuration
        field = fields_by_name.get(name)
        # Check for min/max values
        # TODO: Move `return message, data` to `validate_*` functions
        if field.minimum is not None or field.maximum is not None:
            log.debug(
                "    Checking for bounds of {0}: {1} ∈ [{2}, {3}]",
                repr(value),
                name,
                (field.minimum if field.minimum is not None else "-∞"),
                (field.maximum if field.maximum is not None else "+∞"),
            )
        if not validate_max_min(value, field.minimum, field.maximum):
            return (
                f"`{name}` is out of bounds",
                {
                    "actual_value": value,
                    "minimum_value": field.minimum,
                    "maximum_value": field.maximum,
                },
            )
        # If we don't allow empty values, the min length is one.
        if not field.allow_empty and (field.type in ("string") or field.multiple):
            field = field._replace(min_length=1)
        if field.min_length is not None or field.max_length is not None:
            log.debug(
                "    Checking for length of {0}: len({1}) ∈ [{2}, {3}]",
                repr(value),
                name,
                (field.min_length if field.min_length is not None else "-∞"),
                (field.max_length if field.max_length is not None else "+∞"),
            )
        if not validate_max_min_length(value, field.min_length, field.max_length):
            return (
                f"`{name}` is either too long or too short",
                {
                    "actual_length": len(value),
                    "minimum_length": (field.min_length or 0),
                    "maximum_length": field.max_length,
                },
            )

    # 6. Check

    return None


def validate_type(value: Any, correct_type: str) -> bool:
    # `number`s can be `float`s or `int`s but are stored as `float`s.
    if correct_type == "number" and type(value) is int:
        value = float(value)

    # For types bound to native python types, its just a matter of checking `value`'s `type()`
    if correct_type in NATIVE_TYPES_MAPPING.values():
        return type(value) is swap_keys_and_values(NATIVE_TYPES_MAPPING)[correct_type]

    # Datetime checking: ISO-8601
    if correct_type in ("date", "datetime", "time"):
        PATTERNS = {
            "date": "YYYY-MM-DDZZ",
            "time": "HH:mm:ssZZ",
            "datetime": "YYYY-MM-DD[T]HH:mm:ssZZ",
        }
        try:
            arrow.get(value, PATTERNS[correct_type])
            return True
        except arrow.parser.ParserError:
            return False

    if correct_type == "slug":
        return type(value) is str and slugify(str) == str

    raise ValueError(f"Can't check for unknown type {correct_type!r}.")


Number = Union[int, float]


def validate_max_min(
    value: Number, minimum: Optional[Number], maximum: Optional[Number]
) -> bool:
    if not type(value) in (int, float):
        return True
    validated = True
    if minimum is not None:
        validated = validated and value >= minimum
    if maximum is not None:
        validated = validated and value <= maximum
    return validated


def validate_max_min_length(
    value: Sized, min_length: Optional[Number], max_length: Optional[Number]
) -> bool:
    if not type(value) in (list, str):
        return True
    length = len(value)
    validated = True
    if min_length is not None:
        validated = validated and length >= min_length
    if max_length is not None:
        validated = validated and length <= max_length
    return validated
