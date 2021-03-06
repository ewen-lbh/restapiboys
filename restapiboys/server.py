from restapiboys.database import create_item, delete_item, list_items, read_item, update_item
from restapiboys.validation import validate_request_data
from restapiboys.config import get_api_config
from restapiboys.utils import recursive_namedtuple_to_dict, extract_uuid_from_path
from restapiboys.http import Request, StatusCode, Response
from restapiboys.endpoints import (
    add_computed_values_to_request_data, add_default_fields_to_request_data, get_endpoints,
    get_endpoints_routes,
    get_resource_config_of_route,
    get_resource_headers,
)
from typing import *
from restapiboys import log
import multiprocessing
import traceback
from uuid import UUID, uuid4
import json
import re

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
        resource_id, uuid = extract_uuid_from_path(req.route) or (req.route, None)
        resource = get_resource_config_of_route(resource_id)
        log.debug('resource_id = {0}  uuid = {1}', resource_id, uuid)
        log.debug("Request body: {}", req.body)
        available_routes = get_endpoints_routes()
        if resource and req.method not in resource.allowed_methods:
            res = Response(StatusCode.METHOD_NOT_ALLOWED, {}, b"")
        elif req.route.startswith("/specs") and "/specs" not in available_routes:
            res = handle_spec_route(req)
        elif req.route == "/" and "/" not in available_routes:
            res = Response(StatusCode.FOUND, {"Location": "/specs"}, {})
        elif not endpoint_exists(resource_id):
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
                "traceback": traceback.format_exc().split('\n')
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
    res = interact_with_db(req)
    
    # 4. serialize the response (handle fieldname.serialization)
    return res
    # return Response(
    #     StatusCode.NOT_IMPLEMENTED, headers, {"error": "Not implemented yet."}
    # )


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


def interact_with_db(req: Request) -> Response:
    route, uuid = extract_uuid_from_path(req.route) or (req.route, None)
    resource = get_resource_config_of_route(route)
    req_data = json.loads(req.body) if req.body else None
    if resource is None:
        return Response(StatusCode.INTERNAL_SERVER_ERROR, {}, {'error': f"Could not determine resource from route {route!r}"})
    if req.method == 'GET' and not uuid:
        data = list_items(resource.identifier)
    elif req.method == 'GET' and uuid:
        data = read_item(resource.identifier, uuid)
    elif req.method == 'DELETE' and uuid:
        data = delete_item(resource.identifier, uuid)
    elif req.method == 'PATCH' and uuid:
        if not req_data:
            return Response(StatusCode.BAD_REQUEST, {}, {'error': f'Request body is empty'})
        current_data = read_item(resource.identifier, uuid)
        data = add_computed_values_to_request_data(resource, req_data, current_data, current_data)
        data = {**current_data, **data}
        data = update_item(resource.identifier, uuid, data)
    elif req.method == 'POST':
        if not req_data:
            return Response(StatusCode.BAD_REQUEST, {}, {'error': f'Request body is empty'})
        data = add_default_fields_to_request_data(resource, req_data)
        data = add_computed_values_to_request_data(resource, data, {}, data)
        data = create_item(resource.identifier, uuid4(), data)
    else:
        return Response(StatusCode.METHOD_NOT_ALLOWED, {}, {'error': f'Method {req.method!r}', 'allowed_methods': resource.allowed_methods})
    if type(data) is bool:
        data = {'success': data}
        if not data['success']:
            return Response(StatusCode.INTERNAL_SERVER_ERROR, {}, data)
    return Response(StatusCode.OK, {}, data)
        
