from multiprocessing import cpu_count
from os import getcwd, listdir, environ
from restapiboys.config import get_api_config
import subprocess
from restapiboys.utils import get_path
from typing import *
from restapiboys import log

WATCH_FILES = (
    get_path("endpoints/*.{yaml,py}"),
    get_path("functions/*.py"),
    get_path("config.yaml"),
    get_path("types.yaml"),
    get_path("email-templates/*.{txt,html}"),
)

def run(args: dict):
    bound_address = "%s:%s" % (args["--address"], args["--port"])
    scheme = 'http' if args['--address'] in ('localhost', '127.0.0.1') else 'https'
    workers_count = get_workers_count(args['--workers'])
    
    log.info('Spinning up a webserver listening on {}', f'{scheme}://{bound_address}')
    
    log.debug('Giving {} workers to gunicorn', workers_count)
    
    project_yaml_files = [
        get_path("endpoints", f)
        for f in listdir(get_path("endpoints"))
        if f.endswith(".yaml")
    ] + [get_path("types.yaml"), get_path("config.yaml")]
       
    config = {
        "bind": bound_address,
        "workers": workers_count,
        "log-level": "debug" if args['--debug-gunicorn'] else "error",
        "reload": args["--watch"],
        # "reload-extra-file": project_yaml_files if args["--watch"] else None,
    }
    
    if config['reload']:
        log.info('Watching for file changes...')
    
    subprocess.call(
        ["poetry", "run", "gunicorn", "restapiboys.server:requests_handler"]
        + config_dict_to_cli_args(config)
    )


def get_workers_count(cli_workers_arg: str) -> int:
    if cli_workers_arg == "auto":
        return cpu_count() * 2 + 1
    return int(cli_workers_arg)


def config_dict_to_cli_args(config: Dict[str, Any]) -> List[str]:
    args = []
    for key, value in config.items():
        if value:
            if type(value) is bool:
                args.append(f"--{key}")
            else:
                args.append(f"--{key}={value}")
    return args
