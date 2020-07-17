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
    raise
    sys.exit(1)


if __name__ == "__main__":
  main()
