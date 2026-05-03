from dieline.base_template import BaseTemplate
from dieline.svg_builder import LayerName, SVGBuilder


class TrayBox(BaseTemplate):
    """
    Open-top tray / shelf box.

    Net layout:

              [top side flap]
        [left end | bottom | right end | glue tab]
              [bottom side flap]

    The four corner triangular notches prevent bulging when assembled.
    """

    TEMPLATE_ID = "tray_box"
    TEMPLATE_NAME = "Tray Box"
    DESCRIPTION = "Open-top tray box with four walls and a glue tab."

    def generate(self, params: dict) -> SVGBuilder:
        W = float(params["width"])    # inner tray width
        L = float(params["length"])   # inner tray length
        H = float(params["height"])   # tray height (wall height)
        GW = float(params["glue_tab_width"])
        CN = float(params["corner_notch"])  # corner notch size
        BL = float(params["bleed"])

        # Net dimensions
        total_W = H + L + H + GW       # left wall + base + right wall + glue tab
        total_H = H + W + H            # front wall + base + back wall

        builder = SVGBuilder(total_W + 2 * BL, total_H + 2 * BL)
        ox = BL
        oy = BL

        # Key x positions (left → right)
        x0 = ox
        x1 = ox + H          # base left
        x2 = ox + H + L      # base right
        x3 = ox + H + L + H  # glue tab left
        x4 = ox + total_W    # right edge

        # Key y positions (top → bottom)
        y0 = oy
        y1 = oy + H          # base top
        y2 = oy + H + W      # base bottom
        y3 = oy + total_H    # bottom edge

        # ── CUT LINES ──────────────────────────────────────────────────
        # Outer contour with corner notches.
        # Corner notch: square cut-out at each corner of side flaps
        # to prevent wall overlap when folded.

        # Full outline points (clockwise from top-left):
        pts = [
            # Top edge: left wall top, then base top (with corner notches), right wall top, glue tab top
            (x0, y1),           # left wall top-left
            (x0, y0),           # left wall top corner → up to top
            # wait — the left wall flap doesn't extend to y0 at x0
            # Let me restructure: the net is a cross shape
        ]

        # Actually build as separate closed regions for clarity.
        # 1) Base + four walls (cross shape)
        # 2) Corner notches as cut-outs

        # Cross-shaped outer path:
        # Top flap (front wall): x1..x2, y0..y1  (with corner notches at x1,y1 and x2,y1)
        # Left wall: x0..x1, y1..y2  (with corner notches at x1,y1 and x1,y2)
        # Base: x1..x2, y1..y2
        # Right wall: x2..x3, y1..y2  (with corner notches at x2,y1 and x2,y2)
        # Glue tab: x3..x4, y1..y2
        # Bottom flap (back wall): x1..x2, y2..y3  (with corner notches at x1,y2 and x2,y2)

        # Build cross outline clockwise from (x1, y0):
        cut_pts = [
            (x1, y0),           # front wall top-left
            (x2, y0),           # front wall top-right
            (x2, y1),           # front wall → right wall junction (with notch)
        ]

        if CN > 0:
            # top-right notch of front wall
            cut_pts[-1] = (x2, y0)
            cut_pts += [(x2, y1 - CN), (x2 - CN, y1 - CN), (x2 - CN, y1)]
            # top-right of right wall
            cut_pts += [(x2, y1), (x3, y1)]
        else:
            cut_pts += [(x3, y1)]

        # Right wall and glue tab top
        cut_pts += [
            (x3, y1),
            (x4, y1),           # glue tab top-right
            (x4, y2),           # glue tab bottom-right
            (x3, y2),
        ]

        if CN > 0:
            cut_pts += [(x2 + CN, y2), (x2 + CN, y2 + CN), (x2, y2 + CN), (x2, y3)]
        else:
            cut_pts += [(x2, y3)]

        # Bottom flap
        cut_pts += [
            (x2, y3),
            (x1, y3),
        ]

        if CN > 0:
            cut_pts += [(x1, y2 + CN), (x1 - CN, y2 + CN), (x1 - CN, y2), (x0, y2)]
        else:
            cut_pts += [(x0, y2)]

        # Left wall
        cut_pts += [
            (x0, y2),
            (x0, y1),
        ]

        if CN > 0:
            cut_pts += [(x1 - CN, y1), (x1 - CN, y1 - CN), (x1, y1 - CN), (x1, y0)]
        else:
            cut_pts += [(x1, y0)]

        # Remove duplicate consecutive points
        clean_pts = [cut_pts[0]]
        for p in cut_pts[1:]:
            if p != clean_pts[-1]:
                clean_pts.append(p)

        d_cut = "M " + " L ".join(f"{x:.4f} {y:.4f}" for x, y in clean_pts) + " Z"
        builder.add_path(LayerName.CUT, d_cut)

        # ── FOLD LINES ─────────────────────────────────────────────────
        # Vertical folds (base sides)
        builder.add_line(LayerName.FOLD, x1, y0, x1, y3)
        builder.add_line(LayerName.FOLD, x2, y0, x2, y3)
        builder.add_line(LayerName.FOLD, x3, y1, x3, y2)  # glue tab fold

        # Horizontal folds (base top/bottom)
        builder.add_line(LayerName.FOLD, x0, y1, x4, y1)
        builder.add_line(LayerName.FOLD, x0, y2, x4, y2)

        # ── GUIDES / BLEED ─────────────────────────────────────────────
        if BL > 0:
            builder.add_rect(LayerName.GUIDES, BL / 2, BL / 2,
                             total_W + BL, total_H + BL)

        return builder
