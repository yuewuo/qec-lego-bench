# How to use `unison` to synchronize a folder

When deploying computing tasks in a remote machine (like HPC cluster), we often need to transfer files between our laptop and the remote server. Naive methods like using `scp` or `git` won't scale when number or size of the files are too large. `unison` is a small tool for synchronizing a folder between two machines with powerful customization of what files/sub-folders to sync, as well as providing a safe way of synchronization to avoid data loss due to accidental overwrite.

The source file of this guide is [here](https://github.com/yuewuo/qec-lego-bench/tree/main/tutorial/src/yale-hpc-how-to-use-unison-for-file-sync.md).

## Installation

To use `unison`, both machines must use the same version of unison. The releases of `unison` can be found [in this link](https://github.com/bcpierce00/unison/releases).

### MacOS

The simplest method to install is via `brew install unison`.

### Linux

With root permission, one could install with `apt install unison` or `yum install unison`, etc. However, for servers that we don't have permission with, we will need to manually install the `unison` binary. One could download the corresponding binary and manually add the subfolder to your path.

```sh
mkdir $HOME/.unison
cd $HOME/.unison
wget https://github.com/bcpierce00/unison/releases/download/v2.53.7/unison-2.53.7-ubuntu-x86_64-static.tar.gz
tar -xzvf unison-2.53.7-ubuntu-x86_64-static.tar.gz
echo "export PATH=\$PATH:$HOME/.unison/bin" >> $HOME/.bashrc
source $HOME/.bashrc
unison -version  # to see if the above commands succeed and check whether the version matches the other machine
```

## Folder setup

To synchronize between two folders, one need to create a unison profile in the `$HOME/.unison` folder.
For example, when synchronizing a Python project, here is a template for the `$HOME/.unison/hpc-qec-lego-bench.prf` of your laptop.

```ini
# Unison preferences
label = qec-lego-bench folder on HPC Grace Yale
root = /Users/wuyue/Documents/GitHub/qec-lego-bench  # the local folder to sync
root = ssh://yw729@grace//home/yw729/project/qec-lego-bench  # the remote folder to sync

ignore = Regex (.*/)?node_modules(/.*)?
ignore = Regex (.*/)?target(/.*)?
ignore = Regex (.*/)?dist(/.*)?
ignore = Regex (.*/)?_build(/.*)?
ignore = Regex (.*/)?\.ipynb_checkpoints(/.*)?
ignore = Regex (.*/)?.*\.egg-info(/.*)?
ignore = Regex (.*/)?.*_cache(/.*)?
ignore = Regex (.*/)?\.tox(/.*)?
ignore = Regex (.*/)?slurm-.*
ignore = Regex (.*/)?slurm_job(/.*)?
ignore = Regex (.*/)?__pycache__(/.*)?
ignore = Name .DS_Store

ignore = Regex .*/slurm_jobs/.*\.jobout
ignore = Regex .*/slurm_jobs/.*\.joberror

# log actions to the terminal
log = true

# more configurations see https://www.cis.upenn.edu/~bcpierce/unison/download/releases/stable/unison-manual.html
```

You might need to change the `root` folders accordingly. For Yale HPC, it is better to create an SSH config, which avoids repeated DUO verification. To add SSH config, create or append the following lines to `$HOME/.ssh/config` of your laptop.

```init
Host grace
  HostName login1.grace.ycrc.yale.edu
  User yw729
  ControlMaster auto
  ControlPath /tmp/%h_%p_%r
  ControlPersist 2h
  UseKeychain yes
  AddKeystoAgent yes
```

The `ControlMaster` parameters follows the guide [in this link](https://docs.ycrc.yale.edu/clusters-at-yale/access/advanced-config/). With these parameters, you only need to do the DUO verification once in a while.

## Usage

For the first time of synchronization, you only need to prepare such a folder in one side of the machine (don't git clone in both machine).

```sh
unison hpc-qec-lego-bench -auto -batch  # this will do the job for most of the time
```

In case there is conflict or unfinished synchronization, you can use the following to manually determine which file to keep

```sh
unison hpc-qec-lego-bench
```

