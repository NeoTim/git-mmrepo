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

import argparse
import os

from mmrepo.repo import *


def create_argument_parser():
  parser = argparse.ArgumentParser(
      prog="init",
      description="Initializes a new magical mono repository",
      add_help=False)
  # Reference and shared.
  group = parser.add_mutually_exclusive_group()
  group.add_argument("--local-mirror",
                     help="Use (or create) a bare local mirror for cloning",
                     default=None)
  group.add_argument(
      "--reference",
      help="Clone from reference git trees under this repository "
      "(via git clone --reference)",
      default=None)
  return parser


HELP_MESSAGE = create_argument_parser().format_help() + """

By default, the repository will be initialized in the current directory
as a "bare mm-repo", which means that it is not also a git repository.

If the current working directory is also a git tree, the existing
git tree will be mapped into the repo as the __root__ alias. A subsequent
"mmr checkout" command can fully initialize its dependencies. Such
root git trees cannot exist recursively in dependencies.
"""


def exec(*args):
  args = create_argument_parser().parse_args(args)
  r = Repo.init()

  # Initialize local mirror mode
  if args.local_mirror:
    local_mirror_path = args.local_mirror
    print("Using local mirror at", local_mirror_path)
    os.makedirs(local_mirror_path, exist_ok=True)
    # Configure the mirror.
    mirror_r = Repo.init(from_cwd=local_mirror_path, exact_path=True)
    mirror_trees_config = mirror_r.config.trees
    mirror_trees_config.bare_clone = True
    mirror_trees_config.save()
    # Configure this repo.
    trees_config = r.config.trees
    trees_config.local_mirror_path = local_mirror_path

  # Configure reference and shared repos.
  if args.reference:
    trees_config = r.config.trees
    trees_config.reference_repo = args.reference
    trees_config.save()

  # Initialize and check out.
  print("Initialized magical monorepo at {}".format(r.path))
  if r.git.is_git_repository(r.path):
    root_tree = r.get_root_tree()
    print("Root repository", root_tree.tree_id)
    root_tree.checkout()
