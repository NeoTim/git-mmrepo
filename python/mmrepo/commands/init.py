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

By default, the repository will be initialized in the current directory
as a "bare mm-repo", which means that it is not also a git repository.

If the current working directory is also a git tree, the existing
git tree will be mapped into the repo as the __root__ alias. A subsequent
"mmr checkout" command can fully initialize its dependencies. Such
root git trees cannot exist recursively in dependencies.
"""

def exec(*args):
  r = Repo.init()
  print("Initialized new magical monorepo at {}".format(r.path))
  if r.git.is_git_repository(r.path):
    root_tree = r.get_root_tree()
    print("Created root repository", root_tree.tree_id)
