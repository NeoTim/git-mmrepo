from mmrepo.repo import *

HELP_MESSAGE = """Checks out a remote git repository.

Syntax: mmr checkout <repository url> [local path]
"""

def checkout(repo, remote):
  print("Checking out remote {}".format(remote))
  remote.checkout()


def exec(*args):
  if len(args) == 1:
    remote_url = args[0]
    local_path = None
  elif len(args) == 2:
    remote_url, local_path = args

  # Checkout the repository.
  repo = Repo.find_from_cwd()
  remote = repo.get_remote(remote_url)
  checkout(repo, remote)

  # Create the requested link.
  if local_path is None:
    local_path = remote.default_local_path
  remote.make_link(local_path)

  # Collect recursive dependencies.
  recursive_processed = set()
  recursive_errored = set()
  all_depends = set()

  all_depends.add(remote)
  recursive_processed.add(remote)
  all_depends.update(remote.dependencies)

  while all_depends != recursive_processed:
    for remote_dep in all_depends:
      if remote_dep in recursive_processed:
        continue
      recursive_processed.add(remote_dep)
      print("Checking out remote {}".format(remote_dep))
      checkout(repo, remote_dep)

  # Report.
  print("** Processed {} repositories".format(len(all_depends)))
  if recursive_errored:
    print("!! {} repositories had errors:".format(len(recursive_errored)))
    for error_remote in recursive_errored:
      print("  {}".format(error_remote))
