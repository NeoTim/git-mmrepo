# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The 'help' command."""

import importlib

HELP_MESSAGE = """Manage a magical monorepo.

For more information about any command, run:
  mmr help <command>

Available commands:
  checkout - Checks out a remote git repository.
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
