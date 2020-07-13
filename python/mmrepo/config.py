"""Manages configuration settings."""

from collections import namedtuple
import json
import os

GIT_CONFIG_ANNOTATION_FILE = "mmr-config"

__all__ = [
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

  def get_tree_by_id(self, tree_id):
    td = self.tree_dicts
    return td.get(tree_id)


class GitConfigAnnotation(namedtuple("GitConfigAnnotation", "tree_id")):
  """An annotation that gets stored in .git directories linking to the mmr."""

  @classmethod
  def from_git_root(cls, git_root_path) -> "GitConfigAnnotation":
    path = os.path.join(git_root_path, ".git", GIT_CONFIG_ANNOTATION_FILE)
    d = read_json_file(path)
    return cls(tree_id=d["tree_id"])

  def save_to_git_root(self, git_root_path):
    path = os.path.join(git_root_path, ".git", GIT_CONFIG_ANNOTATION_FILE)
    write_json_file(path, {"tree_id": self.tree_id})


def read_json_file(path):
  with open(path, "rt") as f:
    return json.load(f)


def write_json_file(path, contents):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "wt") as f:
    json.dump(contents, f, indent=2, sort_keys=True)
