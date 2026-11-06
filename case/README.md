# Thigh holster

A holster for wearing the Temper on your thighs, with a swappable clip that goes into the pocket.
The keyboard's printed case isn't changed, and it lifts straight out for desk use.

This is a first draft. It hasn't been printed yet.

## How it's worn

The right half goes on the right thigh, and the left half on the left. Each half turns 180 degrees
from how it sits on a desk, with the thumbs up and USB towards the knee, so your hanging hand meets
the keys the way it does at a desk. The keys face out.

The clip is a J, like a knife clip. It goes over the pocket edge and runs straight down inside the
pocket, so the seam carries the weight and the keyboard sits flush below the pocket edge. The top of
the J is cut at the pocket edge's angle, so it sits along the edge instead of on one corner.

## Side bumps

Knocks from the side are what's most likely to dislodge it, so these all work against them:

- The tongue runs 80 mm down inside the pocket, on the keyboard's centre line.
- Ribs along the tongue press the fabric into grooves in the holster. They slide in easily, and
  resist sideways slip.
- The clip's plate sits in a recess, so its walls take a sideways load instead of the screws.
- Bumpers on both sides stand just above the keycaps, so a knock lands on the holster.

The holster has no clearance for the optional nice!view screens, so take them off before you wear it.

## Parts

All of these come from `holster.py`, in `out/`, as STEP, STL and 3MF, for each side.

| Part | Print in | Notes |
|---|---|---|
| `test-fit` | Anything | Print this first, flat, with no supports. It's a thin slice with every fit in it |
| `holster` | PETG | Print with the keyboard side up. The back is curved, so use tree supports under all of it. That face sits against your leg, so marks there won't show |
| `clip` | Nylon, or PETG | Print on its long edge, so the layers run along the tongue, with 100% infill. Avoid PLA and carbon-filled filament, which are brittle |
| `clip-steel` | Same as `clip` | The same clip with a channel for a steel spine |

Each clip also needs two M3 x 4 heat-set inserts and two M3 x 6 countersunk screws. The inserts go
into the clip, and the screws go in from the keyboard side, flush with the floor, where the keyboard
covers them.

### Steel spine

`clip-steel` seals in a strip of spring steel 12 to 13 mm wide, up to 0.7 mm thick and 50 mm long. A
piece of hacksaw blade works: wear eye protection when you snap it. Printed on its long edge, the
channel is open from the top until about 20.7 mm up, so add a pause there, drop the strip in, and
resume. Check the layer in your slicer's preview.

The steel keeps the clip springy, as plastic slowly relaxes under load. It also holds the clip
together if the plastic ever cracks.

### Tether

The lug on the holster takes 4 mm paracord. Tie it to a belt loop, so the keyboard can't hit the
ground if the clip ever lets go.

## Trial prints

Cheap filament and low infill are fine for checking fit and comfort, in this order:

1. **`test-fit`:** any filament, 2 walls, 15% infill. Check the keyboard drops in, the peg meets the
   slot, the lips hook on, and the latch clicks.
2. **`holster` and `clip`:** 3 walls, 15% infill. Wear it, and check where it sits, how the rails feel,
   and how it reaches your hands.
3. **The final print:** the proper filament and settings from the table above.

Don't judge the clip's strength from a trial print. PLA is stiff and snaps easily, so it won't last.
If `CLEARANCE` was right in one filament, check it again in another, as they shrink differently.

## Fitting the keyboard

1. Slide the clip over the pocket edge, so the tongue goes down inside the pocket.
2. Hook the USB end under the lips at the bottom of the holster.
3. Rock the keyboard in, so the peg goes into the slot.
4. Press the thumb end until the latch clicks.

The walls and rails are chamfered, so it finds its way in by feel. To take it out, pull the tab on
the latch and lift the thumb end.

## Changing the fit

The settings are at the top of `holster.py`. Rerun it with `uv run case/holster.py`.

| Setting | What it does |
|---|---|
| `CASE_H` | Height of the printed case, measured at 8 mm |
| `CLEARANCE` | Gap around the case. Raise it if the test fit is tight |
| `THIGH_R` | Radius of the curve behind the holster |
| `TILT` | How far the fingers point away from straight down |
| `YAW` | How far the keys turn towards your palm. The front edge stands further off the leg |
| `PITCH` | How far the thumb end stands further off the leg than the USB end |
| `POCKET_ANGLE` | The slope of the pocket edge, where the clip goes over it |
| `TONGUE_DEPTH` | How far the clip reaches below the pocket edge. Keep it shorter than the pocket |
| `BACK_MAX` | The deepest the holster gets behind the keyboard |
| `CLIP_PRELOAD` | How hard the clip grips. The script prints the force, and the strain it puts on the plastic |

`traced-outline.json` is the case outline, traced from a photo, so it's only good to about 2 mm.
