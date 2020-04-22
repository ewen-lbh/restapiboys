from multiprocessing import cpu_count
from os import getcwd, listdir
import subprocess
from restapiboys.utils import get_path
from typing import *

WATCH_FILES = (
    get_path("endpoints/*.{yaml,py}"),
    get_path("functions/*.py"),
    get_path("config.yaml"),
    get_path("types.yaml"),
    get_path("email-templates/*.{txt,html}"),
)


def run(args):
    project_yaml_files = [
        get_path("endpoints", f)
        for f in listdir(get_path("endpoints"))
        if f.endswith(".yaml")
    ] + [get_path("types.yaml"), get_path("config.yaml")]

    config = {
        "bind": "%s:%s" % (args["--address"], args["--port"]),
        "workers": get_workers_count(args["--workers"]),
        "log-level": "error",
        "reload": args["--watch"],
        # "reload-extra-file": project_yaml_files if args["--watch"] else None,
    }
    wd = getcwd()
    # print(f"Running in {wd}")
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
            # elif type(value) is str:
            #     args.append(f'--{key}="{value}"')
            # elif type(value) is list:
            #     for val in value:
            #         args.append(f'--{key}="{val}"')
            else:
                args.append(f"--{key}={value}")
    return args
