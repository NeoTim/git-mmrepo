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
"""Overall repository management."""

from typing import Optional
import os

from mmrepo.common import *
from mmrepo.config import *
from mmrepo import fileutils
from mmrepo.git import *

MMREPO_DIR = ".mmrepo"
UNIVERSE_DIR = "universe"
DEFAULT_WORKING_TREE = "defaultwt"

__all__ = [
    "GitTreeRef",
    "Repo",
]


class Repo:
  """Represents an on-disk repository."""

  def __init__(self, path: str):
    super().__init__()
    self._path = os.path.realpath(path)
    self._git = GitExecutor()
    self._config = RepoConfig(self.mmrepo_dir)

  @property
  def config(self) -> RepoConfig:
    return self._config

  @property
  def path(self) -> str:
    return self._path

  @property
  def universe_dir(self) -> str:
    return os.path.join(self._path, MMREPO_DIR, UNIVERSE_DIR)

  @property
  def mmrepo_dir(self) -> str:
    return os.path.join(self._path, MMREPO_DIR)

  @property
  def git(self) -> GitExecutor:
    return self._git

  def tree_from_cwd(self, cwd=None):
    """Gets the tree from a current working directory."""
    if cwd is None:
      cwd = os.getcwd()
    toplevel = self.git.find_git_toplevel(cwd)
    annotation = GitConfigAnnotation.from_git_root(toplevel)
    existing_dict = self._config.trees.get_tree_by_id(annotation.tree_id)
    if existing_dict is None:
      raise UserError(
          "The directory does not seem to be an MMR managed git tree: {}", cwd)
    tree = BaseTreeRef.from_dict(self, d=existing_dict)
    print("Found tree for cwd:", tree)
    return tree

  def get_tree(self,
               remote_url: str,
               working_tree=DEFAULT_WORKING_TREE,
               remote_type="git",
               create=True) -> "GitTreeRef":
    assert remote_type == "git"
    assert working_tree == "defaultwt"
    prototype = GitTreeRef(self, url_spec=remote_url, working_tree=working_tree)
    prototype.validate()
    tree_id = prototype.tree_id
    existing_dict = self._config.trees.get_tree_by_id(tree_id)
    if existing_dict is None:
      if not create:
        return None
      print("Added new tree {}".format(tree_id))
      self._config.trees.add_alias(prototype.default_local_path, tree_id)
      prototype.save()
      return prototype
    else:
      return BaseTreeRef.from_dict(self, d=existing_dict)

  def get_root_tree(self,
                    working_tree=DEFAULT_WORKING_TREE,
                    remote_type="git") -> "GitTreeRef":
    """Gets a special root tree representing the root of the repository.

    This is used when the repository root directory is itself a git repo
    that should be managed.
    """
    assert remote_type == "git"
    assert working_tree == "defaultwt"
    tree_id = "git/__root__"
    existing_dict = self._config.trees.get_tree_by_id(tree_id)
    if existing_dict is not None:
      return BaseTreeRef.from_dict(self, d=existing_dict)
    new_tree = GitTreeRef(self, url_spec="__root__", working_tree=working_tree)
    print("Adding new tree __root__")
    annotation = GitConfigAnnotation(tree_id=tree_id)
    annotation.save_to_git_root(self.path)
    self._config.trees.add_alias(self.path, tree_id)
    new_tree.save()
    return new_tree

  @staticmethod
  def find_existing(existing_path):
    mmrepo_dir = os.path.join(existing_path, MMREPO_DIR)
    universe_dir = os.path.join(mmrepo_dir, UNIVERSE_DIR)
    if os.path.isdir(mmrepo_dir) and os.path.isdir(universe_dir):
      return Repo(existing_path)
    else:
      return None

  @staticmethod
  def find_from_cwd(from_cwd: Optional[str] = None):
    if from_cwd is None:
      from_cwd = os.getcwd()
    prev_cwd = None
    cwd = from_cwd
    while cwd != prev_cwd:
      mmrepo_dir = os.path.join(cwd, MMREPO_DIR)
      universe_dir = os.path.join(mmrepo_dir, UNIVERSE_DIR)
      if os.path.isdir(mmrepo_dir) and os.path.isdir(universe_dir):
        return Repo(cwd)
      prev_cwd = cwd
      cwd = os.path.dirname(cwd)
    raise UserError("Could not find initialized mmrepo under {}", from_cwd)

  @staticmethod
  def init(from_cwd: Optional[str] = None):
    if from_cwd is None:
      from_cwd = os.getcwd()
    # Deny existing.
    try:
      existing = Repo.find_from_cwd(from_cwd=from_cwd)
    except UserError:
      pass
    else:
      raise UserError("Repository cannot be created under existing {}",
                      existing.path)
    # Create.
    repo_path = os.path.join(from_cwd, MMREPO_DIR)
    _make_dir(repo_path, exist_ok=True)
    universe_dir = os.path.join(repo_path, UNIVERSE_DIR)
    _make_dir(universe_dir, exist_ok=True)
    return Repo(from_cwd)


