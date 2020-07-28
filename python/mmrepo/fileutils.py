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
"""Utilities for file and directory management."""

import os
from pathlib import Path

__all__ = []


def make_relative_link(src, dst, relative_to, target_is_directory=False):
  """Makes a symlink from src -> dst, relative to a common root.

  Note that not all operating systems will actually preserve the relative
  structure, but this does work on Unix-like systems. This is also where we
  want to use docker and have self contained checkouts with nothing but
  relative links.
  """
  src = Path(src).resolve()
  dst = Path(dst).resolve()
  relative_to = Path(relative_to).resolve()
  dst_check = dst.parent
  # Accumulate destination backtrack paths.
  link_accum = None
  found_common = False
  for dst_parent in dst.parents:
    if dst_parent == relative_to:
      found_common = True
      break
    if link_accum:
      link_accum = link_accum.joinpath("..")
    else:
      link_accum = Path("..")
  if not found_common:
    raise ValueError("Link destination {} is not relative to {}".format(
        dst, relative_to))
  # And add the source.
  link_accum = link_accum.joinpath(src.relative_to(relative_to))
  os.symlink(link_accum, dst, target_is_directory=target_is_directory)


def is_same_path(path1, path2) -> bool:
  path1 = Path(path1).resolve()
  path2 = Path(path2).resolve()
  return path1 == path2
