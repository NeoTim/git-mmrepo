# Magical Monorepo for Git (MMR)

DISCLAIMER: This may be a horrible, horrible, dirty, rotten idea. You have
been warned.

Manage a graph of projects related by submodules as an actual graph.

## What problem is this addressing?

Submodules suck. We all know it. But, in the words of Miracle Max, maybe they
only *mostly suck*. And there is a big difference between *mostly sucks* and
*all the way sucks*.

It turns out, they are ok at managing a distributed graph of dependencies
between projects in a way that is always locally consistent within a single
project.

What they are not so good at is every way you actually manage and use them. In
their natural state, they are also not good for anything but "leaf" projects
because each level of the hierarchy will tend to bring in its own copies of...
everything. Your SSD fills up. Your internet gets capped. And you have N
versions of everything with nothing but primitive tools to manage the graph.

Let's not talk about what happens if you end up with a mutual or recursive
dependency.

A lot of this pushes people to either:

* abandon submodules in favor of either ad-hoc scripting or build system
  dependency managers that treat every source dependency as a black box.
* make bigger and bigger monorepos with more and more walls and higher and
  higher standards of entry in order to slow down the growth of the large
  shared cost.

## What is it doing?

MMR ever so politely tells git to stop being the user-agent for managing
submodules. In order to use it, the primary thing you need to change about
your git workflow is to never invoke any of the "git submodule ..."
commands again.

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
states in practice. However, it is designed for a person, which typically
is only focusing on one (or a small number) of graph spans at a time.

Want to sync to the checked in (known good) version graph that IREE has?

```shell
mmr focus iree  # Not implemented yet
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

I'm still working on the actual UI here, but suffice to say, I'm trying to
make it less of a foot gun than the current tools. Having the git submodule
user-interface out of the way and just operating on the meta-graph allows most
of the historic design flaws to be gotten around.

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
that can have different version graphs.

I'm hoping that this and some build system consistency can help us resolve
more of the diamond LLVM dependencies that are popping up and get a more
sane dev flow.
