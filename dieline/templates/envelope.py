import math

from dieline.base_template import BaseTemplate
from dieline.svg_builder import LayerName, SVGBuilder


class Envelope(BaseTemplate):
    """
    Flat envelope / document mailer.

    Net layout:

        [top flap (fold-over)]
        ──────────────────────
        [left flap | body | right flap]
        ──────────────────────
        [bottom seal flap]

    Flap styles: straight, diagonal, rounded (affects top flap shape).
    """

    TEMPLATE_ID = "envelope"
    TEMPLATE_NAME = "Envelope / Mailer"
    DESCRIPTION = "Flat envelope with fold-over flap. Suitable for documents and flat items."

    def generate(self, params: dict) -> SVGBuilder:
        W = float(params["width"])
        H = float(params["height"])
        FH = float(params["flap_height"])         # top fold-over flap height
        SFW = float(params["side_flap_width"])    # side glue flap width
        BFH = float(params["bottom_flap_height"]) # bottom seal flap height
        flap_style = str(params.get("flap_style", "diagonal"))
        BL = float(params["bleed"])

        total_W = SFW + W + SFW
        total_H = FH + H + BFH

        builder = SVGBuilder(total_W + 2 * BL, total_H + 2 * BL)
        ox = BL
        oy = BL

        # Key x positions
        x0 = ox
        x1 = ox + SFW       # body left
        x2 = ox + SFW + W   # body right
        x3 = ox + total_W   # right edge

        # Key y positions
        y0 = oy
        y1 = oy + FH        # body top (flap fold line)
        y2 = oy + FH + H    # body bottom (bottom flap fold line)
        y3 = oy + total_H   # bottom edge

        # ── CUT LINES: top flap ────────────────────────────────────────
        # Top flap spans full body width (x1..x2); flap height = FH
        mid_x = (x1 + x2) / 2

        if flap_style == "straight":
            # Rectangular flap
            flap_pts = [(x1, y1), (x1, y0), (x2, y0), (x2, y1)]
        elif flap_style == "rounded":
            # Flap with a semicircular rounded tip
            r = min(FH, (x2 - x1) / 2)
            # arc from (x1, y0+r) to (x2, y0+r) going up
            flap_pts = [(x1, y1), (x1, y0 + r)]
            # approximate arc as polyline (8 segments)
            steps = 12
            for i in range(steps + 1):
                angle = math.pi - (math.pi * i / steps)
                px = mid_x + r * math.cos(angle)
                py = (y0 + r) + r * math.sin(angle)
                flap_pts.append((px, py))
            flap_pts.append((x2, y1))
        else:  # diagonal
            # Pointed / diamond flap
            tip_y = y0
            flap_pts = [
                (x1, y1),
                (x1, y0 + FH * 0.4),
                (mid_x, tip_y),
                (x2, y0 + FH * 0.4),
                (x2, y1),
            ]

        # ── CUT LINES: full outer contour ─────────────────────────────
        # Side flaps taper slightly (triangle shape) for easier sealing
        side_taper = min(SFW * 0.3, 8.0)

        # Build full cut outline clockwise:
        # Start at body top-left (x1, y1), go up for flap, come back, across top
        cut_pts = []

        # Top-left corner (body meets flap)
        cut_pts += [(x1, y1)]
        # Top flap
        cut_pts += flap_pts[1:]  # skip first point (x1,y1), already added

        # Right side going down: body top-right → side flap → body bottom-right
        cut_pts += [
            (x2, y1),                            # body top-right
            (x3, y1 + side_taper),               # right flap outer top
            (x3, y2 - side_taper),               # right flap outer bottom
            (x2, y2),                            # body bottom-right
        ]

        # Bottom seal flap
        cut_pts += [
            (x2, y2),
            (x2, y3),
            (x1, y3),
            (x1, y2),
        ]

        # Left side going up
        cut_pts += [
            (x1, y2),                            # body bottom-left
            (x0, y2 - side_taper),               # left flap outer bottom
            (x0, y1 + side_taper),               # left flap outer top
            (x1, y1),                            # body top-left (close)
        ]

        # Remove consecutive duplicates
        clean = [cut_pts[0]]
        for p in cut_pts[1:]:
            if (abs(p[0] - clean[-1][0]) > 0.001 or abs(p[1] - clean[-1][1]) > 0.001):
                clean.append(p)

        d_cut = "M " + " L ".join(f"{x:.4f} {y:.4f}" for x, y in clean) + " Z"
        builder.add_path(LayerName.CUT, d_cut)

        # ── FOLD LINES ─────────────────────────────────────────────────
        # Horizontal: top flap fold, bottom flap fold
        builder.add_line(LayerName.FOLD, x0, y1, x3, y1)
        builder.add_line(LayerName.FOLD, x0, y2, x3, y2)

        # Vertical: left flap fold, right flap fold
        builder.add_line(LayerName.FOLD, x1, y1, x1, y2)
        builder.add_line(LayerName.FOLD, x2, y1, x2, y2)

        # ── PERFORATION ────────────────────────────────────────────────
        if params.get("perforation"):
            # Tear-off perforation just below the top flap fold
            perf_y = y1 + 3
            builder.add_line(LayerName.PERFORATION, x1, perf_y, x2, perf_y)

        # ── GUIDES / BLEED ─────────────────────────────────────────────
        if BL > 0:
            builder.add_rect(LayerName.GUIDES, BL / 2, BL / 2,
                             total_W + BL, total_H + BL)

        return builder
