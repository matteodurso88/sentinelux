#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y \
  python3 \
  python3-gi \
  python3-psutil \
  gir1.2-gtk-3.0 \
  gir1.2-ayatanaappindicator3-0.1 \
  gir1.2-notify-0.7 \
  libnotify-bin \
  xdg-utils
