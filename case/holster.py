#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = ["cadquery", "shapely"]
# ///
"""A thigh holster for the Temper, with a swappable pocket clip.

The keyboard's own printed case stays as it is. Its USB end hooks under lips at the bottom of the
holster, it rocks in over a peg that fits the case's oblong slot, and a latch clicks over the thumb
edge. A J-shaped clip bolts on behind, goes over the pocket edge and points straight down the leg.

Modelled as the right half, flat on a desk: X to the right, Y up the desk, Z towards the keycaps.
Worn, the whole thing turns 180 degrees, so the thumbs point up and USB points at the knee.

    uv run case/holster.py        # writes STEP, STL and 3MF to case/out, and prints the checks
"""
import json
import math
from pathlib import Path

import cadquery as cq
from shapely import affinity
from shapely.geometry import LineString, Point, Polygon, box

HERE = Path(__file__).parent
OUT = HERE / "out"

# Measured
KEYTOP_H = 17.0  # desk to the top of the keycaps
CASE_H = 8.0  # desk to the top edge of the printed case
# Guessed
THIGH_R = 130.0  # flatter than a real thigh, as the leg gives a little
TILT = 20.0  # degrees the fingers point away from straight down, from the worn photo
YAW = 6.0  # degrees the keys turn towards the palm: the front edge stands further off the leg
PITCH = 0.0  # degrees the thumb end stands further off the leg than the USB end
POCKET_ANGLE = 35.0  # degrees the pocket edge drops towards the back of the leg, where the clip sits
# Fit
CLEARANCE = 0.4  # gap around the case
WALL = 2.4
BACK_MIN = 6.5  # thinnest the holster gets behind the keyboard, where the clip sits
BACK_MAX = 22.0  # deepest it gets: a real thigh falls away from the corners sooner than this curve
LIP = 1.6  # how far the lips reach over the case
LIP_T = 1.6
# Openings, from the inner edge of the case
USB_X, USB_W = 12.1, 16.0
SWITCH_Y, SWITCH_LEN = 38.0, 16.0
# Latch on the thumb edge: a stretch of wall, fixed at one end and free at the other
LATCH_X = (32.0, 60.0)
LATCH_SLIT = 1.2
# Clip: a J that goes over the pocket edge and runs straight down the leg, inside the pocket
CLIP_W = 28.0
TONGUE_DEPTH = 80.0  # how far the tip reaches below the pocket edge
CLIP_ABOVE = 2.0  # how far the pocket edge sits above the top of the holster
CLIP_MOUTH = 2.4  # gap at the top of the J, for thick seams
TONGUE_T = (3.4, 5.2)  # thickness at the tip and at the top, so the stress is spread along it
CLIP_PRELOAD = 3.0  # mm the tip is bent into the holster when printed
BRIDGE_T = 4.5  # thickness over the top of the J
PLATE_T = 4.0  # the plate sits flush in a recess, whose walls take sideways bumps
RIB_OFFSET, RIB_H, RIB_W = 8.0, 0.9, 2.2  # ribs along the tongue resist sideways slip, not insertion
BARB_FROM_TIP = 14.0  # one rib across the tongue resists being pulled out
BOLT_BELOW_TOP, BOLT_SPREAD = 27.0, 9.5  # from the top of the holster
BOLT_D, CSK_D, CSK_H = 3.4, 6.4, 1.8  # M3 countersunk
INSERT_D, INSERT_DEPTH = 4.0, 3.4  # M3 x 4 heat-set insert in the clip
# Bumpers on both sides, standing just above the keycaps
RAIL_ABOVE_KEYS = 0.5
# A strip of hacksaw blade sealed inside the tongue, in the clip-steel version
SPINE_W, SPINE_T = 13.4, 0.9
SPINE_FROM_TOP, SPINE_FROM_TIP = 24.0, 16.0
# Lug for a tether to a belt loop
LUG = (97.0, 12.0)
LUG_HOLE = 5.0


def prism(poly, z0, z1):
    points = list(poly.exterior.coords)[:-1]
    return cq.Workplane("XY").workplane(offset=z0).polyline(points).close().extrude(z1 - z0)


