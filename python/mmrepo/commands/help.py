"""The 'help' command."""

import importlib

HELP_MESSAGE = """Manage a magical monorepo.

For more information about any command, run:
  mmr help <command>

Available commands:
  help - Get help on commands and syntax
  info - Show information about the current repo
  init - Initialize a new repo
"""

def exec(*args):
  if not args:
    print(HELP_MESSAGE)
    return
  for command in args:
    norm_command = command.replace("-", "_")
    try:
      m = importlib.import_module("mmrepo.commands." + norm_command)
    except ImportError:
      raise UserError("Unknown command: {}", command)
    print(m.HELP_MESSAGE)
