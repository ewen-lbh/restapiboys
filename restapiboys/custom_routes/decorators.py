from restapiboys.utils import string_to_identifier
from typing import *
from restapiboys.http import Request, Response
import re

ReturnType = TypeVar("Response")
def _get_response_decorator(
    request_method: str,
) -> Callable[[str], Callable[[Callable[..., ReturnType]], Callable[..., ReturnType]]]:
    """
    Function that returns decorators.
    
    Have I gonne too DRY? Maybe.
    """

    def decorator(
        route: str,
    ) -> Callable[[Callable[..., ReturnType]], Callable[..., ReturnType]]:
        route_pattern = route_pattern_to_regex(route)

        def inner_decorator(
            func: Callable[..., ReturnType]
        ) -> Callable[..., ReturnType]:
            def wrapped(req: Request) -> Optional[Response]:
                # If the request's route does not match the pattern specified in the decorator
                # (`route`)
                # or the decorator itself (`request_method`) here since we'll be creating
                # one decorator per HTTP request method
                if not route_pattern.match(req.route) or req.method != request_method:
                    return None
                
                # Extract route params from the request route
                route_params = route_pattern.search(req.route).groupdict()
                # Convert to identifiers (also handles conflicts with keywords)
                route_params = { string_to_identifier(k): v for k, v in route_params.items() }
                # call the implementation (the user's function defined in the endpoints/*.py file)
                # with the request object and the extracted values from the route params, as kwargs
                return func(req, **route_params)

            return wrapped

        return inner_decorator

    return decorator


CONNECT = _get_response_decorator("CONNECT")
DELETE = _get_response_decorator("DELETE")
GET = _get_response_decorator("GET")
HEAD = _get_response_decorator("HEAD")
OPTIONS = _get_response_decorator("OPTIONS")
PATCH = _get_response_decorator("PATCH")
POST = _get_response_decorator("POST")
PUT = _get_response_decorator("PUT")
TRACE = _get_response_decorator("TRACE")


def route_pattern_to_regex(pattern: str) -> re.Pattern:
    """
    Converts an/api/doc-style/route/with/:params
    to a regular expression:
    ```
    r'an/api/doc-style/route/with/?P<params>([^/]+)'
    ```
    """
    fragments = pattern.split("/")
    regex = r""
    for fragment in fragments:
        if fragment.startswith(":"):
            variable_name = fragment[1:]
            regex += f"/?P<{variable_name}>([^/]+)"
        else:
            regex += f"/{fragment}"
    # Remove initial slash if present
    regex = regex.replace("//", "/")
    regex = re.compile(regex)
    return regex

