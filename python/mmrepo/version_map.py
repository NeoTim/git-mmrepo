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
"""Support for manipulating version maps."""

from collections import namedtuple
import re

from mmrepo.common import *
from mmrepo.repo import *

__all__ = [
    "VersionComponent",
    "VersionMap",
]

EXTRACT_RESOLVED_PAT = re.compile(r"""(.*)=([^=]+)""")
EXTRACT_SYMBOLIC_PAT = re.compile(r"""(.*)@([^@]+)""")
WHITESPACE_PAT = re.compile(r"""[\s|\n|\r]+""")


class VersionComponent(
    namedtuple("VersionComponent",
               ["tree", "resolved_version", "symbolic_version"],
               defaults=[None, None])):
  """Represents a version of a specific tree.

  Consists of:
    tree: A BaseTreeRef
    resolved_version: Commit id (or None if not resolved)
    symbolic_version: A named reference to a version which needs to be resolved

  Syntactically a version component is typically specified as:
    `tree_id|alias` [`@` `symbolic_version`] [`=` `resolved_version`]

  When parsing, either an alias or tree_id is permitted, but when stringifying,
  the tree_id form is generated.
  """

  @staticmethod
  def parse(spec) -> "VersionComponent":
    """Parses the spec, not resolving the tree.

      >>> VersionComponent.parse("foo")
      VersionComponent(tree='foo', resolved_version=None, symbolic_version=None)
      >>> VersionComponent.parse("foo@HEAD")
      VersionComponent(tree='foo', resolved_version=None, symbolic_version='HEAD')
      >>> VersionComponent.parse("foo@HEAD=abcdefg")
      VersionComponent(tree='foo', resolved_version='abcdefg', symbolic_version='HEAD')
      >>> VersionComponent.parse("git/https://github.com/foo@HEAD=abcdefg")
      VersionComponent(tree='git/https://github.com/foo', resolved_version='abcdefg', symbolic_version='HEAD')
      >>> VersionComponent.parse("git/https://github.com/foo=abcdefg")
      VersionComponent(tree='git/https://github.com/foo', resolved_version='abcdefg', symbolic_version=None)
    """
    tree_spec = None
    resolved_version = None
    symbolic_version = None
    # Extract the resolved version.
    m = EXTRACT_RESOLVED_PAT.match(spec)
    if m:
      resolved_version = m.group(2)
      spec = m.group(1)
    # Extract the symbolic version.
    m = EXTRACT_SYMBOLIC_PAT.match(spec)
    if m:
      symbolic_version = m.group(2)
      spec = m.group(1)
    tree_spec = spec
    return VersionComponent(tree=tree_spec,
                            resolved_version=resolved_version,
                            symbolic_version=symbolic_version)

  def __str__(self):
    s = ""
    if isinstance(self.tree, BaseTreeRef):
      s += self.tree.tree_id
    else:
      s += self.tree
    if self.symbolic_version is not None:
      s += "@" + self.symbolic_version
    if self.resolved_version is not None:
      s += "=" + self.resolved_version
    return s

  def resolve(self, repo: Repo) -> "VersionComponent":
    """Parses the spec, resolving the tree to an existing instance."""
    # Try to resolve as a tree id.
    tree_spec = self.tree
    tree = tree_spec
    if not isinstance(tree, BaseTreeRef):
      tree = repo.tree_from_id(tree_spec)
      if tree is None:
        tree = repo.tree_from_alias(tree_spec)
      if tree is None:
        raise UserError("Tree '{}' is not known in the repository",
                        tree_specs)

    # If no resolved_commit, try to resolve it.
    resolved_version = self.resolved_version
    symbolic_version = self.symbolic_version
    if resolved_version is None:
      symbolic_version = (symbolic_version
                          if symbolic_version is not None else "HEAD")
      remote_refs = repo.git.ls_remote(tree.url)
      if symbolic_version in remote_refs:
        resolved_version = remote_refs[symbolic_version]
      else:
        raise UserError("Symbolic version '{}' not found for remote '{}'",
                        symbolic_version, tree.url)
    return self._replace(tree=tree,
                         symbolic_version=symbolic_version,
                         resolved_version=resolved_version)


class VersionMap:
  """Encapsulates a version map.

  A version map is an ordered list of (tree, version) tuples that encapsulates
  the version state of a span of the repository. In typical use, version maps
  are sparse, specifying the versions of key components, while letting others
  float to the versions as specified by the first authoritative dependency.
  """

  def __init__(self, components=()):
    super().__init__()
    self.components = tuple(components)

  def __repr__(self):
    return "VersionMap({})".format(str(self))

  def __str__(self):
    return " ".join((str(c) for c in self.components))

  @staticmethod
  def parse(*specs):
    r"""Parses a string of specs into components.

    Each spec will be split by whitespace.

      >>> VersionMap.parse("foo bar")
      VersionMap(foo bar)
      >>> VersionMap.parse("foo \r\n bar gah")
      VersionMap(foo bar gah)
    """
    components = list()
    for spec in specs:
      spec_split = WHITESPACE_PAT.split(spec)
      components.extend((VersionComponent.parse(s) for s in spec_split))
    return VersionMap(components)

  def resolve(self, repo: Repo):
    """Resolves all components of the version map, returning a new one."""
    return VersionMap([c.resolve(repo) for c in self.components])


if __name__ == "__main__":
  import doctest
  doctest.testmod()