class BaseTreeRef:
  CONFIG_TYPE = None

  def __init__(self, repo: Repo):
    super().__init__()
    self._repo = repo

  def save(self):
    """Saves this tree to the config."""
    d = self.as_dict()
    d["t"] = self.CONFIG_TYPE
    self._repo.config.trees.tree_dicts[self.tree_id] = d
    self._repo.config.trees.save()

  @property
  def repo(self) -> Repo:
    return self._repo

  @staticmethod
  def from_dict(repo: Repo, d: dict):
    t = d["t"] if "t" in d else None
    if t == GitTreeRef.CONFIG_TYPE:
      return GitTreeRef.from_dict(repo, d)
    else:
      raise UserError("Error loading tree from config: unknown type {}", t)

  def as_dict(self) -> dict:
    """Encodes this instance as a dict."""
    raise NotImplementedError()

  def validate(self):
    """Validates that this is a legal tree ref.

    Raises:
      UserError on failure (which can be ignored if validation is optional).
    """
    pass

  @property
  def tree_id(self) -> str:
    """A unique identifier for the tree"""
    raise NotImplementedError()

  def checkout(self):
    """Checks out the tree into the universe."""
    raise NotImplementedError()

  @property
  def dependencies(self):
    """Gets the immediately dependent trees."""
    raise NotImplementedError()

  def make_link(self, target_path):
    """Makes a link from the physical repository to the specified target."""
    raise NotImplementedError()


