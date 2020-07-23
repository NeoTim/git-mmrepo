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

import os

from mmrepo.common import *
from mmrepo.repo import *

HELP_MESSAGE = """Checks out a git repository tree.

Syntax:
  mmr checkout <repository url> [local path]
  mmr checkout

In the first form, a specific repository URL is checkout out, optionally
at a specific local path. This is typically used in bare mm-repos.

In the second form, the git tree that is mapped to the current working directory
is checked out (all dependencies are resolved). Typically it will already
exist, so a clone is skipped.
"""


def checkout(repo, tree, is_root_checkout):
  print("Checking out tree {}".format(tree))
  tree.checkout()
  if not is_root_checkout:
    # Create a default link under all/
    all_path = os.path.join(repo.path, "all", tree.default_local_path)
    tree.make_link(all_path)


def exec(*args):
  repo = Repo.find_from_cwd()
  local_path = None
  is_root_checkout = False
  if len(args) == 0:
    # Re-checkout the current repository.
    tree = repo.tree_from_cwd()
    is_root_checkout = True
  else:
    # Checkout a requested: git_url [local_path]
    if len(args) == 1:
      tree_url = args[0]
    elif len(args) == 2:
      tree_url, local_path = args
    tree = repo.get_tree(tree_url)

  # Checkout the repository.
  checkout(repo, tree, is_root_checkout)

  # Create the requested link.
  if local_path is not None:
    if os.path.isdir(local_path):
      # Treat it like a symlink to a directory where it will create a link
      # with the source name in that directory.
      local_path = os.path.join(local_path, tree.default_local_path)
    tree.make_link(local_path)

  # Collect recursive dependencies.
  recursive_processed = set()
  recursive_errored = set()
  all_exceptions = []
  all_depends = set()

  all_depends.add(tree)
  recursive_processed.add(tree)
  all_depends.update(tree.dependencies)

  while all_depends != recursive_processed:
    for tree_dep in set(all_depends):
      if tree_dep in recursive_processed:
        continue
      recursive_processed.add(tree_dep)
      try:
        checkout(repo, tree_dep, is_root_checkout)
      except UserError as e:
        recursive_errored.add(tree_dep)
        all_exceptions.append(e)

      all_depends.update(tree_dep.dependencies)

  # Report.
  print("** Processed {} repositories".format(len(all_depends)))
  if recursive_errored:
    print("!! {} repositories had errors:".format(len(recursive_errored)))
    for error_tree in recursive_errored:
      print("  {}".format(error_tree))
    print("!! Error messages:")
    for ex in all_exceptions:
      print("  ", ex.message)
