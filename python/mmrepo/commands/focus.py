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

HELP_MESSAGE = """Focuses on the current tree, setting all dependent versions.

This updates the cone of dependencies to the most authoritative versions based
on proximity to this root.
"""

def exec(*args):
  if args:
    raise UserError("Arguments not expected")
  repo = Repo.find_from_cwd()
  tree = repo.tree_from_cwd()

  # TODO: This should traverse the graph.
  dep_providers = tree.dep_providers
  tree_versions = {}
  for dep_provider in dep_providers:
    for dep_tree, version in dep_provider.lookup_versions():
      if dep_tree in tree_versions:
        print("Skipping existing tree version {} = {}".format(dep_tree, version))
      tree_versions[dep_tree] = version

  for dep_tree, version in tree_versions.items():
    print("Updating tree {} to {}".format(dep_tree, version))
    dep_tree.update_version(version)
