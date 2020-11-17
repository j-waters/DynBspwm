# dynbsp

dynbsp is a companion for [bspwm](https://github.com/baskerville/bspwm) that can
dynamically add, rename and remove desktops, amongst other things

## Installation

### pip

```shell script
pip install dynbsp
```

### Arch

```shell script
yay -S dynbsp-git
```

## Usage

```
Usage: dynbsp [OPTIONS] [COMMAND] [ARGS]...


Options:
  --profile  profile application
  --help     Show this message and exit.

Commands:
  multimonitor      Call when a monitor is removed. Any desktops on the
                    old monitor will be moved to a different one
  new-desktop       Create a new 'misc' desktop
  pip               Toggle a node in and out of 'picture in picture' mode
  start             Start dynbsp (default)
```

## Configuration

```yaml
# ~/.config/dynbsp/config.yaml

# Configure the home desktop. Applications launched on this desktop
# will be moved to their own new 'misc' desktop unless whitelisted
home:
  name: ""
  applications:
    - class: conky
    - class: calculator
# The name of 'misc' desktops
misc: "•"
# A list of desktops, with the applications that should be put on them
# If two desktops have the same name, and extra_name is defined, the desktops
# will be renamed to '{name} {extra_name}'
desktops:
  - name: ""
    order: 220
    applications:
      - class: Chromium
  - name: ""
    extra_name: pycharm
    order: 320
    applications:
      - class: jetbrains-pycharm
  - name: ""
    extra_name: webstorm
    order: 310
    applications:
      - class: jetbrains-webstorm
```

Config will automatically be re-loaded