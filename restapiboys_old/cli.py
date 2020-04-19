"""RESTAPIBOYS - A REST API framework Based On YAML Specifications

Usage:
  restapiboys [--verbose ...] [options] <command>

Options:
  -v --verbose          Show debug information
  -q --quiet            Don't show any output
  -c --config=FILEPATH  Specify the configuraiton file path [default: config.yaml]

start command options:
  -p --port=PORT        Port number [default: 8888]
  --run-in-background   Run the webserver as a background process
  --watch               Restart webserver when code changes
"""
import docopt
from typing import Dict, Any
from importlib import import_module

class CliCommandExitCodes:
  UNKNOWN_ERROR  = -1
  OK             = 0
  FILE_NOT_FOUND = 1

def run() -> None:
  args = docopt.docopt(__doc__)
  launch_cli_command(args['<command>'], args)

def launch_cli_command(command:str, args: Dict[str, Any]) -> CliCommandExitCodes:
  command_module = import_module(f'restapiboys.cli_commands.{command}')
  return command_module.run(args)

if __name__ == "__main__":
  run()