def block(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def load_case():
    data = json.loads((HERE / "traced-outline.json").read_text())["right"]
    height = data["height"]
    case = Polygon([(x, height - y) for x, y in data["outline_mm"]]).buffer(0).simplify(0.25)
    (sx, sy), (sw, sh) = data["slot_at"][0], data["slot_mm"][0]
    return case, height, (sx + sw / 2, height - sy - sh / 2), (sw, sh)


class Holster:
    def __init__(self):
        self.case, self.height, self.slot, self.slot_size = load_case()
        self.inner = self.case.buffer(CLEARANCE, join_style=2).simplify(0.1)
        self.outer = self.case.buffer(CLEARANCE + WALL, join_style=1, quad_segs=4).simplify(0.1)
        x0, _, x1, _ = self.outer.bounds
        tilt, pitch = math.radians(TILT), math.radians(PITCH)
        self.across = cq.Vector(math.cos(tilt), -math.sin(tilt), 0)  # towards the back of the leg
        self.axis = cq.Vector(math.sin(tilt) * math.cos(pitch), math.cos(tilt) * math.cos(pitch), math.sin(pitch))  # down it
        self.radial = self.across.cross(self.axis)
        # Turning the keys towards the palm is the same as moving the leg's crown towards the back
        shift = THIGH_R * math.sin(math.radians(YAW))
        self.clip_w = -shift
        self.leg_x = (x0 + x1) / 2 + shift * self.across.x
        self.leg_y = self.height / 2 + shift * self.across.y
        self.leg_z = -BACK_MIN - THIGH_R / self.radial.z
        self.origin = cq.Vector(self.leg_x, self.leg_y, self.leg_z)
        points = list(self.outer.exterior.coords)
        self.back = min(-min(self.surface_z(x, y, THIGH_R) for x, y in points) + 2, BACK_MAX)

        # Where the clip's centre line leaves the top of the holster
        start, end = self.at(0, self.clip_w), self.at(-300, self.clip_w)
        reach = LineString([start, end]).intersection(self.outer.exterior)
        edge = min(getattr(reach, "geoms", [reach]), key=lambda p: p.y)
        self.top = -math.hypot(edge.x - start[0], edge.y - start[1])
        self.edge_s = self.top - CLIP_ABOVE  # the pocket edge, at the clip's centre line
        self.slant = math.tan(math.radians(POCKET_ANGLE))
        self.clip_top = self.edge_s - CLIP_W / 2 * self.slant  # the J's highest point, at the front
        self.clip_tip = self.edge_s + TONGUE_DEPTH
        self.length = self.clip_tip - self.clip_top
        self.bolt_s = self.top + BOLT_BELOW_TOP
        self.plate_len = self.bolt_s + 8 - self.clip_top

    def at(self, s, w=0.0):
        """A point on the holster: s down the leg from its middle, and w across it."""
        return (
            self.leg_x + s * self.axis.x + w * self.across.x,
            self.leg_y + s * self.axis.y + w * self.across.y,
        )

    def surface_z(self, x, y, radius):
        """Height of a cylinder around the leg, at x, y."""
        dx, dy = x - self.leg_x, y - self.leg_y
        w = dx * self.across.x + dy * self.across.y
        along = math.sqrt(radius**2 - w**2)
        return self.leg_z + (along - dx * self.radial.x - dy * self.radial.y) / self.radial.z

    def leg(self, radius):
        """A cylinder along the thigh."""
        start = self.origin - self.axis * 300
        return cq.Workplane(obj=cq.Solid.makeCylinder(radius, 600, start, self.axis))

    def edge_y(self, x):
        """The bottom of the pocket at x, for placing the latch."""
        return self.inner.intersection(box(x - 0.1, -50, x + 0.1, 200)).bounds[1]

    def body(self):
        x, y = LUG
        lug = box(x - 7, y - 5, x + 7, y + 11).buffer(2.5)
        body = prism(self.outer, -self.back, CASE_H - 1).union(prism(lug, -self.back, -1.5))
        body = body.cut(prism(self.inner, 0, CASE_H + 5))
        body = body.cut(self.leg(THIGH_R))

        # Soften the edges against the leg, in steps small enough to feel round
        for reach in (0.9, 1.8, 2.7):
            inside = self.outer.buffer(-reach)
            inside = max(getattr(inside, "geoms", [inside]), key=lambda g: g.area)
            edge = prism(self.outer, -80, 0).cut(prism(inside, -81, 1))
            body = body.cut(edge.intersect(self.leg(THIGH_R + 3.6 - reach)))
            body = body.cut(edge.intersect(block(-50, 200, -50, 200, -self.back - 1, -self.back + 3.6 - reach)))

        # Lips over the +Y edges, which the USB end hooks under
        zone = box(-20, self.height * 0.6, 200, 200)
        shifted = affinity.translate(self.inner, 0, -LIP)
        wall = self.outer.difference(self.inner).intersection(zone)
        lip = self.outer.difference(shifted).intersection(zone)
        for poly, z0, z1 in ((wall, CASE_H - 1, CASE_H + 0.2), (lip, CASE_H + 0.2, CASE_H + 0.2 + LIP_T)):
            for part in getattr(poly, "geoms", [poly]):
                if part.area > 1:
                    body = body.union(prism(part, z0, z1))

        # Peg for the oblong slot
        sx, sy = self.slot
        peg = (
            block(sx - 5.8, sx + 5.8, sy - 2.3, sy + 2.3, -1, CASE_H * 0.8)
            .faces(">Z").edges().chamfer(1.2)
        )
        body = body.union(peg)

        # Bumpers down both sides, to take a knock before the keycaps do
        ring = self.outer.difference(self.inner)
        x0, _, x1, _ = self.outer.bounds
        for zone in (box(x0 - 1, 16, x0 + 4.5, self.height + 5), box(x1 - 4.5, 0, x1 + 1, self.height + 5)):
            rail = ring.intersection(zone)
            for part in getattr(rail, "geoms", [rail]):
                if part.area > 8:
                    body = body.union(prism(part, CASE_H - 1.5, KEYTOP_H + RAIL_ABOVE_KEYS))

        # Lead-ins, so the keyboard finds its way in by feel
        zone = box(-20, self.height * 0.6, 200, 200)
        for grow, z0, z1 in ((0.5, CASE_H - 2, CASE_H - 1.3), (1.0, CASE_H - 1.3, CASE_H - 1)):
            body = body.cut(prism(self.inner.buffer(grow).difference(zone), z0, z1 + 0.01))
        for grow, z0, z1 in ((0.6, KEYTOP_H - 2.2, KEYTOP_H - 1.1), (1.2, KEYTOP_H - 1.1, KEYTOP_H + 2)):
            body = body.cut(prism(self.inner.buffer(grow), z0, z1))

        # USB and the power switch
        body = body.cut(block(USB_X - USB_W / 2, USB_X + USB_W / 2, self.height - 12, self.height + 10, 0, 40))
        body = body.cut(block(-10, 6, SWITCH_Y - SWITCH_LEN / 2, SWITCH_Y + SWITCH_LEN / 2, 0.5, 40))

        body = self.add_latch(body)
        # Drop any specks the cuts left behind
        body = cq.Workplane(obj=max(solid(body).Solids(), key=lambda s: s.Volume()))

        # A recess for the clip's plate. Its walls take sideways bumps, not the screws
        plate_end = self.clip_top + self.plate_len + 0.3
        body = body.cut(self.band([(THIGH_R - 2, self.clip_top - 30), (THIGH_R - 2, plate_end),
                                   (THIGH_R + PLATE_T, plate_end), (THIGH_R + PLATE_T, self.clip_top - 30)], CLIP_W + 0.6))

        # Grooves the ribs press the fabric into, so the fabric can't slide sideways
        for w in (-RIB_OFFSET, RIB_OFFSET):
            groove = [(THIGH_R - 2, plate_end - 0.3), (THIGH_R - 2, self.clip_tip), (THIGH_R + 1.5, self.clip_tip), (THIGH_R + 1.5, plate_end - 0.3)]
            body = body.cut(self.band(groove, RIB_W + 1.6, w))
        barb = self.clip_tip - BARB_FROM_TIP
        body = body.cut(self.band([(THIGH_R - 2, barb - 3), (THIGH_R - 2, barb + 3), (THIGH_R + 1.5, barb + 3), (THIGH_R + 1.5, barb - 3)], CLIP_W + 1))

        # The tether hole
        lx, ly = LUG
        body = body.cut(cq.Workplane("XY").workplane(offset=-40).center(lx, ly).circle(LUG_HOLE / 2).extrude(45))

        # Countersunk bolts for the clip, flush with the floor under the keyboard
        for x, y in self.bolts():
            assert self.inner.buffer(-CSK_D / 2).contains(Point(x, y)), f"bolt at {x:.1f}, {y:.1f} is off the floor"
            body = body.cut(cq.Workplane("XY").workplane(offset=-30).center(x, y).circle(BOLT_D / 2).extrude(31))
            cone = cq.Solid.makeCone(BOLT_D / 2, CSK_D / 2, CSK_H, cq.Vector(x, y, -CSK_H), cq.Vector(0, 0, 1))
            floor = -self.surface_z(x, y, THIGH_R + PLATE_T)
            assert floor > CSK_H + 0.4, f"only {floor:.1f} mm of floor over the plate"
            body = body.cut(cq.Workplane(obj=cone))
        return body

    def add_latch(self, body):
        """A stretch of wall on the thumb edge, sprung from one end. Pull it back to release."""
        x0, x1 = LATCH_X
        zone = box(x0, -50, x1, self.height * 0.4)
        arm = self.outer.difference(self.inner).intersection(zone)
        arm = max(getattr(arm, "geoms", [arm]), key=lambda g: g.area)
        # Clear the wall, and leave a slit under it and at its free end
        clear = arm.buffer(0.01)
        body = body.cut(prism(clear, 0, 40))
        body = body.cut(block(x0 - LATCH_SLIT, x0, -50, self.height * 0.4, 0, 40).intersect(prism(self.outer, 0, 40)))
        top = CASE_H + 3
        body = body.union(prism(arm, 0.8, top))
        # Join the fixed end back into the wall
        anchor = self.outer.difference(self.inner).intersection(box(x1 - 3, -50, x1 + 3, self.height * 0.4))
        anchor = max(getattr(anchor, "geoms", [anchor]), key=lambda g: g.area)
        body = body.union(prism(anchor, -0.5, CASE_H - 1))
        # The catch, stepped back layer by layer so the case rides over it
        steps = 5
        for i in range(steps):
            reach = LIP * (1 - i / steps)
            catch = self.outer.difference(affinity.translate(self.inner, 0, reach)).intersection(zone)
            catch = max(getattr(catch, "geoms", [catch]), key=lambda g: g.area)
            body = body.union(prism(catch, CASE_H + 0.2 + i * 0.5, CASE_H + 0.2 + (i + 1) * 0.5))
        # A tab to pull, near the free end where the arm moves most
        edge = self.edge_y(x0 + 8) - WALL - CLEARANCE
        tab = box(x0 + 2, edge - 8, x0 + 14, edge + 1.5).buffer(1.5)
        return body.union(prism(tab, CASE_H + 0.4, top))

    def bolts(self):
        return self.at(self.bolt_s, self.clip_w - BOLT_SPREAD), self.at(self.bolt_s, self.clip_w + BOLT_SPREAD)

    def band(self, chain, width, offset=0.0):
        """Sweep a (radius, s) outline around the leg, so it follows the curve across its width."""
        radius = THIGH_R
        angle = width / radius
        start = (self.clip_w + offset) / radius - angle / 2
        x_dir = self.radial * math.cos(start) + self.across * math.sin(start)
        plane = cq.Plane(
            origin=self.origin.toTuple(),
            xDir=x_dir.toTuple(),
            normal=x_dir.cross(self.axis).toTuple(),
        )
        return cq.Workplane(plane).polyline(chain).close().revolve(math.degrees(angle), (0, 0, 0), (0, 1, 0))

    def along(self, s):
        """How far along the tongue s is, from 0 at the top to 1 at the tip."""
        return min(max((s - self.clip_top) / self.length, 0.0), 1.0)

    def thickness(self, s):
        tip, top = TONGUE_T
        q = self.along(s)
        return top + (tip - top) * q + 2.0 * math.exp(-(s - self.clip_top) / 5)  # thicker where it leaves the J

    def centre_line(self, s):
        """The tongue's holster side, without the barb. It leans in, then flares back at the tip."""
        q = self.along(s)
        face = THIGH_R - CLIP_MOUTH + (CLIP_MOUTH + CLIP_PRELOAD) * q**2
        flare_from = self.clip_tip - 12
        if s > flare_from:
            face -= 2.6 * ((s - flare_from) / 12) ** 2
        return face

    def clip(self, steel=False):
        top, tip = self.clip_top, self.clip_tip
        steps = [top + i * (tip - top) / 164 for i in range(165)]
        barb = tip - BARB_FROM_TIP
        rib = lambda s: RIB_H * math.exp(-(((s - barb) / 1.6) ** 2))
        plate_r = THIGH_R + PLATE_T - 0.15
        mouth = CLIP_MOUTH / 2
        chain = [(self.centre_line(s) + rib(s), s) for s in reversed(steps)]
        # Around the inside of the J, where the seam sits
        chain += [(THIGH_R - mouth - mouth * math.cos(a), top - mouth * math.sin(a))
                  for a in (math.pi * i / 12 for i in range(1, 13))]
        # Down the plate and back up its far side
        chain += [(THIGH_R, top + self.plate_len), (plate_r, top + self.plate_len)]
        # Over the top of the J
        back = self.centre_line(top) - self.thickness(top)
        crown = (plate_r - back) / 2
        crown_r, crown_s = (plate_r + back) / 2, top - mouth - BRIDGE_T + crown
        chain += [(crown_r + crown * math.cos(a), crown_s - crown * math.sin(a))
                  for a in (math.pi * i / 16 for i in range(17))]
        # Down the leg side of the tongue
        chain += [(self.centre_line(s) - self.thickness(s), s) for s in steps if s > crown_s + 0.5]
        clip = self.band(chain, CLIP_W)

        # Rounded in plan, as a square corner is where a crack or a snag starts
        corners = box(top - 20, -CLIP_W / 2 + 7, tip - 7, CLIP_W / 2 - 7).buffer(7, quad_segs=10)
        plan = Polygon([self.at(s, w + self.clip_w) for s, w in corners.exterior.coords])
        clip = clip.intersect(prism(plan.buffer(0), -80, 40))

        # Fill the top of the J down to a slant, so it sits along the pocket edge instead of on a corner
        half = CLIP_W / 2
        deep = top + CLIP_W * self.slant
        slant = Polygon([self.at(top - 3, self.clip_w - half), self.at(top - 3, self.clip_w + half), self.at(deep, self.clip_w + half), self.at(top, self.clip_w - half)])
        web = [(THIGH_R + 0.2, top - 3), (THIGH_R + 0.2, deep + 2), (THIGH_R - CLIP_MOUTH - 0.8, deep + 2), (THIGH_R - CLIP_MOUTH - 0.8, top - 3)]
        clip = clip.union(self.band(web, CLIP_W).intersect(prism(slant.buffer(0), -80, 40)))

        # Ribs along the tongue
        first = top + self.plate_len + 2
        ribs = [s for s in steps if first <= s <= barb - 3]
        for w in (-RIB_OFFSET, RIB_OFFSET):
            strip = [(self.centre_line(s) + RIB_H, s) for s in ribs] + [(self.centre_line(s) - 0.8, s) for s in reversed(ribs)]
            clip = clip.union(self.band(strip, RIB_W, w))

        if steel:
            clip = clip.cut(self.spine(SPINE_T, SPINE_W))

        for x, y in self.bolts():
            face = self.surface_z(x, y, THIGH_R + PLATE_T)
            hole = cq.Workplane("XY").workplane(offset=face - INSERT_DEPTH).center(x, y).circle(INSERT_D / 2).extrude(INSERT_DEPTH + 3)
            clip = clip.cut(hole)
        return clip

    def spine_radius(self, s):
        return self.centre_line(min(s, self.clip_tip - 12)) - self.thickness(s) / 2

    def spine(self, thick=0.65, width=12.7):
        """The steel strip, or the channel for it. It's sealed in, so the print pauses to add it."""
        a, b = self.clip_top + SPINE_FROM_TOP, self.clip_tip - SPINE_FROM_TIP
        steps = [a + i * (b - a) / 80 for i in range(81)]
        return self.band([(self.spine_radius(s) + thick / 2, s) for s in steps]
                         + [(self.spine_radius(s) - thick / 2, s) for s in reversed(steps)], width)

    def spine_walls(self):
        """The thinnest plastic either side of the steel strip."""
        thinnest = 99.0
        for i in range(81):
            s = self.clip_top + SPINE_FROM_TOP + i * (self.length - SPINE_FROM_TOP - SPINE_FROM_TIP) / 80
            face, back = self.centre_line(s), self.centre_line(s) - self.thickness(s)
            r = self.spine_radius(s)
            thinnest = min(thinnest, face - r - SPINE_T / 2, r - SPINE_T / 2 - back)
        return thinnest

    def screws(self):
        out = None
        for x, y in self.bolts():
            head = cq.Workplane(obj=cq.Solid.makeCone(1.45, CSK_D / 2 - 0.2, CSK_H, cq.Vector(x, y, -CSK_H), cq.Vector(0, 0, 1)))
            screw = head.union(cq.Workplane("XY").workplane(offset=-6.0).center(x, y).circle(1.45).extrude(6.0 - CSK_H + 0.1))
            out = screw if out is None else out.add(screw)
        return out

    def spring_check(self, modulus=2000.0):
        """Treats the tongue as a tapered cantilever, closed over thin fabric. Returns N and strain."""
        deflection = CLIP_PRELOAD + 1.0
        length = self.length
        steps = 400
        flex = 0.0
        for i in range(steps):
            d = (i + 0.5) / steps * length  # distance from the tip
            t = self.thickness(self.clip_tip - d)
            flex += d**2 / (modulus * CLIP_W * t**3 / 12) * (length / steps)
        force = deflection / flex
        strain = 0.0
        for i in range(1, 51):
            d = length * i / 50
            t = self.thickness(self.clip_tip - d)
            strain = max(strain, force * d * (t / 2) / (modulus * CLIP_W * t**3 / 12))
        return force, strain

    def test_fit(self, body):
        """A thin slice with every fit in it: walls, lips, peg and latch. Print this first."""
        keep = prism(self.outer.buffer(6), -2.0, 40)
        window = prism(self.inner.buffer(-9), -3, -0.0)
        sx, sy = self.slot
        return body.intersect(keep).cut(window.cut(block(sx - 9, sx + 9, sy - 6, sy + 6, -3, 0)))

    def keyboard(self):
        """A stand-in for the keyboard, for checking fits."""
        sx, sy = self.slot
        sw, sh = self.slot_size
        return prism(self.case, 0, CASE_H).cut(block(sx - sw / 2, sx + sw / 2, sy - sh / 2, sy + sh / 2, -1, 40))


def solid(work):
    return work.val() if len(work.vals()) == 1 else cq.Compound.makeCompound(work.vals())


def report(name, work):
    shape = solid(work)
    bb = shape.BoundingBox()
    grams = shape.Volume() / 1000 * 1.27
    print(f"{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, {shape.Volume() / 1000:.1f} cm3 "
          f"(about {grams:.0f} g solid), valid={shape.isValid()}, solids={len(shape.Solids())}")


def overlap(a, b):
    try:
        return solid(a.intersect(b)).Volume()
    except Exception:
        return 0.0


def export(work, name):
    OUT.mkdir(exist_ok=True)
    for ext in ("step", "stl", "3mf"):
        cq.exporters.export(work, str(OUT / f"{name}.{ext}"), tolerance=0.05, angularTolerance=0.2)


def describe(name, work):
    for s in solid(work).Solids():
        c, bb = s.Center(), s.BoundingBox()
        print(f"  {name} piece: {s.Volume():.1f} mm3 at ({c.x:.0f}, {c.y:.0f}, {c.z:.0f}), "
              f"x {bb.xmin:.0f}..{bb.xmax:.0f} y {bb.ymin:.0f}..{bb.ymax:.0f} z {bb.zmin:.0f}..{bb.zmax:.0f}")


def main():
    h = Holster()
    print(f"back of the holster: {BACK_MIN:.1f} mm at its thinnest, {h.back:.1f} mm at its deepest")
    print(f"clip: {h.length:.0f} mm from the top of the J to the tip, {TONGUE_DEPTH:.0f} mm below the pocket edge")
    body, clip, keyboard = h.body(), h.clip(), h.keyboard()
    steel = h.clip(steel=True)
    fit = h.test_fit(body)
    report("holster", body)
    report("clip", clip)
    report("clip-steel", steel)
    print(f"thinnest wall beside the steel strip: {h.spine_walls():.2f} mm")
    for material, modulus in (("PETG", 2000.0), ("nylon", 1400.0)):
        force, strain = h.spring_check(modulus)
        print(f"clip in {material}: about {force:.1f} N of clamp, peak strain {strain * 100:.2f}%")
    report("test fit", fit)
    if len(solid(body).Solids()) > 1:
        describe("holster", body)
    print(f"keyboard into holster: {overlap(keyboard, body):.2f} mm3 of overlap (should be about 0)")
    if overlap(keyboard, body) > 1:
        describe("overlap", keyboard.intersect(body))
    print(f"clip into holster: {overlap(clip, body):.2f} mm3 of overlap (the preload, at the tip)")
    mirror = lambda w: w.mirror("YZ")
    for name, part in (("holster", body), ("clip", clip), ("clip-steel", steel), ("test-fit", fit)):
        export(part, f"{name}-right")
        export(mirror(part), f"{name}-left")
    print("wrote", len(list(OUT.iterdir())), "files to", OUT)


if __name__ == "__main__":
    main()
