"""RESTAPIBOYS - A REST API framework Based On YAML Specifications

Usage:
  restapiboys [--help] [options] <command>

Options:
  -v --log-level=LEVEL  Show log messages of at most this level. [default: info]
                        Possible values:
                            debug   - Shows all messages, including debug information
                            info    - Informative messages
                            warning - Message that informs of potentially erroneous
                            error   - Error messages
                            none    - Show no messages
  -q --quiet            Equivalent of --log-level=none
  -c --config=FILEPATH  Specify the configuraiton file path [default: config.yaml]

Command 'start' options:
  -p --port=PORT               Port number [default: 8888]
  --address=IP_ADDRESS         Listen on this IP address [default: 127.0.0.1]
  --run-in-background          Run the webserver as a background process
  --watch                      Restart webserver when code changes
  --workers=INTEGER|'auto'     Number of gunicorn workers to boot [default: auto]
"""
from enum import Enum
from typing import *
from importlib import import_module
import sys
import docopt


class CommandNotFoundError(Exception):
    """Used when a CLI command isn't found """

    pass


def entry_point() -> None:
    args = docopt.docopt(__doc__)
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
