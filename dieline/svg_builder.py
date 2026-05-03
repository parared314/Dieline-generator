import math
from enum import Enum
from xml.etree import ElementTree as ET


class LayerName(str, Enum):
    CUT = "Cut Lines"
    FOLD = "Fold Lines"
    PERFORATION = "Perforation Lines"
    GUIDES = "Guides / Bleed"


LINE_STYLES = {
    LayerName.CUT: {
        "stroke": "#FF0000",
        "stroke-width": "0.5",
        "stroke-dasharray": "none",
        "fill": "none",
    },
    LayerName.FOLD: {
        "stroke": "#0000FF",
        "stroke-width": "0.5",
        "stroke-dasharray": "6,3",
        "fill": "none",
    },
    LayerName.PERFORATION: {
        "stroke": "#FF00FF",
        "stroke-width": "0.5",
        "stroke-dasharray": "6,3,1,3",
        "fill": "none",
    },
    LayerName.GUIDES: {
        "stroke": "#CCCCCC",
        "stroke-width": "0.25",
        "stroke-dasharray": "10,5",
        "fill": "none",
    },
}

SVG_NS = "http://www.w3.org/2000/svg"
INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"


class SVGBuilder:
    """Accumulates geometry into named layers and emits Inkscape/Illustrator-compatible SVG."""

    def __init__(self, width_mm: float, height_mm: float):
        self.width_mm = width_mm
        self.height_mm = height_mm
        self._layers: dict[LayerName, list[ET.Element]] = {l: [] for l in LayerName}

    def add_line(self, layer: LayerName, x1: float, y1: float, x2: float, y2: float):
        el = ET.Element("line", x1=f"{x1:.4f}", y1=f"{y1:.4f}", x2=f"{x2:.4f}", y2=f"{y2:.4f}")
        self._layers[layer].append(el)

    def add_path(self, layer: LayerName, d: str):
        el = ET.Element("path", d=d.strip())
        self._layers[layer].append(el)

    def add_polyline(self, layer: LayerName, points: list[tuple[float, float]]):
        pts = " ".join(f"{x:.4f},{y:.4f}" for x, y in points)
        el = ET.Element("polyline", points=pts)
        self._layers[layer].append(el)

    def add_rect(self, layer: LayerName, x: float, y: float, w: float, h: float):
        d = f"M {x:.4f} {y:.4f} L {x+w:.4f} {y:.4f} L {x+w:.4f} {y+h:.4f} L {x:.4f} {y+h:.4f} Z"
        self.add_path(layer, d)

    def add_arc(
        self,
        layer: LayerName,
        cx: float,
        cy: float,
        r: float,
        start_deg: float,
        end_deg: float,
    ):
        sa = math.radians(start_deg)
        ea = math.radians(end_deg)
        x1 = cx + r * math.cos(sa)
        y1 = cy + r * math.sin(sa)
        x2 = cx + r * math.cos(ea)
        y2 = cy + r * math.sin(ea)
        large = 1 if abs(end_deg - start_deg) > 180 else 0
        d = f"M {x1:.4f} {y1:.4f} A {r:.4f} {r:.4f} 0 {large} 1 {x2:.4f} {y2:.4f}"
        self.add_path(layer, d)

    def to_svg_string(self) -> str:
        ET.register_namespace("", SVG_NS)
        ET.register_namespace("inkscape", INKSCAPE_NS)
        ET.register_namespace("sodipodi", SODIPODI_NS)

        svg = ET.Element(
            "svg",
            {
                "xmlns": SVG_NS,
                "xmlns:inkscape": INKSCAPE_NS,
                "xmlns:sodipodi": SODIPODI_NS,
                "width": f"{self.width_mm}mm",
                "height": f"{self.height_mm}mm",
                "viewBox": f"0 0 {self.width_mm:.4f} {self.height_mm:.4f}",
                "version": "1.1",
            },
        )

        ET.SubElement(
            svg,
            f"{{{SODIPODI_NS}}}namedview",
            {"inkscape:document-units": "mm"},
        )

        for layer_enum, elements in self._layers.items():
            if not elements:
                continue
            layer_id = layer_enum.value.lower().replace(" ", "_").replace("/", "").replace("__", "_")
            g = ET.SubElement(
                svg,
                "g",
                {
                    "id": layer_id,
                    "inkscape:label": layer_enum.value,
                    "inkscape:groupmode": "layer",
                },
            )
            style_str = ";".join(f"{k}:{v}" for k, v in LINE_STYLES[layer_enum].items())
            g.set("style", style_str)
            for el in elements:
                g.append(el)

        return ET.tostring(svg, encoding="unicode", xml_declaration=True)
