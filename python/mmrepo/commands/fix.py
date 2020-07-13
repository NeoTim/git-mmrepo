from mmrepo.config import *
from mmrepo.repo import *

HELP_MESSAGE = """Fixes trees after repository events.

Certain repository events (pull, reset --hard, etc) can leave tree dependency
links in an inconsistent state. This resets them.
"""

def exec(*args):
  if args:
    raise UserError("Arguments not expected")
  repo = Repo.find_from_cwd()
  tree = repo.tree_from_cwd()
  tree.checkout()
