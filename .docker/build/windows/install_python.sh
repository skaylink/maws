#!/bin/bash

set -e

Xvfb :0 -screen 0 1024x768x16 &

whoami="$(whoami)"

function install_python {
    wget -q -O /builddir/_python.exe \
        https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe
    wget -q -O /builddir/depends22_x86.zip \
        https://www.dependencywalker.com/depends22_x86.zip
    wget -q -O /builddir/gcc.zip \
        https://github.com/brechtsanders/winlibs_mingw/releases/download/14.2.0posix-19.1.1-12.0.0-msvcrt-r2/winlibs-x86_64-posix-seh-gcc-14.2.0-llvm-19.1.1-mingw-w64msvcrt-12.0.0-r2.zip
    mkdir -p /python/prefix/drive_c/users/"${whoami}"/AppData/Local/Nuitka/Nuitka/Cache/downloads/depends/x86_64
    unzip -q /builddir/depends22_x86.zip -d /python/prefix/drive_c/users/"${whoami}"/AppData/Local/Nuitka/Nuitka/Cache/downloads/depends/x86_64

    mkdir -p /python/prefix/drive_c/users/"${whoami}"/AppData/Local/Nuitka/Nuitka/Cache/downloads/gcc/x86_64/14.2.0posix-19.1.1-12.0.0-msvcrt-r2
    unzip -q /builddir/gcc.zip -d /python/prefix/drive_c/users/"${whoami}"/AppData/Local/Nuitka/Nuitka/Cache/downloads/gcc/x86_64/14.2.0posix-19.1.1-12.0.0-msvcrt-r2/

    echo -e "\033[0;32mInstalling Python\033[0m"
    wine cmd /c _python.exe \
        /quiet \
        InstallAllUsers=1 \
        Include_exe=1 \
        Include_lib=1 \
        Include_pip=1 \
        Include_tools=1 \
        PrependPath=1CompileAll=0 \
        AssociateFiles=0 \
        Include_debug=0 \
        Include_launcher=0 \
        InstallLauncherAllUsers=0 \
        Include_symbols=0 \
        Include_tcltk=0 \
        Include_test=0 & \
        while kill -0 $! 2> /dev/null; do sleep 1; done;
    rm -f /builddir/*.{zip,exe}
}

echo -e "\033[0;32mRunning wineboot\033[0m"
wineboot --init & while kill -0 $! 2> /dev/null; do sleep 1; done;

echo -e "\033[0;32mRunning winecfg\033[0m"
winecfg /v win11 & while kill -0 $! 2> /dev/null; do sleep 1; done;

echo -e "\033[0;32mRunning winetricks for win11\033[0m"
winetricks -q --force win11 & while kill -0 $! 2> /dev/null; do sleep 1; done;

install_python

echo -e "\033[38;5;250mChecking python version:\033[0m"
wine cmd /c python --version

echo -e "\033[38;5;250mInstalling nuitka:\033[0m"
# versions 2.8.6+ break, see https://github.com/Nuitka/Nuitka/issues/3679
wine cmd /c pip install nuitka==2.8.6 --break-system-packages
