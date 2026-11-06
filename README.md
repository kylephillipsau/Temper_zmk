# Kyles Temper

Personal ZMK config for a Temper, a 36-key wireless split keyboard with a nice!nano v2 and a
nice!view screen on each half. It's based on the seller's repo
([Sifan6688/Temper_zmk](https://github.com/Sifan6688/Temper_zmk), kept as the `upstream` remote).

## Keymap

![Temper keymap: Base, NAV_NUM, SYM, ARROWS and SYSTEM layers](keymap_img/temper.svg)

How to read the diagram:

- **Big label:** what the key does when tapped.
- **Small label at the bottom:** what it does when held. On the thumbs that's a layer or a modifier.
- **Blue boxes between keys:** combos. Press the two keys around the box together.
- **Red key:** the thumb key you're holding to reach that layer.
- **Orange keys:** see [Keys to be careful with](#keys-to-be-careful-with).
- **▽:** passes through to the layer underneath. A blank key does nothing.

The diagram is generated from `config/temper.keymap`, so trust it over any notes here if they
ever disagree.

## Reaching the layers

There's no number row, and nothing but the thumbs switches layers. Each layer is only active while
you hold its thumb key. Holding both Space thumbs together opens SYSTEM.

```mermaid
flowchart LR
    base["Base<br/>letters"]
    arrows["ARROWS<br/>↑ ← ↓ →, Backspace"]
    sym["SYM<br/>symbols, Delete,<br/>Bluetooth"]
    num["NAV_NUM<br/>numbers, Backspace"]
    system["SYSTEM<br/>bootloader, clear Bluetooth"]
    base -- "hold left outer thumb" --> arrows
    base -- "hold left inner thumb" --> sym
    base -- "hold right inner thumb" --> num
    sym -- "also hold right inner thumb" --> system
    num -- "also hold left inner thumb" --> system
```

| Thumb key | Tap | Hold |
|---|---|---|
| Left outer | Backspace | ARROWS layer |
| Left middle | Cmd | Cmd |
| Left inner | Space | SYM layer |
| Right inner | Space | NAV_NUM layer |
| Right middle | Enter | Ctrl |
| Right outer | Shift | Shift |

### Common keys

| To type | Press |
|---|---|
| Backspace | Tap the left outer thumb, or hold it and press P (holding P repeats) |
| Numbers 1–0 | Hold the right inner thumb, then the top row (Q is 1, P is 0) |
| Symbols `!@#$%^&*()` | Hold the left inner thumb, then the top row |
| `[` `]` `` ` `` `\` `'` | Hold the left inner thumb, then H, J, K, L, ; |
| `{` `}` `~` `\|` `"` | Hold the left inner thumb, then N, M, comma, full stop, / |
| Cmd shortcuts | Hold the left middle thumb, then the letter |
| Ctrl shortcuts | Hold the right middle thumb, then the letter |
| Delete | Hold the left inner thumb, then D |
| Arrows | Hold the left outer thumb, then W (up), Q (left), S (down), D (right) |

### Combos

| Keys | Sends |
|---|---|
| W + E | Esc |
| X + C | Tab |
| S + D | Caps Lock |
| U + I | Enter |
| I + O | Backspace |
| O + P | Backspace |
| J + K | `-` |
| K + L | `=` |

Combos work on every layer. The diagram only shows them on Base to keep the other layers readable.

U + I, I + O and X + C have a 30 ms window, so those keys need to land almost exactly together.
The others have ZMK's default window.

### Timing

If you hold a layer thumb within 180 ms of tapping it, you get the tap repeating instead of the
layer. That's useful for repeating Backspace, but after a Space, pause briefly before holding the
same thumb for numbers.

## Keys to be careful with

The first three are on the SYSTEM layer, so they need both Space thumbs held and can't be hit by
accident while typing:

| Keys | What it does |
|---|---|
| Both Space thumbs + G | Clears **all** Bluetooth pairings. Every device has to be paired again. |
| Both Space thumbs + B | Puts the left half into its bootloader. It stops typing and mounts as a `NICENANO` drive. |
| Both Space thumbs + N | Puts the right half into its bootloader. |
| Left inner thumb + Z, X, C, V | Switch to Bluetooth profiles 3, 2, 1 and 0. A device on another profile disconnects. |

## Known gaps

These are still missing, and they're the next things to sort out:

- **Modifiers:** there's no Option key and no left Shift.
- **Navigation:** no Home, End, Page Up or Page Down, despite the NAV_NUM name.
- **Sleep:** neither half ever goes to sleep, so the batteries run down faster if the switches are
  left on. The seller's `CONFIG_ZMK_SLEEP=y` is in `boards/shields/temper/temper.conf`, which the
  build doesn't read. Moving it to `config/temper.conf` turns it on.

## What's different from upstream

- **Left outer thumb:** taps Backspace rather than the Non-US Backslash key, which isn't much use
  on a Mac.
- **Cmd and Ctrl:** the left middle thumb is a plain Cmd key, so shortcuts like Cmd+C work. The
  seller's key could only tap Cmd and sent Ctrl when held, so Ctrl moved to holding the right middle
  thumb.
- **Space:** both inner thumbs are Space. The seller's left Space was on the middle thumb.
- **Punctuation:** the right side of the SYM layer has the brackets, quotes, backslash, pipe,
  backtick and tilde, which the seller's keymap left out. The bottom row is the home row shifted.
- **Backspace on P:** hold the left outer thumb and press P.
- **Layer name:** the fourth layer is called ARROWS.
- **SYSTEM layer:** the bootloader and Clear Bluetooth keys moved here from SYM, where rolling off
  Space could hit them. The right half also gets a bootloader key, which it never had.
- **Diagram:** drawn from `config/temper.keymap` with the Temper's layout from `config/temper.json`.
  The seller's workflow drew `boards/shields/temper/temper.keymap`, which the firmware doesn't use.
- **Local tooling:** `build.sh` and `flash.sh`.

## Building and flashing

`build.sh` builds in Docker, with the west workspace in the `zmk-temper-ws` volume. Firmware goes
to `firmware/`, which git ignores.

```sh
./build.sh          # both halves
./build.sh left     # one target: left, right or reset
./build.sh update   # re-run west update after editing config/west.yml
```

`flash.sh` waits for the half's bootloader drive, so start it, then plug that half in and hold both
Space thumbs and press B for left or N for right. The right half has to be connected to the left
for its key to work.

```sh
./flash.sh left
./flash.sh right
```

Both halves mount as `NICENANO`. After each half's first flash, the script remembers its USB serial
and refuses to flash one half's firmware onto the other, so take extra care the first time.

```mermaid
flowchart LR
    keymap["Changed config/temper.keymap"] --> left["./build.sh left<br/>./flash.sh left"]
    other["Changed a .conf, config/west.yml<br/>or anything in boards/"] --> both["./build.sh<br/>./flash.sh left<br/>./flash.sh right"]
```

The left half runs the keymap, so keymap changes only need the left half flashed. The exception is
the first flash: do both halves, so they aren't running different firmware. If they don't reconnect
afterwards, run `./build.sh reset`, copy `firmware/temper_reset.uf2` onto each half's `NICENANO`
drive by hand, then flash left and right again. A reset clears that half's Bluetooth pairings.

Pushing to GitHub also builds the firmware in Actions, if they're enabled on the repo.

## Redrawing the diagram

`.github/workflows/doc.yml` redraws it when the keymap changes on GitHub and commits the result, so
run `git pull --rebase` before pushing again. To redraw locally:

```sh
uvx --from keymap-drawer keymap -c keymap_img/keymap_drawer.config.yaml parse -c 10 -z config/temper.keymap > keymap_img/temper.yaml
uvx --from keymap-drawer keymap -c keymap_img/keymap_drawer.config.yaml draw keymap_img/temper.yaml -j config/temper.json > keymap_img/temper.svg
```

## Troubleshooting

- **The bootloader keys don't work:** this keyboard has no reset button. The original Temper design
  has one, but it isn't fitted here. Use tweezers to briefly bridge the `RST` and `GND` pins on the
  controller twice, quickly, with USB connected. Check the labels first, because bridging `GND` and
  the battery pin next to it is a short circuit.
- **A half looks dead on battery but works on USB:** it needs charging. USB powers it either way,
  so leave it plugged in with the switch on for an hour or so.
