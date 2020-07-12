from mmrepo.repo import *

HELP_MESSAGE = """Prints the top directory of the current repo."""


def exec(*args):
  if args:
    raise UserError("'top' expects no arguments'")
  r = Repo.find_from_cwd()
  print(r.path)