class GitTreeRef(BaseTreeRef):
  """A reference to a git tree mapped into an mmr."""
  CONFIG_TYPE = "git"

  def __init__(self, repo: Repo, url_spec: str, working_tree: str):
    super().__init__(repo)
    self._origin = GitOrigin(url_spec)
    self._working_tree = working_tree
    self._deps = None
    self._submodule_deps_provider = None

  @staticmethod
  def from_dict(repo: Repo, d):
    url_spec = d["url"]
    working_tree = d["working_tree"]
    return GitTreeRef(repo=repo, url_spec=url_spec, working_tree=working_tree)

  def as_dict(self) -> dict:
    return {"url": self._origin.git_origin, "working_tree": self._working_tree}

  @property
  def tree_id(self) -> str:
    # TODO: The id should really be canonicalized based on some knowledge
    # of the origin.
    return "git/{}".format(self._origin.git_origin)

  def validate(self):
    self._origin.universe_path  # Validate

  def __eq__(self, other):
    if self is other:
      return True
    if type(other) is not GitTreeRef:
      return False
    return self._origin == other._origin

  def __hash__(self):
    return hash(self._origin)

  @property
  def url(self):
    return self._origin.git_origin

  @property
  def is_root_tree(self):
    return self.url == "__root__"

  @property
  def path_in_repo(self) -> str:
    if self.is_root_tree:
      return self.repo.path
    else:
      return os.path.join(self._repo.universe_dir, self._origin.universe_path)

  @property
  def default_local_path(self) -> str:
    """A path segment to use for a default checkout of the project.

    This defaults to the last directory component minus the ".git" suffix
    (similar to git).
    """
    if self.is_root_tree:
      return "__root__"
    return self._origin.default_alias

  @property
  def dependencies(self):
    self._init_deps()
    all_trees = set()
    for dep_provider in self._deps:
      all_trees.update(dep_provider.trees)
    return all_trees

  @property
  def dep_providers(self):
    self._init_deps()
    return self._deps

  def _init_deps(self):
    if self._deps:
      return
    # Add a default submodule deps provider.
    self._submodule_deps_provider = SubmoduleDepProvider(
        self.repo, self.path_in_repo)
    self._deps = [self._submodule_deps_provider]

    # See if there should be a JSON deps provider.
    json_deps_provider = JsonDepProvider.create_if_exists(
        repo=self.repo, parent_dir=self.path_in_repo)
    if json_deps_provider:
      self._deps.append(json_deps_provider)

  @property
  def clone_args(self):
    trees_config = self.repo.config.trees
    args = []

    # Reference or shared.
    other_repo_path = trees_config.reference_repo or trees_config.shared_repo
    if other_repo_path:
      other_repo = Repo.find_existing(other_repo_path)
      if other_repo:
        other_tree = other_repo.get_tree(self.url)
        if other_tree:
          if trees_config.reference_repo:
            args.extend(["--reference-if-able", other_tree.path_in_repo])
          elif trees_config.shared_repo:
            args.extend(["--shared", other_tree.path_in_repo])
    return args

  def __repr__(self):
    return "GitTree(url={}, working_tree={})".format(self._origin,
                                                     self._working_tree)

  def checkout(self):
    path = self.path_in_repo
    if not self.is_root_tree:
      if not self.repo.git.is_git_repository(path):
        self.repo.git.clone(self._origin.git_origin,
                            path,
                            clone_args=self.clone_args)
        self._deps = None
      else:
        print("Skipping clone of {} (already exists)".format(self._origin))

    # Make sure that submodule initialization has been done.
    # Even though we aren't actually doing recursive checkouts here, it is
    # necessary to initialize various git structures.
    for dep_provider in self.dep_providers:
      dep_provider.initialize()

  def make_link(self, target_path):
    if self.is_root_tree:
      return
    source_path = self.path_in_repo
    # Update the annotation.
    annotation = GitConfigAnnotation(tree_id=self.tree_id)
    annotation.save_to_git_root(source_path)

    if os.path.exists(target_path) or os.path.islink(target_path):
      if not os.path.islink(target_path):
        raise UserError("Cannot link tree: {} (path exists)", target_path)
      existing_target = os.readlink(target_path)
      if existing_target == source_path:
        print(
            "Not creating link because the path '{}' is already linked correctly"
            .format(target_path), " ({})".format(target_path))
        return
      raise UserError("Cannot link tree: {} (path is already linked to {})",
                      target_path, source_path)
    print("Create symlink {} -> '{}'".format(source_path, target_path))
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    fileutils.make_relative_link(source_path,
                                 target_path,
                                 self.repo.path,
                                 target_is_directory=True)

  def update_version(self, version):
    """Updates the version for this tree."""
    self.repo.git.checkout_version(repository=self.path_in_repo,
                                   version=version)


class BaseDepProvider:
  """Provides access to dependencies for a tree."""

  @property
  def trees(self):
    """Gets a list of the remotes corresponding to the submodules."""
    raise NotImplementedError()

  def initialize(self):
    """Performs clone or update time initialization."""
    raise NotImplementedError()


