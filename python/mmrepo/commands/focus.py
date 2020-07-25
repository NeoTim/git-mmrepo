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

import argparse

from mmrepo.config import *
from mmrepo.repo import *


def create_argument_parser():
  parser = argparse.ArgumentParser(
      prog="focus",
      description="Focuses all versions in a cone of trees",
      add_help=False)
  parser.add_argument("--no-fetch",
                      dest="no_fetch",
                      action="store_true",
                      help="Do not fetch prior to checking out")
  parser.add_argument("specs", nargs="*", help="Version specs to apply")
  return parser


HELP_MESSAGE = create_argument_parser().format_help() + """

Focus dependent trees based on a sequence of version specs. Each version
specs is one of the following forms:
  alias
  alias=refspec

Terms:
  'alias' is a tree alias (typically the last path component of a git URL)
  'refspec' is anything legal to pass to a git checkout command.

If a refspec is not specified, it defaults to "origin/HEAD".

When processing each item in the list, the referenced tree will checkout the
given refspec if the tree has not yet been encountered. Then all dependencies
of the tree are added to the list of version updates. In this way, versions
are set in a first-come fashion and proceed depthwise. Specific, deep versions
can be pinned by listing or encountering them first in the graph of deps.
"""


def parse_spec(spec: str):
  try:
    eq_index = spec.index("=")
  except ValueError:
    return spec, "origin/HEAD"
  else:
    return spec.split("=", maxsplit=1)


def exec(*args):
  args = create_argument_parser().parse_args(args)
  repo = Repo.find_from_cwd()

  # Prime the worklist.
  pending_tree_specs = list()
  if not args.specs:
    pending_tree_specs.append((repo.tree_from_cwd(), "origin/HEAD"))
  else:
    for spec in args.specs:
      alias, ref = parse_spec(spec)
      pending_tree_specs.append((repo.tree_from_alias(alias), ref))

  # Process the worklist.
  processed_trees = set()
  while pending_tree_specs:
    current_tree_specs = list(pending_tree_specs)
    pending_tree_specs.clear()
    for tree, spec in current_tree_specs:
      if tree in processed_trees:
        continue
      processed_trees.add(tree)
      # Update this tree.
      print(":: Update {} to {}".format(tree, spec))
      tree.update_version(spec, fetch=not args.no_fetch)

      # Add deps to worklist.
      for dep_provider in tree.dep_providers:
        for dep_tree, dep_version in dep_provider.lookup_versions():
          pending_tree_specs.append((dep_tree, dep_version))
