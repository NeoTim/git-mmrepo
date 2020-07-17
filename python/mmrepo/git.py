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

"""Git helpers."""

import collections
import os
import re
import subprocess
import sys
import urllib.parse

from mmrepo.common import *

SubmoduleInfo = collections.namedtuple("SubmoduleInfo", "url,path")

PRINT_ALL = True

__all__ = [
    "GitExecutor",
    "GitOrigin",
]


class GitExecutor:
  """Wraps access to running git commands."""

  def is_git_repository(self, path):
    """Returns whether the given path appears to be a git repo."""
    if not os.path.isfile(os.path.join(path, ".git", "HEAD")):
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
    try:
      if PRINT_ALL or not silent:
        print("+", " ".join(args), "  [from %s]" % cwd)
      if capture_output:
        return subprocess.check_output(args, cwd=cwd, **kwargs)
      else:
        return subprocess.check_call(args, cwd=cwd, **kwargs)
    except subprocess.CalledProcessError:
      message = "\n".join([
          "Error executing command:",
          "  cd {}".format(cwd),
          "  {}".format(" ".join(args)),
      ])
      raise UserError(message)


class GitOrigin:
  """Wraps a git URL, applying some normalization.

  HTTPS origins:
    >>> https_origin = GitOrigin("https://github.com/stellaraccident/mlir-federation.git")
    >>> https_origin.git_origin
    'https://github.com/stellaraccident/mlir-federation.git'
    >>> https_origin.universe_path
    'github.com/stellaraccident/mlir-federation.git'
    >>> https_origin.default_alias
    'mlir-federation'

  SSH origins:
    >>> ssh_origin = GitOrigin("git@github.com:stellaraccident/mlir-federation.git")
    >>> ssh_origin.git_origin
    'git@github.com:stellaraccident/mlir-federation.git'
    >>> ssh_origin.universe_path
    'github.com/stellaraccident/mlir-federation.git'
    >>> ssh_origin.default_alias
    'mlir-federation'
  """

  def __init__(self, spec):
    super().__init__()
    self._spec = spec

  def __eq__(self, other):
    return self._spec == other._spec

  def __hash__(self):
    return hash(self._spec)

  def __repr__(self):
    return self._spec

  @property
  def git_origin(self) -> str:
    return self._spec

  @property
  def universe_path(self) -> str:
    """Returns a unique path for this in the universe.

    Ideally, this normalizes SSH and HTTPS access mechanisms for a host
    so that they produce the same universe location.
    """
    if self._spec.startswith("https://") or self._spec.startswith("http://"):
      # Extract {netloc}{path}
      url = urllib.parse.urlsplit(self._spec)
      norm_path = url.path
      # Remove leading '/', making it relative.
      if norm_path and norm_path[0] == "/":
        norm_path = norm_path[1:]
      # TODO: Be more exacting in scrubbing the path?
      norm_path = norm_path.replace("/", os.path.sep)
      assert not os.path.isabs(norm_path)
      return os.path.join(url.netloc, norm_path)
    else:
      # Assume SSH.
      try:
        split_pos = self._spec.index(":")
      except ValueError:
        raise UserError(
            "Git origin does not appear to be an SSH path: {}".format(
                self._spec))
      netloc = self._spec[0:split_pos]
      path = self._spec[split_pos + 1:]
      try:
        atpos = netloc.index("@")
      except ValueError:
        pass  # No user.
      else:
        netloc = netloc[atpos + 1:]
      if path and path[0] == "/":
        path = path[1:]
      # TODO: Be more exacting in scrubbing the path?
      path = path.replace("/", os.path.sep)
      assert not os.path.isabs(path)
      return os.path.join(netloc, path)

  @property
  def default_alias(self) -> str:
    """Return a default short alias name for this repo.

    This is typically the last component of the path, minus any .git suffix.
    """
    basename = os.path.basename(self.universe_path)
    if basename.endswith(".git"):
      return basename[0:-4]
    return basename


if __name__ == "__main__":
  import doctest
  doctest.testmod()