class JsonDepProvider(BaseDepProvider):
  """Light-weight dep provider that processes a module_deps.json file."""
  DEFAULT_DEPS_FILENAME = "module_deps.json"

  def __init__(self, repo: Repo, deps_file: str):
    super().__init__()
    self._repo = repo
    self._deps_file = deps_file

  @property
  def parent_dir(self):
    return os.path.dirname(self._deps_file)

  @classmethod
  def create_if_exists(cls, repo: Repo, parent_dir: str):
    """Creates a provider if the deps file exists."""
    deps_file = os.path.join(parent_dir, cls.DEFAULT_DEPS_FILENAME)
    if os.path.isfile(deps_file):
      return cls(repo=repo, deps_file=deps_file)
    return None

  def initialize(self):
    dep_records = DepRecord.read_from_file(self._deps_file)
    for dep_record in dep_records:
      try:
        tree = self._repo.get_tree(dep_record.url,
                                   working_tree=DEFAULT_WORKING_TREE,
                                   remote_type="git")
      except UserError as e:
        print("** ERROR INITIALIZING DEPENDENCY (skipped):", dep_record.url)
        print(e.message)
        continue
      for target_path in dep_record.paths:
        local_path = os.path.join(self.parent_dir, target_path)
        # Setup the symlink.
        if os.path.islink(local_path):
          # Update the link (for tidyness and better self correction).
          os.unlink(local_path)
        elif os.path.exists(local_path):
          raise UserError(
              "Dependency path {} must not exist or be a symlink".format(
                  local_path))
        tree.make_link(local_path)

  @property
  def trees(self):
    dep_records = DepRecord.read_from_file(self._deps_file)
    trees = []
    for dep_record in dep_records:
      try:
        trees.append(
            self._repo.get_tree(dep_record.url,
                                working_tree=DEFAULT_WORKING_TREE,
                                remote_type="git"))
      except UserError as e:
        print("** ERROR INITIALIZING DEPENDENCY (skipped):", dep_record.url)
        print(e.message)
    return trees


class SubmoduleDepProvider(BaseDepProvider):
  """Encapsulates access to submodule dependencies of a git repo."""

  def __init__(self, repo, git_path):
    super().__init__()
    self._repo = repo
    self._git_path = git_path
    self._module_info_dict = self.repo.git.parse_gitmodules(git_path)

  @property
  def repo(self) -> Repo:
    return self._repo

  @property
  def has_submodules(self) -> bool:
    return bool(self._module_info_dict)

  @property
  def git_path(self) -> str:
    return self._git_path

  @property
  def trees(self):
    """Gets a list of the remotes corresponding to the submodules."""
    trees = []
    for info in self._module_info_dict.values():
      try:
        trees.append(self._tree_for_module_info(info))
      except UserError as e:
        print("** ERROR INITIALIZING DEPENDENCY (skipped):", info)
        print(e.message)
        continue
    return trees

  def _tree_for_module_info(self, module_info):
    return self._repo.get_tree(remote_url=module_info.url,
                               working_tree=DEFAULT_WORKING_TREE,
                               remote_type="git")

  def _tree_for_path(self, local_path):
    return self._tree_for_module_info(self._module_info_dict[local_path])

  def initialize(self):
    """Performs clone or update time initialization of submodules.

    This step is necessary, regardless of whether the submodules have been
    populated in order to make git release its hold on them.
    """
    if not self.has_submodules:
      return
    for module_info in self._module_info_dict.values():
      try:
        module_tree_ref = self._tree_for_module_info(module_info)
      except UserError as e:
        print("** ERROR INITIALIZING DEPENDENCY (skipped):", module_info)
        print(e.message)
        continue

      module_tree_path = module_tree_ref.path_in_repo
      module_path = os.path.join(self._git_path, module_info.path)

      # Tell git "hands off"!
      self.repo.git.skip_worktree(repository=self._git_path,
                                  path=module_info.path)

      # Setup the symlink.
      if os.path.islink(module_path):
        # Update the link (for tidyness and better self correction).
        os.unlink(module_path)
        module_tree_ref.make_link(module_path)
      elif (not os.path.exists(module_path) or os.path.isdir(module_path)):
        # Create the symlink.
        print("Redirecting submodule {} to {}".format(module_info.path,
                                                      module_tree_path))
        if os.path.exists(module_path):
          os.rmdir(module_path)
        module_tree_ref.make_link(module_path)

  def lookup_versions(self):
    """Looks up requested versions for dependent trees.

    Returns:
      Sequence of (dep_tree, version).
    """
    path_versions = self.repo.git.parse_submodule_versions(
        repository=self._git_path)
    results = []
    for path, version in path_versions:
      try:
        results.append((self._tree_for_path(path), version))
      except UserError as e:
        print("** ERROR INITIALIZING DEPENDENCY (skipped):", path)
        print(e.message)
        continue
    return results


def _make_dir(path: str, exist_ok=False):
  try:
    os.makedirs(path, exist_ok=exist_ok)
  except FileExistsError:
    raise UserError("Unable to create directory {} (exists)", path)
  except OSError:
    raise UserError("Unable to create directory {}", path)
