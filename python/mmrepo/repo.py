"""Overall repository management."""

from typing import Optional
import os
import urllib.parse

from mmrepo.common import *
from mmrepo.config import *
from mmrepo.git import GitExecutor

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
               remote_type="git") -> "GitTreeRef":
    assert remote_type == "git"
    assert working_tree == "defaultwt"
    prototype = GitTreeRef(self, url_spec=remote_url, working_tree=working_tree)
    prototype.validate()
    tree_id = prototype.tree_id
    existing_dict = self._config.trees.get_tree_by_id(tree_id)
    if existing_dict is None:
      print("Added new tree {}".format(tree_id))
      prototype.save()
      return prototype
    else:
      return BaseTreeRef.from_dict(self, d=existing_dict)

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
      raise UserError("Cannot initialize: Existing repo at {}", existing.path)
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
    self._url_spec = url_spec
    self._working_tree = working_tree
    self._url = urllib.parse.urlsplit(url_spec)
    self._deps = None
    self._submodule_deps_provider = None

  @staticmethod
  def from_dict(repo: Repo, d):
    url_spec = d["url"]
    working_tree = d["working_tree"]
    return GitTreeRef(repo=repo, url_spec=url_spec, working_tree=working_tree)

  def as_dict(self) -> dict:
    return {"url": self._url_spec, "working_tree": self._working_tree}

  @property
  def tree_id(self) -> str:
    # TODO: The id should really be canonicalized based on some knowledge
    # of the origin.
    return "git/{}".format(self._url_spec)

  def validate(self):
    if self._url.scheme not in ["http", "https", "ssh"]:
      raise UserError("Unsupported git remote scheme: {}", self._url.scheme)

  def __eq__(self, other):
    if self is other:
      return True
    if type(other) is not GitTreeRef:
      return False
    return self._url_spec == other._url_spec

  def __hash__(self):
    return hash(self._url_spec)

  @property
  def url(self):
    return self._url

  @property
  def declared_local_path(self) -> str:
    """Path name components normalized to local system requirements."""
    norm_path = self._url.path
    # Remove leading '/', making it relative.
    if norm_path and norm_path[0] == "/":
      norm_path = norm_path[1:]
    # TODO: Be more exacting in scrubbing the path?
    norm_path = norm_path.replace("/", os.path.sep)
    assert not os.path.isabs(norm_path)
    return norm_path

  @property
  def path_in_repo(self) -> str:
    url = self._url
    return os.path.join(self._repo.universe_dir, self._working_tree, url.netloc,
                        self.declared_local_path)

  @property
  def default_local_path(self) -> str:
    """A path segment to use for a default checkout of the project.

    This defaults to the last directory component minus the ".git" suffix
    (similar to git).
    """
    basename = os.path.basename(self.declared_local_path)
    if basename.endswith(".git"):
      return basename[0:-4]
    return basename

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
    self._submodule_deps_provider = SubmoduleDepProvider(
        self.repo, self.path_in_repo)
    self._deps = [self._submodule_deps_provider]

  def __repr__(self):
    return "GitTree(url={}, working_tree={})".format(self._url_spec,
                                                     self._working_tree)

  def checkout(self):
    path = self.path_in_repo
    if not self.repo.git.is_git_repository(path):
      self.repo.git.clone(self._url_spec, path)
      self._deps = None
    else:
      print("Skipping clone of {} (already exists)".format(self._url_spec))

    # Make sure that submodule initialization has been done.
    # Even though we aren't actually doing recursive checkouts here, it is
    # necessary to initialize various git structures.
    self._init_deps()
    self._submodule_deps_provider.initialize()

  def make_link(self, target_path):
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
            .format(target_path))
        return
      raise UserError("Cannot link tree: {} (path is already linked to {})",
                      target_path, source_path)
    print("Create symlink {} -> '{}'".format(source_path, target_path))
    os.symlink(source_path, target_path, target_is_directory=True)

  def update_version(self, version):
    """Updates the version for this tree."""
    self.repo.git.checkout_version(repository=self.path_in_repo, version=version)


class SubmoduleDepProvider:
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
    return [
        GitTreeRef(self._repo,
                   url_spec=info.url,
                   working_tree=DEFAULT_WORKING_TREE)
        for info in self._module_info_dict.values()
    ]

  def _tree_for_module_info(self, module_info):
    return GitTreeRef(self.repo,
                      url_spec=module_info.url,
                      working_tree=DEFAULT_WORKING_TREE)

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
      module_tree_ref = self._tree_for_module_info(module_info)
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
    return [
        (self._tree_for_path(path), version)
        for path, version in path_versions
    ]


def _make_dir(path: str, exist_ok=False):
  try:
    os.makedirs(path, exist_ok=exist_ok)
  except FileExistsError:
    raise UserError("Unable to create directory {} (exists)", path)
  except OSError:
    raise UserError("Unable to create directory {}", path)
