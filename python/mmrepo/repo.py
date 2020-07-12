"""Overall repository management."""

from typing import Optional
import os
import urllib.parse

from mmrepo.git import GitExecutor

MMREPO_DIR = ".mmrepo"
UNIVERSE_DIR = "universe"

__all__ = [
    "GitRemoteRef",
    "Repo",
    "UserError",
]


class Repo:
  """Represents an on-disk repository."""

  def __init__(self, path: str):
    super().__init__()
    self._path = os.path.realpath(path)
    self._git = GitExecutor()

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

  def get_remote(self, remote_url: str, remote_type="git") -> "GitRemoteRef":
    assert remote_type == "git"
    remote = GitRemoteRef(self, remote_url)
    return remote

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


class GitRemoteRef:
  """A reference to a git remote mapped into an mmr."""

  def __init__(self, repo: Repo, url_spec: str):
    super().__init__()
    self._repo = repo
    self._url_spec = url_spec
    self._url = urllib.parse.urlsplit(url_spec)
    self._deps = None
    self._submodule_deps = None

  def validate(self):
    """Validates that this is a legal remote.

    Raises:
      UserError on failure (which can be ignored if validation is optional).
    """
    if self._url.scheme not in ["http", "https", "ssh"]:
      raise UserError("Unsupported git remote scheme: {}", self._url.scheme)

  def __eq__(self, other):
    if self is other: return True
    if type(other) is not GitRemoteRef: return False
    return self._url_spec == other._url_spec

  def __hash__(self):
    return hash(self._url_spec)

  @property
  def repo(self) -> Repo:
    return self._repo

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
    return os.path.join(self._repo.universe_dir, url.netloc,
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
    """Gets the immediately dependent remotes."""
    self._init_deps()
    all_remotes = set()
    for dep_provider in self._deps:
      all_remotes.update(dep_provider.remotes)
    return all_remotes

  def _init_deps(self):
    if self._deps:
      return
    self._submodule_deps = SubmoduleDeps(self.repo, self.path_in_repo)
    self._deps = [self._submodule_deps]

  def __repr__(self):
    return "GitRemote({})".format(self._url_spec)

  def checkout(self):
    """Checks out the remote into the universe."""
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
    self._submodule_deps.initialize()

  def make_link(self, target_path):
    """Makes a link from the physical repository to the specified target."""
    source_path = self.path_in_repo
    if os.path.exists(target_path) or os.path.islink(target_path):
      if not os.path.islink(target_path):
        raise UserError("Cannot link remote: {} (path exists)", target_path)
      existing_target = os.readlink(target_path)
      if existing_target == source_path:
        print(
            "Not creating link because the path '{}' is already linked correctly"
            .format(target_path))
        return
      raise UserError("Cannot link remote: {} (path is already linked to {})",
                      target_path, source_path)
    print("Create symlink {} -> '{}'".format(source_path, target_path))
    os.symlink(source_path, target_path, target_is_directory=True)


class SubmoduleDeps:
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
  def remotes(self):
    """Gets a list of the remotes corresponding to the submodules."""
    return [
        GitRemoteRef(self._repo, info.url)
        for info in self._module_info_dict.values()
    ]

  def initialize(self):
    """Performs clone or update time initialization of submodules.

    This step is necessary, regardless of whether the submodules have been
    populated in order to make git release its hold on them.
    """
    if not self.has_submodules:
      return
    for module_info in self._module_info_dict.values():
      module_remote_ref = GitRemoteRef(self.repo, module_info.url)
      module_remote_path = module_remote_ref.path_in_repo
      module_path = os.path.join(self._git_path, module_info.path)

      # Tell git "hands off"!
      self.repo.git.skip_worktree(repository=self._git_path,
                                  path=module_info.path)

      # Setup the symlink.
      if os.path.islink(module_path):
        # Update the link (for tidyness and better self correction).
        os.unlink(module_path)
        module_remote_ref.make_link(module_path)
      elif (not os.path.exists(module_path) or os.path.isdir(module_path)):
        # Create the symlink.
        print("Redirecting submodule {} to {}".format(module_info.path,
                                                      module_remote_path))
        if os.path.exists(module_path):
          os.rmdir(module_path)
        module_remote_ref.make_link(module_path)


def _make_dir(path: str, exist_ok=False):
  try:
    os.makedirs(path, exist_ok=exist_ok)
  except FileExistsError:
    raise UserError("Unable to create directory {} (exists)", path)
  except OSError:
    raise UserError("Unable to create directory {}", path)


class UserError(Exception):
  """A user-reportable error."""

  def __init__(self, message: str, *args, **kwargs):
    super().__init__(message.format(*args, **kwargs))

  @property
  def message(self) -> str:
    return self.args[0]
