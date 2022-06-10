# Set up git and repository

There is a script with the following in [../Setup/git.setup](../Setup/git.setup) Bit it is a bit of a catch 22

- Setup git defaults for dealing with submodule recurssion
  - `git config --global user.email "you@example.com"`
  - `git config --global user.name "Your Name"`
  - `git config --global submodule.recurse true`
  - `git config --global diff.submodule log`
  - `git config --global status.submodulesummary 1`
  - `git config --global push.recurseSubmodules on-demand`
- Clone this repository, `git clone --recurse-submodules git@github.com:mousebrains/SUNRISE2022.git`
