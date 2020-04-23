"""RESTAPIBOYS - A REST API framework Based On YAML Specifications

Usage:
  restapiboys [--help] [options] <command>

Options:
  -v --log-level=LEVEL  Show log messages of at most this level. [default: info]
                        Possible values:
                            debug    - Shows all messages, including debug information
                            info     - Informative messages
                            warning  - Message that informs of potentially erroneous
                            error    - Error messages
                            critical - Show only critical messages
  -q --quiet            Equivalent of --log-level=critical
  -c --config=FILEPATH  Specify the configuraiton file path [default: config.yaml]

Command 'start' options:
  -p --port=PORT               Port number [default: 8888]
  --address=IP_ADDRESS         Listen on this IP address [default: 127.0.0.1]
  --run-in-background          Run the webserver as a background process
  --watch                      Restart webserver when code changes
  --workers=INTEGER|'auto'     Number of gunicorn workers to boot [default: auto]
"""
from enum import Enum
import os
from logging import getLogger
from typing import *
from importlib import import_module
import docopt


class CommandNotFoundError(Exception):
    """Used when a CLI command isn't found """

    pass

logger = getLogger()

def entry_point() -> None:
    args = docopt.docopt(__doc__)
    if args['--quiet']:
        os.environ['log-level'] = 'CRITICAL'
    else:
        os.environ['log-level'] = args.get('--log-level', 'INFO').upper()
    logger.setLevel(os.environ.get('log-level', 'INFO'))
    subcommand = args["<command>"]
    dispatch_subcommand(subcommand, args)


def dispatch_subcommand(subcommand_name: str, args: Dict[str, Any]):
    try:
        subcommand = import_module(f"restapiboys.cli.{subcommand_name}")
    except ModuleNotFoundError:
        raise CommandNotFoundError(f"Command {subcommand_name!r} not found.")

    try:
        subcommand.run(args)
    except AttributeError:
        raise NotImplementedError(
            f"Command {subcommand_name!r} not implemented. (does not define a 'run' function)"
        )
