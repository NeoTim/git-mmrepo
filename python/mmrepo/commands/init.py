"""Initialize a new mmrepo."""

from mmrepo.repo import *

HELP_MESSAGE = """Initializes a new magical mono repository.

By default, the repository will be initialized in the current directory.
It is an error to initialize a repository inside of an existing repository.
"""

def exec(*args):
  r = Repo.init()
  print("Initialized new magical monorepo at {}".format(r.path))
