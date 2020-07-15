from mmrepo.repo import *

HELP_MESSAGE = """Checks out a git repository tree.

Syntax: mmr checkout <repository url> [local path]
"""

def checkout(repo, tree):
  print("Checking out tree {}".format(tree))
  tree.checkout()


def exec(*args):
  if len(args) == 1:
    tree_url = args[0]
    local_path = None
  elif len(args) == 2:
    tree_url, local_path = args

  # Checkout the repository.
  repo = Repo.find_from_cwd()
  tree = repo.get_tree(tree_url)
  checkout(repo, tree)

  # Create the requested link.
  if local_path is None:
    local_path = tree.default_local_path
  tree.make_link(local_path)

  # Collect recursive dependencies.
  recursive_processed = set()
  recursive_errored = set()
  all_depends = set()

  all_depends.add(tree)
  recursive_processed.add(tree)
  all_depends.update(tree.dependencies)

  while all_depends != recursive_processed:
    for tree_dep in all_depends:
      if tree_dep in recursive_processed:
        continue
      recursive_processed.add(tree_dep)
      checkout(repo, tree_dep)

  # Report.
  print("** Processed {} repositories".format(len(all_depends)))
  if recursive_errored:
    print("!! {} repositories had errors:".format(len(recursive_errored)))
    for error_remote in recursive_errored:
      print("  {}".format(error_remote))
