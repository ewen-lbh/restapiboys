from restapiboys.config import get_api_config
from restapiboys.utils import recursive_namedtuple_to_dict
from restapiboys.http import Request, StatusCode, Response
from restapiboys.endpoints import get_endpoints, get_endpoints_routes
from typing import *
import multiprocessing


DEFAULT_GUNICORN_OPTIONS = {
    "bind": "127.0.0.1:8080",
    "workers": (multiprocessing.cpu_count() * 2) + 1,
    "reload_extra_files": "",
}


def requests_handler(environ, start_response):
    req = Request.from_gunicorn_environ(environ)
    config = get_api_config()
    print(f"<-- {req.method} {req.route}")
    try:
        available_routes = get_endpoints_routes()
        if req.route.startswith("/specs") and "/specs" not in available_routes:
            res = handle_spec_route(req)
        else:
            res = Response(StatusCode.OK, {}, {"error": "Not implemented yet."})
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
    print(f"--> {res.status}\n")
    return [res.body]


def handle_spec_route(req: Request) -> Response:
    endpoints = get_endpoints()
    if req.route == "/specs":
        specs_urls_map = {}
        for endpoint in endpoints:
            specs_urls_map[endpoint.identifier] = (
                req.gunicorn_env["wsgi.url_scheme"]
                + "://"
                + req.gunicorn_env["HTTP_HOST"]
                + "/specs"
                + endpoint.endpoint
            )
        return Response(StatusCode.OK, {}, specs_urls_map)
    else:
        requested_endpoint = req.route.replace("/specs", "", 1)
        for endpoint in endpoints:
            if requested_endpoint == endpoint.endpoint:
                return Response(
                    StatusCode.OK, {}, recursive_namedtuple_to_dict(endpoint)
                )
        return Response(
            StatusCode.NOT_FOUND,
            {},
            {"error": f"The requested endpoint {requested_endpoint} does not exist."},
        )
