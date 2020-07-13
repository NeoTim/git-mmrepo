"""Git helpers."""

import collections
import os
import subprocess

SubmoduleInfo = collections.namedtuple("SubmoduleInfo", "url,path")


class GitExecutor:
  """Wraps access to running git commands."""

  def is_git_repository(self, path):
    """Returns whether the given path appears to be a git repo."""
    if not os.path.isdir(os.path.join(path, ".git")):
      return False
    self.find_git_toplevel(cwd=path)  # For sanity
    return True

  def find_git_toplevel(self, cwd):
    """Finds the containing git top-level directory at the given cwd."""
    return self.execute(["git", "rev-parse", "--show-toplevel"],
                        cwd=cwd,
                        capture_output=True,
                        silent=True).strip().decode("UTF-8")

  def clone(self, repository, directory):
    """Clones the given repository into a directory."""
    if os.path.exists(directory):
      raise GitError("Cannot clone into {} (directory entry exists)", directory)
    return self.execute(["git", "clone", repository, directory],
                        cwd=os.getcwd())

  def skip_worktree(self, repository, path):
    """Marks a path in the repository with --skip-worktree."""
    self.execute(["git", "update-index", "--skip-worktree", path],
                 cwd=repository)

  def parse_gitmodules(self, repository):
    """Parses the .gitmodules file into a more sane structure."""
    gitmodules_file = os.path.join(repository, ".gitmodules")
    if not os.path.isfile(gitmodules_file):
      return {}
    props_lines = self.execute(
        ["git", "config", "-f", gitmodules_file, "-l"],
        cwd=repository,
        capture_output=True,
        silent=True).strip().decode("UTF-8").splitlines()
    props_splits = [line.split("=", 1) for line in props_lines]
    props_dict = {s[0]: s[1] for s in props_splits}
    # Keys are of the form:
    #   submodule./for/some/path.path
    # To get unique key prefixes, just scan for keys that end in ".path" and
    # chop.
    suffix = ".path"
    key_prefixes = [
        k[0:-len(suffix)] for k in props_dict.keys() if k.endswith(suffix)
    ]

    module_info_dict = {}
    for key_prefix in key_prefixes:
      try:
        path = props_dict[key_prefix + ".path"]
        url = props_dict[key_prefix + ".url"]
      except IndexError:
        continue
      module_info_dict[path] = SubmoduleInfo(url=url, path=path)
    return module_info_dict

  def parse_submodule_versions(self, repository):
    """Parses the submodule versions.

    Returns:
      Sequence of (path, version).
    """
    # This works even for not inited submodules (but prints a '-' in the first
    # char).
    status_lines = self.execute(
        ["git", "submodule", "status"],
        cwd=repository,
        capture_output=True,
        silent=True).strip().decode("UTF-8").splitlines()
    results = []
    for line in status_lines:
      line = line.strip()
      if line.startswith("-"):
        line = line[1:]
      version, path = line.split(" ", 1)
      results.append((path, version))
    return results

  def checkout_version(self, repository, version):
    """Checks out a version from a repository.

    Fails if the repository is dirty.
    """
    self.execute(["git", "fetch"], cwd=repository)
    self.execute(["git", "checkout", version], cwd=repository)

  def execute(self, args, cwd, capture_output=False, silent=False, **kwargs):
    """Executes a command.
    Args:
      args: List of command line arguments.
      cwd: Directory to execute in.
      capture_output: Whether to capture the output.
      silent: Whether to skip logging the invocation.
      **kwargs: Extra arguments to pass to subprocess.exec
    Returns:
      The output if capture_output, otherwise None.
    """
    if not silent:
      print("+", " ".join(args), "  [from %s]" % cwd)
    if capture_output:
      return subprocess.check_output(args, cwd=cwd, **kwargs)
    else:
      return subprocess.check_call(args, cwd=cwd, **kwargs)


class GitError(Exception):
  """An error from git."""

  def __init__(self, message: str, *args, **kwargs):
    super().__init__(message.format(*args, **kwargs))

  @property
  def message(self) -> str:
    return self.args[0]
