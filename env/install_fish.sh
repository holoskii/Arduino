#!/bin/bash

THIS_DIR=$(cd "$(dirname "$0")"; pwd)

set -x
set +e

sudo apt install fish curl fonts-powerline
set -e
curl --insecure -L https://get.oh-my.fish > /tmp/install
echo "bb1f4025934600ea6feef2ec11660e17e2b6449c5a23c033860aed712ad328c9 /tmp/install"
fish /tmp/install --path=~/.local/share/omf --config=~/.config/omf --noninteractive --yes
rm /tmp/install
fish -c "omf install bobthefish"
mkdir -p ~/.config/fish/
set +x

echo "To make fish your default shell, issue: chsh -s /usr/bin/fish"
echo "To restore your default shell: chsh -s /bin/bash"

fish $THIS_DIR/install_fish.fish $1
