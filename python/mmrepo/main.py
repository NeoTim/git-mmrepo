"""Main entry-point."""

import importlib
import sys

from mmrepo.common import *
from mmrepo.repo import *


def exec_command(command: str, *args):
  norm_command = command.replace("-", "_")
  try:
    m = importlib.import_module("mmrepo.commands." + norm_command)
  except ImportError:
    raise UserError("Unknown command: {}", command)
  m.exec(*args)


def main():
  _, *args = sys.argv
  if not args:
    print("Expected command to execute.")
    exec_command("help")
    sys.exit(1)

  command, *args = args
  try:
    exec_command(command, *args)
  except UserError as e:
    print("ERROR:", e.message)
    sys.exit(1)


if __name__ == "__main__":
  main()
