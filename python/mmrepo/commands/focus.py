from mmrepo.config import *
from mmrepo.repo import *

HELP_MESSAGE = """Focuses on the current tree, setting all dependent versions.

This updates the cone of dependencies to the most authoritative versions based
on proximity to this root.
"""

def exec(*args):
  if args:
    raise UserError("Arguments not expected")
  repo = Repo.find_from_cwd()
  tree = repo.tree_from_cwd()

  # TODO: This should traverse the graph.
  dep_providers = tree.dep_providers
  tree_versions = {}
  for dep_provider in dep_providers:
    for dep_tree, version in dep_provider.lookup_versions():
      if dep_tree in tree_versions:
        print("Skipping existing tree version {} = {}".format(dep_tree, version))
      tree_versions[dep_tree] = version

  for dep_tree, version in tree_versions.items():
    print("Updating tree {} to {}".format(dep_tree, version))
    dep_tree.update_version(version)
