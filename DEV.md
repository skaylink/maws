# DEV

## Build steps

```bash
podman run --rm -it --arch arm64 --volume $PWD:/host:z --workdir /tmp --tmpfs /tmp:exec fedora:43
dnf -y copr enable jdxcode/mise && dnf -y install mise git
cp -r /host . && cd host
mise trust && mise build:binary
```
