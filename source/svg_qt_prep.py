"""Convert CorelDRAW SVG fonts + <text> into path outlines for QtSvg.

Qt's QSvgRenderer does not draw ``@font-face … format(svg)`` glyph fonts, so
labels disappear. Chromium does. We expand each ``<text>`` into ``<path>``
using the embedded SVG font glyphs so pure Qt can show the same labels.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class _Glyph:
    d: str
    adv: float


@dataclass
class _SvgFont:
    glyphs: dict[str, _Glyph]
    default_adv: float
    units_per_em: float = 1000.0


@dataclass(frozen=True)
class _FontFace:
    font_id: str
    size: float


_NS = {"svg": "http://www.w3.org/2000/svg"}
_CLASS_FONT_RE = re.compile(
    r"\.(fnt\d+)\s*\{([^}]*)\}",
    re.IGNORECASE,
)
_FACE_RE = re.compile(
    r"@font-face\s*\{([^}]*)\}",
    re.IGNORECASE,
)
_PROP_RE = re.compile(r"([a-zA-Z-]+)\s*:\s*([^;]+)")


def _local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _parse_props(blob: str) -> dict[str, str]:
    return {
        m.group(1).strip().lower(): m.group(2).strip().strip("'\"")
        for m in _PROP_RE.finditer(blob)
    }


def _parse_fonts(root: ET.Element) -> dict[str, _SvgFont]:
    fonts: dict[str, _SvgFont] = {}
    for font_el in root.iter():
        if _local(font_el.tag) != "font":
            continue
        font_id = font_el.get("id")
        if not font_id:
            continue
        default_adv = float(font_el.get("horiz-adv-x") or 1000)
        units = 1000.0
        glyphs: dict[str, _Glyph] = {}
        for child in font_el:
            name = _local(child.tag)
            if name == "font-face":
                upe = child.get("units-per-em")
                if upe:
                    units = float(upe)
            elif name == "glyph":
                uni = child.get("unicode")
                d = child.get("d") or ""
                if uni is None:
                    continue
                adv = float(child.get("horiz-adv-x") or default_adv)
                glyphs[uni] = _Glyph(d=d, adv=adv)
        fonts[font_id] = _SvgFont(
            glyphs=glyphs, default_adv=default_adv, units_per_em=units
        )
    return fonts


def _parse_style_maps(root: ET.Element) -> tuple[dict[str, _FontFace], dict[str, str]]:
    """Return (css_class -> FontFace, css_class -> fill color if known)."""
    style_text = ""
    for el in root.iter():
        if _local(el.tag) == "style" and el.text:
            style_text += el.text

    # Map font-family+weight+style signature -> FontID from @font-face src.
    face_key_to_id: dict[tuple[str, str, str], str] = {}
    for face in _FACE_RE.finditer(style_text):
        props = _parse_props(face.group(1))
        family = props.get("font-family", "").strip("'\"")
        weight = props.get("font-weight", "normal").lower()
        fstyle = props.get("font-style", "normal").lower()
        src = props.get("src", "")
        m = re.search(r'url\(["\']?#([^"\')\s]+)', src)
        if not m:
            continue
        face_key_to_id[(family.lower(), weight, fstyle)] = m.group(1)

    def _norm_weight(w: str) -> str:
        w = w.lower()
        if w in {"bold", "700", "800", "900"}:
            return "bold"
        return "normal"

    def _norm_style(s: str) -> str:
        s = s.lower()
        if s in {"italic", "oblique"}:
            return "italic"
        return "normal"

    class_to_face: dict[str, _FontFace] = {}
    for m in _CLASS_FONT_RE.finditer(style_text):
        cls = m.group(1)
        props = _parse_props(m.group(2))
        if "font-family" not in props or "font-size" not in props:
            continue
        family = props["font-family"].strip("'\"")
        weight = _norm_weight(props.get("font-weight", "normal"))
        fstyle = _norm_style(props.get("font-style", "normal"))
        size_s = props["font-size"].replace("px", "").strip()
        try:
            size = float(size_s)
        except ValueError:
            continue
        font_id = face_key_to_id.get((family.lower(), weight, fstyle))
        if font_id is None:
            # Fallbacks: ignore style, then ignore weight.
            font_id = face_key_to_id.get((family.lower(), weight, "normal"))
        if font_id is None:
            font_id = face_key_to_id.get((family.lower(), "normal", fstyle))
        if font_id is None:
            font_id = face_key_to_id.get((family.lower(), "normal", "normal"))
        if font_id is None:
            continue
        class_to_face[cls] = _FontFace(font_id=font_id, size=size)

    return class_to_face, {}


def _text_content(el: ET.Element) -> str:
    parts: list[str] = [el.text or ""]
    for child in el:
        parts.append(_text_content(child))
        parts.append(child.tail or "")
    return "".join(parts)


def _text_to_path_group(
    text_el: ET.Element,
    fonts: dict[str, _SvgFont],
    class_to_face: dict[str, _FontFace],
) -> ET.Element | None:
    classes = (text_el.get("class") or "").split()
    face: _FontFace | None = None
    for cls in classes:
        if cls in class_to_face:
            face = class_to_face[cls]
            break
    if face is None:
        return None
    font = fonts.get(face.font_id)
    if font is None:
        return None

    content = _text_content(text_el)
    if not content:
        return None

    try:
        x0 = float(text_el.get("x") or 0)
        y0 = float(text_el.get("y") or 0)
    except ValueError:
        return None

    scale = face.size / font.units_per_em
    # SVG font y-up → SVG user y-down.
    g = ET.Element("g")
    # Preserve fill from text classes when possible (fil1 = black, etc.).
    fill_class = " ".join(c for c in classes if c.startswith("fil"))
    if fill_class:
        g.set("class", fill_class)
    else:
        g.set("fill", "black")

    transform = text_el.get("transform")
    base_tf = f"translate({x0},{y0}) scale({scale},{-scale})"
    g.set("transform", f"{transform} {base_tf}" if transform else base_tf)

    pen = 0.0
    space_adv = font.default_adv * 0.33
    for ch in content:
        glyph = font.glyphs.get(ch)
        if glyph is None:
            # Whitespace / missing: advance without drawing.
            if ch.isspace():
                pen += space_adv
            else:
                pen += font.default_adv * 0.5
            continue
        if glyph.d:
            path = ET.SubElement(g, "path")
            path.set("d", glyph.d)
            path.set("transform", f"translate({pen},0)")
        pen += glyph.adv
    return g


def prepare_svg_for_qt(svg_bytes: bytes) -> bytes:
    """Return SVG bytes with ``<text>`` expanded to glyph paths for QtSvg."""
    # Preserve default namespace so Qt still parses the file.
    text = svg_bytes.decode("utf-8", errors="replace")
    # ElementTree needs a single root; Corel files are fine.
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return svg_bytes

    fonts = _parse_fonts(root)
    if not fonts:
        return svg_bytes
    class_to_face, _ = _parse_style_maps(root)
    if not class_to_face:
        return svg_bytes

    # Replace text nodes from deepest first so nested structures stay stable.
    parents = {c: p for p in root.iter() for c in p}
    texts = [el for el in root.iter() if _local(el.tag) == "text"]
    for text_el in texts:
        parent = parents.get(text_el)
        if parent is None:
            continue
        replacement = _text_to_path_group(text_el, fonts, class_to_face)
        if replacement is None:
            continue
        # Keep sibling order.
        kids = list(parent)
        idx = kids.index(text_el)
        parent.remove(text_el)
        parent.insert(idx, replacement)

    # Drop bulky SVG font definitions (no longer needed).
    for font_el in list(root.iter()):
        if _local(font_el.tag) != "font":
            continue
        parent = parents.get(font_el)
        # parents map may be stale after inserts; rebuild if needed.
        if parent is None:
            parents = {c: p for p in root.iter() for c in p}
            parent = parents.get(font_el)
        if parent is not None:
            parent.remove(font_el)

    out = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return out
