aw-watcher-buttons
==================

This extension watches the physical buttons based on an arduino.

![IMG_5582](https://github.com/user-attachments/assets/635bc5f2-810d-42ea-99f2-7793a368d078)

This watcher is currently in a early stage of development, please submit PRs if you find bugs!


## Usage

### Step 1: Install the watcher with uv

Install [uv](https://github.com/astral-sh/uv) if you do not already have it, then from this repository run:

```sh
uv tool install .
```

This makes `aw-watcher-buttons` available on your PATH for all shells. To upgrade later, run `uv tool install --force .`.

### Step 2: First run (generates config)

```sh
aw-watcher-buttons
```

This creates the config file (see the path in the log output). Update the `ports` and `button_names` entries as needed for your setup.

### Step 3: Restart the server and enable the watcher



