# Set up git and repository
- Setup git defaults for dealing with submodule recurssion
  - `git config --global user.email "you@example.com"`
  - `git config --global user.name "Your Name"`
  - `git config --global submodule.recurse true`
  - `git config --global diff.submodule log`
  - `git config --global status.submodulesummary 1`
  - `git config --global push.recurseSubmodules on-demand`
- Clone this repository, `git --recurse-submodules clone git@github.com:mousebrains/SUNRISE2022.git`
