"""RESTAPIBOYS - A REST API framework Based On YAML Specifications

Usage:
  restapiboys [--help] [options] <command>

Options:
  -L --log=LEVEL        Show log messages of at most this level. [default: info]
                        Possible values:
                            debug    - Shows all messages, including debug information
                            info     - Informative messages
                            warning  - Message that informs of potentially erroneous
                            error    - Error messages
                            critical - Show only critical messages
  -q --quiet            Equivalent of --log=critical
  -v --verbose          Equivalent of --log=debug
  -c --config=FILEPATH  Specify the configuration file path [default: config.yaml]

Command 'start' options:
  -p --port=PORT               Port number [default: 8888]
  --address=IP_ADDRESS         Listen on this IP address [default: 127.0.0.1]
  --run-in-background          Run the webserver as a background process
  -w --watch                   Restart webserver when code changes
  --workers=INTEGER|'auto'     Number of gunicorn workers to boot [default: auto]
  --debug-gunicorn             Set gunicorn's log-level to "debug"
  --no-start-couchdb           Don't start CouchDB. Notice that the service will not 
                               be started when already running, even without this option.
                               Useful if you don't have access to `sudo`, since
                               touching services requires `sudo systemctl` / `sudo service`
  --force-start-couchdb        Starts CouchDB even if it is already runnning.
"""
from enum import Enum
import os
from logging import getLogger
from typing import *
from importlib import import_module
from restapiboys.cli import start, manage_db
import docopt


class CommandNotFoundError(Exception):
    """Used when a CLI command isn't found """

    pass


logger = getLogger()


def entry_point() -> None:
    args = docopt.docopt(__doc__)
    if args["--quiet"]:
        os.environ["log-level"] = "CRITICAL"
    if args["--verbose"]:
        os.environ["log-level"] = "DEBUG"
    else:
        os.environ["log-level"] = args.get("--log", "INFO").upper()
    logger.setLevel(os.environ.get("log-level", "INFO"))
    subcommand = args["<command>"]
    dispatch_subcommand(subcommand, args)


def dispatch_subcommand(subcommand_name: str, args: Dict[str, Any]) -> None:
    if subcommand_name == "start":
        start.run(args)
    if subcommand_name in ("manage-db", "manage-database", "database", "db"):
        manage_db.run(args)