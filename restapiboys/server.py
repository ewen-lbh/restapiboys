from restapiboys.utils import recursive_namedtuple_to_dict
from restapiboys.http import Request, StatusCode, Response
from restapiboys.endpoints import get_endpoints
from typing import *
import multiprocessing
import gunicorn.app.base


DEFAULT_GUNICORN_OPTIONS = {
    "bind": "127.0.0.1:8080",
    "workers": (multiprocessing.cpu_count() * 2) + 1,
}


def requests_handler(environ, start_response):
    req = Request.from_gunicorn_environ(environ)
    print(f"<-- {req.method} {req.route}")
    routes = [ recursive_namedtuple_to_dict(o) for o in get_endpoints() ]
    res = Response(StatusCode.OK, {}, routes)
    start_response(res.status, res.headers)
    return [res.body]


class RESTAPIBOYSApp(gunicorn.app.base.BaseApplication):
    def __init__(self, options: Optional[Dict[str, str]] = None):
        options = options or {}
        self.options = {**DEFAULT_GUNICORN_OPTIONS, **options}
        self.endpoints = get_endpoints()
        self.application = requests_handler
        super().__init__()

    def endpoint_exists(self, endpoint):
        return endpoint in [endpoint.endpoint for endpoint in self.endpoints]

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application


class StandaloneApplication(gunicorn.app.base.BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
