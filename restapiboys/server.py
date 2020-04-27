from restapiboys.validation import validate_request_data
from restapiboys.config import get_api_config
from restapiboys.utils import recursive_namedtuple_to_dict
from restapiboys.http import Request, StatusCode, Response
from restapiboys.endpoints import (
    get_endpoints,
    get_endpoints_routes,
    get_resource_config_of_route,
    get_resource_headers,
)
from typing import *
from restapiboys import log
import multiprocessing


DEFAULT_GUNICORN_OPTIONS = {
    "bind": "127.0.0.1:8080",
    "workers": (multiprocessing.cpu_count() * 2) + 1,
    "reload_extra_files": "",
}


def requests_handler(environ, start_response):
    try:
        req = Request.from_gunicorn_environ(environ)
        config = get_api_config()
    except Exception as exception:
        log.critical(str(exception))
        return
    try:
        resource = get_resource_config_of_route(req.route)
        log.debug("Request body: {}", req.body)
        available_routes = get_endpoints_routes()
        if resource and req.method not in resource.allowed_methods:
            res = Response(StatusCode.METHOD_NOT_ALLOWED, {}, b"")
        elif req.route.startswith("/specs") and "/specs" not in available_routes:
            res = handle_spec_route(req)
        elif req.route == "/" and "/" not in available_routes:
            res = Response(StatusCode.FOUND, {"Location": "/specs"}, {})
        elif not endpoint_exists(req.route):
            res = Response(
                StatusCode.NOT_FOUND,
                {},
                {"error": f"The resource {req.route} was not found"},
            )
        else:
            res = handle_endpoint(req)
    except Exception as exception:
        res = Response(
            StatusCode.INTERNAL_SERVER_ERROR,
            {},
            {
                "error": str(exception),
                "please_contact": f"{config.contact_info.name} <{config.contact_info.email}>",
            },
        )
    start_response(res.status, res.headers)
    if res.is_error():
        log.warn(f"{req.method} {req.route} {{}} {res.status}", "-->")
    else:
        log.success(f"{req.method} {req.route} {{}} {res.status}", "-->")
    return [res.body]


def endpoint_exists(route: str) -> bool:
    routes = ["/" + r for r in get_endpoints_routes()]
    return route in routes


def handle_endpoint(req: Request) -> Response:
    # 1. validation of the request's body
    resource = get_resource_config_of_route(req.route)
    headers = {}
    if resource:
        headers = get_resource_headers(resource)
    error = validate_request_data(req)
    if error:
        message, data = error
        return Response(StatusCode.BAD_REQUEST, headers, {"error": message, **data})

    # 2. execute code for custom routes
    # 3. (or) interact with the database
    # 4. serialize the response (handle fieldname.serialization)
    return Response(
        StatusCode.NOT_IMPLEMENTED, headers, {"error": "Not implemented yet."}
    )


def handle_spec_route(req: Request) -> Response:
    config = get_api_config()
    endpoints = get_endpoints()
    if req.route == "/specs":
        specs_urls_map = {}
        for endpoint in endpoints:
            specs_urls_map[
                endpoint.identifier
            ] = f"{req.scheme}://{req.host}/specs{endpoint.route}"
        return Response(StatusCode.OK, {}, specs_urls_map)
    else:
        requested_endpoint = req.route.replace("/specs", "", 1)
        for endpoint in endpoints:
            if requested_endpoint == endpoint.route:
                return Response(
                    StatusCode.OK, {}, recursive_namedtuple_to_dict(endpoint)
                )
        return Response(
            StatusCode.NOT_FOUND,
            {},
            {
                "error": f"The requested endpoint {requested_endpoint} does not exist.",
                "documentation_url": config.documentation_url,
            },
        )
