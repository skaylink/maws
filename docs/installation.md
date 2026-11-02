# Installation

## Linux binary

Download the [latest release binaries](https://github.com/skaylink/maws/releases/latest).

```bash
sudo curl -Lo /usr/local/bin/maws https://github.com/skaylink/maws/releases/download/latest/maws_$(arch)
sudo chmod +x /usr/local/bin/maws
maws --help
```

## Windows EXE

Download `maws.exe` from the [latest release](https://github.com/skaylink/maws/releases/latest) and place it in a
directory that is on your `PATH`.

## pip

```bash
pip install maws
```

## Shell completion

`maws` ships with shell completion for bash, zsh, fish and PowerShell.

```bash
# install completion for the current shell
maws --install-completion

# or just print the completion script to customize it
maws --show-completion
```

Restart your shell afterwards.
