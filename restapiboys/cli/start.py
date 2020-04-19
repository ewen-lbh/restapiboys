from multiprocessing import cpu_count
import subprocess
from restapiboys.utils import get_path
from restapiboys.server import RESTAPIBOYSApp, StandaloneApplication, requests_handler
from typing import *

WATCH_FILES = (
    get_path("endpoints/*.{yaml,py}"),
    get_path("functions/*.py"),
    get_path("config.yaml"),
    get_path("types.yaml"),
    get_path("email-templates/*.{txt,html}"),
)


def run(args):
    config = {
        "bind": "%s:%s" % (args["--address"], args["--port"]),
        "workers": get_workers_count(args["--workers"]),
        "log-level": "error",
        "reload": args["--watch"],
        # 'reload-extra-files':
    }
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
        if type(value) is bool:
            if value:
                args.append(f"--{key}")
        else:
            args.append(f"--{key}={value}")
    return args
