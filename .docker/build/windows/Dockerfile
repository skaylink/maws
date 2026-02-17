# https://github.com/Nuitka/Nuitka/issues/43#issuecomment-2100416081

FROM archlinux/archlinux:latest

SHELL ["/bin/bash", "-c"]

RUN <<EOI
tee -a /etc/pacman.conf <<EOF

[multilib]
Include = /etc/pacman.d/mirrorlist
EOF
mkdir /builddir /python
useradd -m -G wheel -s /bin/bash builder
chown builder:builder /builddir
chown builder:builder /python
EOI

RUN <<EOF
pacman -Sy
pacman --quiet -S --noconfirm python wine winetricks wine-mono wine-gecko wget xorg-server-xvfb coreutils which lib32-gnutls libwbclient samba
EOF

USER builder
WORKDIR /builddir

ENV DISPLAY=:0.0
ENV WINEPATH=/python
ENV WINEARCH=win64
ENV WINEPREFIX=/python/prefix
ENV WINEDEBUG=trace-all,warn-all,err+all,fixme-all

COPY install_python.sh /install_python.sh
RUN /install_python.sh
