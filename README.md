# Magical Monorepo for Git (MMR)

DISCLAIMER: This tool is primarily being co-developed with some related
project release tools, and it is almost certainly not in a state for
general use. We are using it for managing project graphs for CI systems,
and it is quite a ways from being a general tool for developers.

Manage a graph of projects related by submodules as an actual graph.

## What problem is this addressing?

This tool attempts to stitch together a graph of git repos that may have
mutual or duplicated dependencies (by way of submodules or JSON descriptors).

Unlike other tools, it aims to meet existing repositories where they are,
either using submodule metadata to build the dependency graph or using
more explicit mechanisms. The result is an ability to clone a root project
that references a graph of repos that use various dependency styles and
manage their versions holistically.

## What is it doing?

In submodule emulation mode, MMR ever so politely tells git to stop being 
the user-agent for managing submodules. In order to use it, the primary 
thing you need to change about your git workflow is to never invoke any of 
the "git submodule ..." commands again.

## Getting started.

Clone or otherwise acquire this repo from somewhere and it the root directory
to your path.

Then:

```shell
cd ~
mkdir mmrepo
cd mmrepo
# Setup the MMR super repository.
mmr init
# Check out a project with a twisted web of submodule deps.
mmr checkout https://github.com/google/iree.git
# Want to hack on just one of the deps?
mmr checkout https://github.com/google/marl.git
mmr checkout https://github.com/pybind/pybind11.git
mmr checkout https://github.com/llvm/llvm-project.git
```

## What is it doing?

What did this give you? You now should have the following symlinks in your
`~/mmrepo` directory:

* iree
* marl
* pybind11
* llvm-project

Each one has tip-of-tree checkout out.

If you look at the symlinks, you will see that each points into a directory
under `~/mmrepo` like `universe/github.com/llvm/llvm-project.git`. Now if you
`ls -l` in any of the checked out project's submodules, you will see that all
of those symlink back to the tree of actual git repositories under `universe/`.

As part of the checkout process, MMR told git to pretend that each of the
working tree paths that git would usually manage for the submodule don't exist.
The submodule nodes still exist in the index, but without being tied to the
working tree, they are just ignored. MMR puts symlinks to its central checkouts
there instead.

## But what about getting the right versions?

MMR is trying to be a tool that will let you set up the virtual monorepo in
a state where, for any given project, a consistent view of versions is
rational. Since this is not actually a carefully curated and tested monorepo,
the fact is that there will be all kinds of illegal and inconsistent version
states in practice. However, it is designed for a person or CI, which typically
is only focusing on one (or a small number) of graph spans at a time.

Want to sync to the checked in (known good) version graph that IREE has?

```shell
mmr focus iree
```

Want to bump one of the deps to head and trying to build? It's just a git
repo... go for it.

Have the dep graph in a consistent state and want to publish the bumps to
one or more sub-repos:

```shell
# Will stage version bumps for commit corresponding to the versions in each
# dependency.
mmr add_versions iree  # Not implemented yet.
```

Stuck and just want to go back to how it was?

```shell
mmr focus iree --force
```

The precise command line UI is still a work in progress.

There are some other things that will be needed in practice like branch
tracking and pinning to different repos, etc.

Also, it should be obvious, but the structure of the checkouts will make it
really easy to have a light-weight command like:

```shell
mmr dup ~/original_mmr_repo
```

This can get away with just creating an `upstream_universe` symlink and then
making sure to do any git clones with `--reference`, sharing most things. That
way, you can easily end up with multiple, relatively light-weight "views"
that can have different version graphs. This can be useful for various caching
scenarios on build bots.
