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

"""Manages configuration settings."""

import itertools
from typing import Sequence

from collections import namedtuple
import json
import os

__all__ = [
    "read_json_file",
    "write_json_file",
    "DepRecord",
    "RepoConfig",
    "RepoTreesConfig",
    "GitConfigAnnotation",
]


class RepoConfig:
  """Configuration for the repository."""

  def __init__(self, repo_dir: str):
    super().__init__()
    self._repo_dir = repo_dir
    self._config_dir = os.path.join(self._repo_dir, "config")
    self._trees_config = RepoTreesConfig(
        os.path.join(self._config_dir, "trees.json"))

  @property
  def trees(self) -> "RepoTreesConfig":
    return self._trees_config


class RepoTreesConfig:
  """Configuration for the known trees."""

  def __init__(self, config_file: str):
    super().__init__()
    self._config_file = config_file
    if os.path.isfile(self._config_file):
      self._contents = read_json_file(self._config_file)
    else:
      self._contents = {}

  def save(self):
    write_json_file(self._config_file, self._contents)

  @property
  def tree_dicts(self):
    if not "trees" in self._contents:
      self._contents["trees"] = {}
    td = self._contents["trees"]
    assert isinstance(td, dict)
    return td

  @property
  def aliases(self):
    if not "aliases" in self._contents:
      self._contents["aliases"] = {}
    aliases = self._contents["aliases"]
    assert isinstance(aliases, dict)
    return aliases

  def add_alias(self, alias: str, tree_id: str) -> str:
    """Adds an alias to a tree id.

    If the alias already exists and is bound to another tree, then an integer
    is appended to unique it. The actual alias is returned.
    """
    requested_alias = alias
    aliases = self.aliases
    for i in itertools.count(0):
      existing_tree_id = aliases.get(alias)
      if existing_tree_id is None or existing_tree_id == tree_id:
        aliases[alias] = tree_id
        return alias
      alias = requested_alias + "-" + str(i)

  def get_tree_by_id(self, tree_id):
    td = self.tree_dicts
    return td.get(tree_id)


class GitConfigAnnotation(namedtuple("GitConfigAnnotation", "tree_id")):
  """An annotation that gets stored in .git directories linking to the mmr."""

  @staticmethod
  def _get_config_file(git_root_path: str) -> str:
    parent = os.path.dirname(git_root_path)
    base = os.path.basename(git_root_path)
    return os.path.join(parent, ".{}.mmr-config".format(base))

  @classmethod
  def from_git_root(cls, git_root_path) -> "GitConfigAnnotation":
    d = read_json_file(cls._get_config_file(git_root_path))
    return cls(tree_id=d["tree_id"])

  def save_to_git_root(self, git_root_path):
    write_json_file(self._get_config_file(git_root_path),
                    {"tree_id": self.tree_id})


class DepRecord(namedtuple("DepRecord", "paths,version,url")):
  """Represents a dependency record."""

  @staticmethod
  def read_from_file(deps_file: str) -> Sequence["DepRecord"]:
    file_dict = read_json_file(deps_file)
    if not file_dict:
      return []
    deps_records = file_dict.get("deps")
    if not deps_records:
      return []
    results = []
    for dep_record in deps_records:
      results.append(
          DepRecord(paths=[dep_record["path"]],
                    version=dep_record["version"],
                    url=dep_record["url"]))
    return results


def read_json_file(path):
  with open(path, "rt") as f:
    return json.load(f)


def write_json_file(path, contents):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "wt") as f:
    json.dump(contents, f, indent=2, sort_keys=True)
