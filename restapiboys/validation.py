from json.decoder import JSONDecodeError
from restapiboys.endpoints import get_endpoints, get_resource_config_of_route
from restapiboys.http import Request
from restapiboys import log
from typing import *
import json

BODYLESS_REQUEST_METHODS = ["GET", "DELETE"]


def validate_request_data(req: Request) -> Optional[str]:
    log.debug("Starting validation")
    resource = get_resource_config_of_route(req.route)
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
        return "The JSON request body is malformed"
    log.debug("Request is well-formed JSON")

    log.debug("Got fields: {}", [f.name for f in resource.fields])
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
            return f"The following fields are required but missing: {', '.join(missing_fields)}"

    return None
