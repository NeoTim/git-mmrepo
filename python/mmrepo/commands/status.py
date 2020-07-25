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
      prog="status",
      description="Displays status of trees in the repository",
      add_help=False)
  return parser


HELP_MESSAGE = create_argument_parser().format_help()


def print_git_status(args, tree):
  url = tree.url
  message = tree.repo.git.show(tree.path_in_repo,
                               git_object="HEAD",
                               option_args=[
                                   "--format=%H : {} : %s (%cd)".format(
                                       url),
                                   "--date=relative",
                                   "--no-patch",
                               ])
  print(message)


def exec(*args):
  args = create_argument_parser().parse_args(args)
  repo = Repo.find_from_cwd()
  for tree in repo.all_trees():
    if isinstance(tree, GitTreeRef):
      print_git_status(args, tree)
    else:
      print("UNKNOWN TREE TYPE:", tree.tree_id)
