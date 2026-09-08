"""Reuse the complete PoC TRIZ report, safely rendered with portable SVG at each stage."""
import re
from markdown_it import MarkdownIt

def sections(state, figures):
    from .render import render_report
    narrative = state.report.narrative if state.report else {}
    markdown = render_report(state, narrative, template="report_full.md.j2")
    # Original Mermaid descriptions are replaced by deterministic SVG, never executable scripts.
    markdown = re.sub(r"```mermaid\s*.*?```", "", markdown, flags=re.S)
    markdown = re.sub(r"</?sub>|<br\s*/?>", "", markdown)
    markdown = re.sub(r"</?(?:details|summary)>", "", markdown)
    parser = MarkdownIt("commonmark", {"html": False}).enable("table")
    groups = {
        "2": ("nine-windows", "functions", "sufield-", "resources", "ceca"),
        "3": ("ifr", "tc-", "pc-", "trimming"),
        "4": ("matrix-", "standards", "separation", "trends", "fos", "effects", "ariz"),
        "6": ("concept-",),
    }
    out, used = [], set()
    for i, part in enumerate(re.split(r"(?m)^## ", markdown)):
        if not part.strip():
            continue
        title, _, body = part.partition("\n")
        if i == 0:
            # The standalone cover is already shown by both report consumers.
            continue
        number = title.split(".", 1)[0].strip()
        selected = [f for f in figures if any(f["key"].startswith(prefix) for prefix in groups.get(number, ()))]
        used.update(f["key"] for f in selected)
        out.append({"key": f"report-{i}", "title": title.strip(), "html": parser.render(body), "figures": selected})
    remaining = [f for f in figures if f["key"] not in used]
    if remaining:
        out.append({"key": "supplement", "title": "보충 도식", "html": "", "figures": remaining})
    return out
