"""Show info about the current mmrepo."""

from mmrepo.repo import *

HELP_MESSAGE = """Displays information about the current magical monorepo."""


def exec(*args):
  if args:
    raise UserError("'info' expects no arguments'")
  r = Repo.find_from_cwd()
  print("top:", r.path)
  print("mmrepo:", r.mmrepo_dir)
  print("universe:", r.universe_dir)
