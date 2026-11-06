#!/usr/bin/env bash
# Flash one half: ./flash.sh left|right, then double-press that half's reset button.
#
# Both halves' bootloaders mount as NICENANO, so this tells them apart by USB serial number, kept
# in ~/.cache/temper-flash/<half>-serial after each half's first flash, and refuses to put one
# half's firmware on the other.
set -euo pipefail
half="${1:?usage: ./flash.sh left|right}"
case "$half" in left) other=right ;; right) other=left ;; *) echo "usage: ./flash.sh left|right"; exit 2 ;; esac
uf2="$(cd "$(dirname "$0")" && pwd)/firmware/temper_$half.uf2"
[ -f "$uf2" ] || { echo "no firmware at $uf2: run ./build.sh $half first"; exit 1; }
known="$HOME/.cache/temper-flash"
mkdir -p "$known"

echo "waiting for the $half half's bootloader drive (double-press its reset button)"
until [ -d /Volumes/NICENANO ]; do sleep 1; done
sleep 1
serial=$(ioreg -p IOUSB -l -w0 | python3 -c '
import re, sys
for block in re.split(r"\+-o ", sys.stdin.read()):  # one block per USB device
    if "Nice Keyboards" in block:
        m = re.search(r"\"USB Serial Number\" = \"([^\"]+)\"", block)
        if m:
            print(m.group(1))
            break
')
echo "bootloader drive, USB serial ${serial:-unknown}"
if [ -n "$serial" ] && [ "$serial" = "$(cat "$known/$other-serial" 2>/dev/null)" ]; then
  echo "that's the $other half: not flashing"
  exit 1
fi

# cp ends with a harmless "Device not configured" when the drive resets mid-copy
cp "$uf2" /Volumes/NICENANO/ 2>/dev/null || true
for _ in $(seq 1 90); do [ -d /Volumes/NICENANO ] || break; sleep 1; done
echo "flashed $half"
if [ -n "$serial" ]; then echo "$serial" > "$known/$half-serial"; fi
