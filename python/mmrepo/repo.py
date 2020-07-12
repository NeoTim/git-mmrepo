"""Overall repository management."""

from typing import Optional
import os

MMREPO_DIR = ".mmrepo"
UNIVERSE_DIR = "universe"

__all__ = [
    "Repo",
    "UserError",
]


def _make_dir(path: str, exist_ok=False):
  try:
    os.makedirs(path, exist_ok=exist_ok)
  except FileExistsError:
    raise UserError("Unable to create directory {} (exists)", path)
  except OSError:
    raise UserError("Unable to create directory {}", path)


class Repo:
  """Represents an on-disk repository."""

  def __init__(self, path: str):
    super().__init__()
    self._path = path

  @property
  def path(self) -> str:
    return self._path

  @property
  def universe_dir(self) -> str:
    return os.path.join(self._path, MMREPO_DIR, UNIVERSE_DIR)

  @property
  def mmrepo_dir(self) -> str:
    return os.path.join(self._path, MMREPO_DIR)

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


class UserError(Exception):
  """A user-reportable error."""

  def __init__(self, message: str, *args, **kwargs):
    super().__init__(message.format(*args, **kwargs))

  @property
  def message(self) -> str:
    return self.args[0]
