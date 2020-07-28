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
from mmrepo.version_map import *


def create_argument_parser():
  parser = argparse.ArgumentParser(
      prog="version_map",
      description="Resolve and set version maps for components",
      add_help=False)
  parser.add_argument("--set",
                      dest="set",
                      action="store_true",
                      help="Set the version map, checking out as needed")
  parser.add_argument("--no-fetch",
                      dest="no_fetch",
                      action="store_true",
                      help="Do not fetch prior to checking out")
  parser.add_argument("specs", nargs="*", help="Version specs to apply")
  return parser


HELP_MESSAGE = create_argument_parser().format_help() + """

Query or set a version map.

By default, this will resolve all components of a version map to concrete
revisions and print back the resolved mapping (suitable for a future call).
If the --set option is specified, then checked out revisions are updated
as neeeded.

A version map is a white-space delimitted list of components, where each is
of the form:
  `tree_id|alias` [`@` `symbolic_version`] [`=` `resolved_version`]

For git repositories, the symbolic_version is a ref known to the remote (i.e.
"HEAD", "refs/heads/master", etc). The resolved_version is a commit hash. If
both a symbolic and resolved version are omitted, then "HEAD" is assumed.

When processing each item in the list, the referenced tree will checkout the
given version if the tree has not yet been encountered. Then all dependencies
of the tree are added to the list of version updates. In this way, versions
are set in a first-come fashion and proceed depthwise. Specific, deep versions
can be pinned by listing or encountering them first in the graph of deps.
"""


def exec(*args):
  args = create_argument_parser().parse_args(args)
  repo = Repo.find_from_cwd()

  version_map = VersionMap.parse(*args.specs)
  version_map = version_map.resolve(repo)
  print(version_map)

  if not args.set: return

  # Prime the worklist.
  pending_tree_specs = list()
  for comp in version_map.components:
    pending_tree_specs.append((comp.tree, comp.resolved_version))

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
