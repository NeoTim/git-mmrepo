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

"""Initialize a new mmrepo."""

from mmrepo.repo import *

HELP_MESSAGE = """Initializes a new magical mono repository.

By default, the repository will be initialized in the current directory.
It is an error to initialize a repository inside of an existing repository.
"""

def exec(*args):
  r = Repo.init()
  print("Initialized new magical monorepo at {}".format(r.path))
