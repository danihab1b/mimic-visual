"""HTML parser — extracts text nodes with position metadata from DOM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from lxml import html as lxml_html


@dataclass
class HTMLTextNode:
    text: str
    xpath: str
    dom_depth: int
    tag_name: str
    font_size: float | None = None
    font_weight: str | None = None
    text_align: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    is_visible: bool = True

    @property
    def full_text(self) -> str:
        return self.text.strip()


VISIBLE_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "span", "div", "td", "th",
                "li", "a", "label", "strong", "em", "b", "i", "code", "pre", "blockquote",
                "figcaption", "caption", "dt", "dd", "summary", "button", "option"}
HIDDEN_TAGS = {"script", "style", "noscript", "meta", "link", "head", "title"}


def extract_text_nodes(html_content: str) -> list[HTMLTextNode]:
    """Parse HTML and extract visible text nodes with DOM metadata."""
    if not html_content.strip():
        return []

    parser = lxml_html.HTMLParser(encoding="utf-8")
    doc = lxml_html.document_fromstring(html_content, parser=parser)
    nodes = []
    _walk_tree(doc, nodes, depth=0)
    return [n for n in nodes if n.is_visible and n.text.strip()]


def _walk_tree(element, nodes: list, depth: int):
    tag = getattr(element, "tag", "")
    if not isinstance(tag, str) or tag in HIDDEN_TAGS:
        return

    xpath = element.getroottree().getpath(element)
    style = _parse_inline_style(element.get("style", ""))

    children_text = []
    for child in element:
        child_nodes = []
        _walk_tree(child, child_nodes, depth + 1)
        nodes.extend(child_nodes)
        children_text.extend(c.text for c in child_nodes if c.text.strip())

    direct_text = "".join(element.text or "").strip()
    combined_text = direct_text if direct_text else ""

    if combined_text:
        node = HTMLTextNode(
            text=combined_text,
            xpath=xpath,
            dom_depth=depth,
            tag_name=tag if isinstance(tag, str) else "",
            font_size=style.get("font-size"),
            font_weight=style.get("font-weight"),
            text_align=style.get("text-align"),
            bbox=None,
            is_visible=True,
        )
        nodes.append(node)


def _parse_inline_style(style_str: str) -> dict[str, str]:
    result = {}
    if not style_str:
        return result
    for part in style_str.split(";"):
        if ":" in part:
            key, _, val = part.partition(":")
            result[key.strip().lower()] = val.strip()
    return result


def get_visible_text(html_content: str) -> str:
    """Extract all visible text from HTML as a single string."""
    nodes = extract_text_nodes(html_content)
    return "\n".join(n.text for n in nodes if n.text.strip())


def get_text_with_positions(html_content: str) -> list[dict[str, Any]]:
    """Extract text nodes with their position metadata."""
    nodes = extract_text_nodes(html_content)
    return [
        {
            "text": n.text,
            "xpath": n.xpath,
            "dom_depth": n.dom_depth,
            "tag_name": n.tag_name,
            "font_size": n.font_size,
            "font_weight": n.font_weight,
            "text_align": n.text_align,
        }
        for n in nodes
    ]
