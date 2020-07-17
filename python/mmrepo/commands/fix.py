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

from mmrepo.config import *
from mmrepo.repo import *

HELP_MESSAGE = """Fixes trees after repository events.

Certain repository events (pull, reset --hard, etc) can leave tree dependency
links in an inconsistent state. This resets them.
"""

def exec(*args):
  if args:
    raise UserError("Arguments not expected")
  repo = Repo.find_from_cwd()
  tree = repo.tree_from_cwd()
  tree.checkout()
