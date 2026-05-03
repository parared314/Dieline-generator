from dieline.base_template import BaseTemplate
from dieline.svg_builder import LayerName, SVGBuilder


class TuckTopBox(BaseTemplate):
    """
    Standard retail tuck-top box (tuck-in top and bottom flaps).

    Net layout (flat unfolded):

        [glue tab | front | depth | back | depth]   ← wide axis
        top tuck flap
        ──────────────
        body (height)
        ──────────────
        bottom tuck flap

    The tuck tabs have a small angled notch so they slide into the slot.
    """

    TEMPLATE_ID = "tuck_top_box"
    TEMPLATE_NAME = "Tuck-Top Box"
    DESCRIPTION = "Retail box with tuck-in top and bottom flaps."

    def generate(self, params: dict) -> SVGBuilder:
        W = float(params["width"])
        H = float(params["height"])
        D = float(params["depth"])
        FH = float(params["flap_height"])   # tuck flap height
        GW = float(params["glue_tab_width"])
        BL = float(params["bleed"])

        # Panel widths left→right: glue | front | depth | back | depth
        panels = [GW, W, D, W, D]
        total_W = sum(panels)
        total_H = FH + H + FH  # top flap + body + bottom flap

        builder = SVGBuilder(total_W + 2 * BL, total_H + 2 * BL)
        ox = BL  # x origin (left of net)
        oy = BL  # y origin (top of net)

        # ── CUT LINES ──────────────────────────────────────────────────
        # Tuck tab width equals the depth panel; height = FH with angled tip
        tuck_notch = min(5.0, FH * 0.3)  # angled notch depth

        # Top edge (with tuck-tab profile on front and back panels)
        # We build the outer cut contour as one closed path
        # x positions of panel folds (cumulative)
        xs = [ox]
        for pw in panels:
            xs.append(xs[-1] + pw)
        # xs[0]=glue left, xs[1]=front left, xs[2]=front right/depth left,
        # xs[3]=depth right/back left, xs[4]=back right/depth2 left, xs[5]=right edge

        # Top tuck tabs on front panel (xs[1]..xs[2]) and back panel (xs[3]..xs[4])
        # Side panels (glue, depth) have straight top/bottom edges at oy
        top_y = oy
        body_top = oy + FH
        body_bot = oy + FH + H
        bot_y = oy + FH + H + FH

        # Build cut path: start at top-left of glue tab, go clockwise
        # Top edge: glue straight, front tuck tab, depth straight, back tuck tab, depth2 straight
        def tuck_top_points(x_left, x_right, top_y, tuck_y):
            """Points for top tuck tab going up from top_y."""
            w = x_right - x_left
            notch = tuck_notch
            return [
                (x_left, top_y),
                (x_left + notch, tuck_y),
                (x_right - notch, tuck_y),
                (x_right, top_y),
            ]

        def tuck_bot_points(x_left, x_right, bot_y, tuck_y):
            """Points for bottom tuck tab going down from bot_y."""
            notch = tuck_notch
            return [
                (x_left, bot_y),
                (x_left + notch, tuck_y),
                (x_right - notch, tuck_y),
                (x_right, bot_y),
            ]

        tuck_top = oy  # straight top for side panels
        tuck_front_top = oy  # front tuck goes to oy already (flat top)
        # For realistic dieline, tuck flap is on top, so the tuck-tab
        # protrudes above the body. The front/back panels have full FH tuck flap.
        # Depth panels have half the tuck flap height (dust flap).
        dust_FH = FH * 0.5

        # Full outer cut outline as a polyline (clockwise)
        pts: list[tuple[float, float]] = []

        # Start: top-left of glue tab
        pts.append((xs[0], oy + FH - dust_FH))      # glue tab top-left
        pts.append((xs[0], oy + FH + H + dust_FH))  # glue tab bottom-left
        # bottom: glue straight bottom, then across
        pts.append((xs[1], bot_y))                  # bottom-left of front
        # bottom tuck tab front
        pts.extend(tuck_bot_points(xs[1], xs[2], bot_y, bot_y + tuck_notch * 0.6))
        pts.append((xs[2], oy + FH + H + dust_FH))  # depth1 bottom
        pts.append((xs[3], oy + FH + H + dust_FH))  # back bottom
        # bottom tuck tab back
        pts.extend(tuck_bot_points(xs[3], xs[4], bot_y, bot_y + tuck_notch * 0.6))
        pts.append((xs[5], oy + FH + H + dust_FH))  # depth2 bottom
        pts.append((xs[5], oy + FH - dust_FH))       # depth2 top-right

        # top: depth2 straight, back tuck, depth1 straight, front tuck, glue
        pts.extend(reversed(tuck_top_points(xs[3], xs[4], tuck_top + FH - dust_FH, oy - tuck_notch * 0.6)))
        pts.append((xs[3], oy + FH - dust_FH))
        pts.append((xs[2], oy + FH - dust_FH))
        pts.extend(reversed(tuck_top_points(xs[1], xs[2], tuck_top + FH - dust_FH, oy - tuck_notch * 0.6)))
        pts.append((xs[1], oy + FH - dust_FH))
        pts.append((xs[0], oy + FH - dust_FH))       # close

        d_cut = "M " + " L ".join(f"{x:.4f} {y:.4f}" for x, y in pts) + " Z"
        builder.add_path(LayerName.CUT, d_cut)

        # ── FOLD LINES ─────────────────────────────────────────────────
        # Vertical panel folds (full height)
        for x in xs[1:5]:
            builder.add_line(LayerName.FOLD, x, oy, x, oy + total_H)

        # Horizontal flap folds (across full width)
        builder.add_line(LayerName.FOLD, xs[0], body_top, xs[5], body_top)
        builder.add_line(LayerName.FOLD, xs[0], body_bot, xs[5], body_bot)

        # ── PERFORATION ────────────────────────────────────────────────
        if params.get("perforation"):
            # Perforation line just inside the bottom fold on front+back panels
            py = body_bot - 4
            builder.add_line(LayerName.PERFORATION, xs[1], py, xs[2], py)
            builder.add_line(LayerName.PERFORATION, xs[3], py, xs[4], py)

        # ── GUIDES / BLEED ─────────────────────────────────────────────
        if BL > 0:
            builder.add_rect(LayerName.GUIDES, BL / 2, BL / 2,
                             total_W + BL, total_H + BL)

        return builder
