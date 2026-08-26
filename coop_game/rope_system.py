from __future__ import annotations
import math
import pygame


class RopeNode:
    __slots__ = ('x', 'y', 'px', 'py', 'pinned')

    def __init__(self, x: float, y: float, pinned: bool = False):
        self.x = x
        self.y = y
        self.px = x
        self.py = y
        self.pinned = pinned


class RopeSystem:
    NUM_NODES = 30
    ITERATIONS = 12
    ROPE_GRAVITY = 0.45
    DAMPING = 0.998
    TAUT_THRESHOLD = 0.92
    PULL_STRENGTH = 0.35
    MAX_PULL = 4.5
    ROPE_COLOR_OUTER = (90, 60, 25)
    ROPE_COLOR_INNER = (160, 120, 60)
    ROPE_COLOR_TAUT = (200, 80, 50)

    def __init__(self, enabled: bool, max_dist: float):
        self.enabled = enabled
        self.max_dist = max_dist
        self.nodes: list[RopeNode] = []
        self._initialized = False
        self._segment_length = 0.0

    def _init_nodes(self, ax: float, ay: float, bx: float, by: float):
        self.nodes = []
        for i in range(self.NUM_NODES):
            t = i / (self.NUM_NODES - 1)
            x = ax + (bx - ax) * t
            y = ay + (by - ay) * t
            pinned = (i == 0 or i == self.NUM_NODES - 1)
            self.nodes.append(RopeNode(x, y, pinned))
        self._segment_length = self.max_dist / (self.NUM_NODES - 1)
        self._initialized = True

    def _solve_constraints(self, solids: list):
        seg_len = self._segment_length
        nodes = self.nodes
        n = len(nodes)

        for _ in range(self.ITERATIONS):
            for i in range(n - 1):
                a = nodes[i]
                b = nodes[i + 1]
                dx = b.x - a.x
                dy = b.y - a.y
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < 0.001:
                    dist = 0.001

                diff = (dist - seg_len) / dist

                if a.pinned and b.pinned:
                    continue
                elif a.pinned:
                    b.x -= dx * diff
                    b.y -= dy * diff
                elif b.pinned:
                    a.x += dx * diff
                    a.y += dy * diff
                else:
                    half = diff * 0.5
                    a.x += dx * half
                    a.y += dy * half
                    b.x -= dx * half
                    b.y -= dy * half

            for i in range(1, n - 1):
                node = nodes[i]
                for solid in solids:
                    if solid.collidepoint(node.x, node.y):
                        cx = solid.centerx
                        cy = solid.centery
                        ndx = node.x - cx
                        ndy = node.y - cy
                        hw = solid.width * 0.5
                        hh = solid.height * 0.5

                        if abs(ndx) < 0.01 and abs(ndy) < 0.01:
                            node.y = solid.top - 1
                            # only kill vertical velocity, keep horizontal
                            node.py = node.y
                            continue

                        pen_x = hw - abs(ndx)
                        pen_y = hh - abs(ndy)

                        if pen_x < pen_y:
                            if ndx > 0:
                                node.x = solid.right + 0.5
                            else:
                                node.x = solid.left - 0.5
                            # only kill velocity perpendicular to the edge (horizontal)
                            node.px = node.x
                        else:
                            if ndy > 0:
                                node.y = solid.bottom + 0.5
                            else:
                                node.y = solid.top - 0.5
                            # only kill velocity perpendicular to the edge (vertical)
                            node.py = node.y

    def apply(self, players, solids=None):
        if not self.enabled or len(players) < 2:
            return
        if solids is None:
            solids = []

        a_player = players[0]
        b_player = players[-1]

        ax = float(a_player.rect.centerx)
        ay = float(a_player.rect.centery)
        bx = float(b_player.rect.centerx)
        by = float(b_player.rect.centery)

        if not self._initialized:
            self._init_nodes(ax, ay, bx, by)

        # Update endpoint nodes to current player endpoint positions
        self.nodes[0].x = ax
        self.nodes[0].y = ay
        self.nodes[0].px = ax
        self.nodes[0].py = ay
        self.nodes[-1].x = bx
        self.nodes[-1].y = by
        self.nodes[-1].px = bx
        self.nodes[-1].py = by

        # If there are intermediate players, pin nodes at fractional indices to those players
        pinned_indices = {}
        if len(players) > 2:
            n_nodes = len(self.nodes)
            segments = len(players) - 1
            for i, pl in enumerate(players):
                t = 0.0 if segments == 0 else (i / segments)
                idx = int(round(t * (n_nodes - 1)))
                pinned_indices[idx] = pl
                node = self.nodes[idx]
                cx = float(pl.rect.centerx)
                cy = float(pl.rect.centery)
                node.x = cx
                node.y = cy
                node.px = cx
                node.py = cy
                node.pinned = True

        for i in range(1, len(self.nodes) - 1):
            node = self.nodes[i]
            vx = (node.x - node.px) * self.DAMPING
            vy = (node.y - node.py) * self.DAMPING

            node.px = node.x
            node.py = node.y

            node.x += vx
            node.y += vy + self.ROPE_GRAVITY

        self._solve_constraints(solids)

        rope_length = 0.0
        for i in range(len(self.nodes) - 1):
            na = self.nodes[i]
            nb = self.nodes[i + 1]
            dx = nb.x - na.x
            dy = nb.y - na.y
            rope_length += math.sqrt(dx * dx + dy * dy)

        # Enforce pairwise maximum distance so rope cannot stretch indefinitely.
        # For N players in series, divide total max_dist among (N-1) segments.
        n_players = len(players)
        if n_players >= 2:
            max_pair = self.max_dist
            for i in range(n_players - 1):
                pa = players[i]
                pb = players[i + 1]
                dx = float(pb.rect.centerx - pa.rect.centerx)
                dy = float(pb.rect.centery - pa.rect.centery)
                dist = math.hypot(dx, dy)
                if dist > max_pair and dist > 0.001:
                    excess = dist - max_pair
                    nx = dx / dist
                    ny = dy / dist

                    a_on_ground = getattr(pa, 'on_ground', False)
                    b_on_ground = getattr(pb, 'on_ground', False)
                    if a_on_ground and not b_on_ground:
                        weight_a = 0.2
                        weight_b = 0.8
                    elif b_on_ground and not a_on_ground:
                        weight_a = 0.8
                        weight_b = 0.2
                    else:
                        weight_a = 0.5
                        weight_b = 0.5

                    move_a_x = nx * excess * weight_a
                    move_a_y = ny * excess * weight_a
                    move_b_x = -nx * excess * weight_b
                    move_b_y = -ny * excess * weight_b

                    if hasattr(pa, 'pos'):
                        pa.pos.x += move_a_x
                        pa.pos.y += move_a_y
                        pa.rect.x = int(pa.pos.x)
                        pa.rect.y = int(pa.pos.y)
                    else:
                        pa.rect.x += int(round(move_a_x))
                        pa.rect.y += int(round(move_a_y))

                    if hasattr(pb, 'pos'):
                        pb.pos.x += move_b_x
                        pb.pos.y += move_b_y
                        pb.rect.x = int(pb.pos.x)
                        pb.rect.y = int(pb.pos.y)
                    else:
                        pb.rect.x += int(round(move_b_x))
                        pb.rect.y += int(round(move_b_y))

                    # Cancel velocity component that stretches the rope, but
                    # only for airborne players.  Grounded players keep their
                    # velocity — they are the ones doing the pulling.
                    # (nx, ny) points from pa toward pb.
                    if hasattr(pa, 'vel') and not a_on_ground:
                        # pa "away from pb" = direction (-nx, -ny)
                        v_along = pa.vel.x * nx + pa.vel.y * ny
                        if v_along < 0:  # pa moving away from pb
                            pa.vel.x -= nx * v_along
                            pa.vel.y -= ny * v_along
                    if hasattr(pb, 'vel') and not b_on_ground:
                        # pb "away from pa" = direction (nx, ny)
                        v_along = pb.vel.x * nx + pb.vel.y * ny
                        if v_along > 0:  # pb moving away from pa
                            pb.vel.x -= nx * v_along
                            pb.vel.y -= ny * v_along

        # After moving players to satisfy pairwise limits, update pinned nodes positions and re-solve constraints once
        if len(players) > 2:
            n_nodes = len(self.nodes)
            segments = len(players) - 1
            for i, pl in enumerate(players):
                t = 0.0 if segments == 0 else (i / segments)
                idx = int(round(t * (n_nodes - 1)))
                node = self.nodes[idx]
                cx = float(pl.rect.centerx)
                cy = float(pl.rect.centery)
                node.x = cx
                node.y = cy
                node.px = cx
                node.py = cy

            self._solve_constraints(solids)

        self._tautness = min(rope_length / self.max_dist, 1.0)

    def draw(self, screen, camera, players):
        if not self.enabled or len(players) < 2 or not self._initialized:
            return

        nodes = self.nodes
        n = len(nodes)
        if n < 2:
            return

        cam_x = camera.x
        cam_y = camera.y
        tautness = getattr(self, '_tautness', 0.0)

        points = []
        for node in nodes:
            points.append((node.x - cam_x, node.y - cam_y))

        if n >= 4:
            smooth_points = self._catmull_rom(points, 3)
        else:
            smooth_points = points

        if len(smooth_points) < 2:
            return

        if tautness > 0.85:
            t = min((tautness - 0.85) / 0.15, 1.0)
            r = int(self.ROPE_COLOR_OUTER[0] + (self.ROPE_COLOR_TAUT[0] - self.ROPE_COLOR_OUTER[0]) * t)
            g = int(self.ROPE_COLOR_OUTER[1] + (self.ROPE_COLOR_TAUT[1] - self.ROPE_COLOR_OUTER[1]) * t)
            b = int(self.ROPE_COLOR_OUTER[2] + (self.ROPE_COLOR_TAUT[2] - self.ROPE_COLOR_OUTER[2]) * t)
            outer_color = (r, g, b)
        else:
            outer_color = self.ROPE_COLOR_OUTER

        total = len(smooth_points)
        for i in range(total - 1):
            t = i / max(total - 1, 1)
            thickness_factor = 1.0 - 0.4 * abs(t - 0.5) * 2.0
            outer_w = max(2, int(5 * thickness_factor))
            inner_w = max(1, int(3 * thickness_factor))

            p1 = smooth_points[i]
            p2 = smooth_points[i + 1]

            p1_int = (int(p1[0]), int(p1[1]))
            p2_int = (int(p2[0]), int(p2[1]))

            pygame.draw.line(screen, outer_color, p1_int, p2_int, outer_w)
            pygame.draw.line(screen, self.ROPE_COLOR_INNER, p1_int, p2_int, inner_w)

        knot_radius = 3
        for idx in (0, n - 1):
            kx = int(nodes[idx].x - cam_x)
            ky = int(nodes[idx].y - cam_y)
            pygame.draw.circle(screen, (70, 45, 15), (kx, ky), knot_radius + 1)
            pygame.draw.circle(screen, (140, 100, 50), (kx, ky), knot_radius)

    @staticmethod
    def _catmull_rom(points, subdivisions):
        n = len(points)
        if n < 2:
            return list(points)

        result = []
        for i in range(n - 1):
            p0 = points[max(i - 1, 0)]
            p1 = points[i]
            p2 = points[min(i + 1, n - 1)]
            p3 = points[min(i + 2, n - 1)]

            for s in range(subdivisions):
                t = s / subdivisions
                t2 = t * t
                t3 = t2 * t

                x = 0.5 * (
                    (2.0 * p1[0]) +
                    (-p0[0] + p2[0]) * t +
                    (2.0 * p0[0] - 5.0 * p1[0] + 4.0 * p2[0] - p3[0]) * t2 +
                    (-p0[0] + 3.0 * p1[0] - 3.0 * p2[0] + p3[0]) * t3
                )
                y = 0.5 * (
                    (2.0 * p1[1]) +
                    (-p0[1] + p2[1]) * t +
                    (2.0 * p0[1] - 5.0 * p1[1] + 4.0 * p2[1] - p3[1]) * t2 +
                    (-p0[1] + 3.0 * p1[1] - 3.0 * p2[1] + p3[1]) * t3
                )
                result.append((x, y))

        result.append(points[-1])
        return result

    def reset(self):
        self._initialized = False
        self.nodes = []
