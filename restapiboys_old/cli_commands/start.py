"""Spin-up a webserver

Usage:
  restapiboys start [options]

Options:
  -p --port=PORT  Port number. [default: 8888]
"""
from collections import namedtuple
from restapiboys.utils import get_path, recursive_namedtuple_to_dict, yaml
from restapiboys.routes import ResourceConfig, ResourceFieldConfig, get_route_names, get_route_config
from restapiboys import http
from typing import Callable, Dict, Any, List, Tuple, Union
from ..logger import Logger
from pprint import pprint
import subprocess
import json
import urllib

def run(args: Dict[str, Any]):
  port = args["--port"]
  url = f'http://localhost:{port}'
  log = Logger(args)
  in_background = args['--run-in-background']
  log.info('Starting webserver at {url}', url=url)
  gunicorn_invocation = [
    'poetry', 'run', 
    'gunicorn',
    f'--bind=127.0.0.1:{port}',
    '--log-level=error',
    'restapiboys.cli_commands.start:app',
  ]
  if args['--watch']:
    gunicorn_invocation.append('--reload')
  
  log.debug('Loaded the following routes:')
  for route in get_route_names():
    log.debug(f'- {url}{{route}}', route=route)
  
  if in_background:
    webserver = subprocess.Popen(gunicorn_invocation)
    pid = webserver.pid
    log.success('Server started in the background with PID {pid}.', pid=pid)
    log.info('Run {command} to stop it.', command=f"kill {pid}")
    
  else:
    log.info('Press {keystroke} to stop it.', keystroke="^C")
    try:
      subprocess.call(gunicorn_invocation)
    except KeyboardInterrupt:
      log.info('Server stopped')
  

def app(environ: Dict[str, Any], start_response: Callable[[str, List[Tuple[str, Any]]], None]):
  req = get_request_info(environ)
  print(f"-> {req.method} {req.raw['RAW_URI']} {'√ SSL' if req.is_ssl else ''}")
  res = dispatch_request(req)
  print(f'<- {res.status}')
  headers = [ (str(k), str(v)) for k, v in res.headers.items() ]
  print(f'   With headers {headers}')
  start_response(res.status, headers)
  return iter([res.data])

RequestInfo = namedtuple('RequestInfo', ['route', 'is_ssl', 'method', 'query', 'raw'])

def get_request_info(gunicorn_environ: Dict[str, Any]) -> RequestInfo:
  route = gunicorn_environ['PATH_INFO']
  is_ssl = gunicorn_environ['wsgi.url_scheme'] == 'https'
  method = gunicorn_environ['REQUEST_METHOD']
  query = { k:v[0] for k, v in dict(urllib.parse.parse_qs(gunicorn_environ['QUERY_STRING'])).items() }
  
  return RequestInfo(route, is_ssl, method, query, gunicorn_environ)

def dispatch_request(req: RequestInfo) -> http.Response:
  route_names = get_route_names()
  if req.route == '/spec':
    return get_api_spec(req)
  if req.route not in route_names:
    return http.Response(status=http.STATUS.NOT_FOUND)
  route_config = get_route_config(req.route)
  if not is_method_allowed(req, route_config):
    return http.Response(status=http.STATUS.METHOD_NOT_ALLOWED)
  
  # Do the magic here.
  fields = {}
  
  
def get_api_spec(req: RequestInfo) -> http.Response:
  # Get each route name
  routes = get_route_names()
  configs = {}
  for route in routes:
    configs[route] = recursive_namedtuple_to_dict(get_route_config(route))
  
  return http_response_from_obj(configs, http.STATUS.OK)

def http_response_from_obj(obj: Union[list, dict], status: str, headers: Dict[str, Any] = {}) -> http.Response:
  encoded_data = encode_data(obj)
  return http.Response(
    status=http.STATUS.OK,
    headers={
      **{
        'Content-Type': 'application/json',
        'Content-Length': len(encoded_data)
      },
      **headers
    },
    data=encoded_data
  )

def encode_data(obj: Union[List[Any], Dict[str, Any]]) -> bytes:
  return bytes(json.dumps(obj), 'utf-8')

def is_method_allowed(req: RequestInfo, route_config: ResourceConfig):
  return req.method in [ method.value for method in route_config.allowed_methods ]
