"""Ordered report blocks: each artifact is placed by its own template slot."""
import math
import re
import secrets
import unicodedata
from markdown_it import MarkdownIt
from .report_style import references_html

def _width(text):
    return sum(2 if unicodedata.east_asian_width(c) in 'WF' else 1 for c in text)

def _table_columns(tokens):
    for token in tokens:
        if token.type in ('th_open', 'td_open'):
            token.attrSet('style', 'text-align:center;vertical-align:middle')
    for start, token in enumerate(tokens):
        if token.type != 'table_open': continue
        rows, row, headers = [], [], []
        for t in tokens[start+1:]:
            if t.type == 'table_close': break
            if t.type == 'tr_open': row = []
            if t.type == 'inline':
                row.append(''.join(c.content for c in (t.children or []) if c.type in ('text','code_inline')))
            if t.type == 'tr_close':
                rows.append(row)
                if not headers: headers = row
        count = len(headers)
        if not count: continue
        matrix = count > 2 and headers[0] == '해결책' and headers[-1] == '종합' and all(h.isdigit() for h in headers[1:-1])
        if matrix:
            weights = [35] + [57 / (count-2)] * (count-2) + [8]
            token.attrSet('class', 'report-matrix')
        else:
            weights = []
            for i in range(count):
                lengths = sorted(_width(r[i]) for r in rows if i < len(r))
                typical = lengths[min(len(lengths)-1, int(len(lengths)*.8))]
                weights.append(max(3, _width(headers[i]) + 1, min(45, math.sqrt(typical) * 2.8)))
            total = sum(weights)
            weights = [w / total * 100 for w in weights]
        token.meta = {'columns': weights}

def render_markdown(body, emphasize_tables=True):
    parser = MarkdownIt('commonmark', {'html': False}).enable('table')
    def table_open(tokens, idx, options, env):
        token = tokens[idx]
        cls = token.attrGet('class') or ''
        cols = ''.join(f'<col style="width:{width:.3f}%">' for width in token.meta.get('columns', []))
        return f'<table class="{cls}"><colgroup>{cols}</colgroup>\n'
    parser.renderer.rules['table_open'] = table_open
    from .visuals import TERM_COLORS
    from html import escape
    def styled_text(tokens, idx, options, env):
        text = tokens[idx].content
        color = env.get('cell_color') if emphasize_tables else None
        return f'<strong class="report-term" style="color:{color}">{escape(text)}</strong>' if color and text.strip() else escape(text)
    parser.renderer.rules['text'] = styled_text
    def cell_open(tokens, idx, options, env):
        # Decide using the entire cell, before Markdown splits bold text or links
        # into separate tokens. A word inside a sentence must stay uncolored.
        inline = tokens[idx + 1] if idx + 1 < len(tokens) else None
        children = inline.children or [] if inline and inline.type == 'inline' else []
        text = ''.join('\n' if child.type in ('softbreak','hardbreak') else child.content for child in children)
        env['cell_color'] = TERM_COLORS.get(text.strip())
        return parser.renderer.renderToken(tokens, idx, options, env)
    def cell_close(tokens, idx, options, env):
        env['cell_color'] = None
        return parser.renderer.renderToken(tokens, idx, options, env)
    for tag in ('th', 'td'):
        parser.renderer.rules[tag + '_open'] = cell_open
        parser.renderer.rules[tag + '_close'] = cell_close
    tokens = parser.parse(body)
    _table_columns(tokens)
    return parser.renderer.render(tokens, parser.options, {'cell_color':None})

def sections(state, figures):
    from .render import render_report
    by_key = {f['key']: f for f in figures if f['key'] != 'nine-windows'}
    blocks, used = {}, set()
    prefix = 'TRIZBLOCK' + secrets.token_hex(12)
    def register(block):
        marker = prefix + str(len(blocks)) + 'END'
        blocks[marker] = block
        return '\n\n' + marker + '\n\n'
    def diagram(key):
        if key not in by_key or key in used: return ''
        used.add(key)
        return register({'type': 'figure', 'figure': by_key[key]})
    def references(cid):
        return register({'type': 'html', 'html': references_html(state, state.concept(cid))})
    markdown = render_report(state, state.report.narrative if state.report else {}, template='report_full.md.j2',
                             diagram=diagram, references=references)
    markdown = re.sub(r'```mermaid\s*.*?```', '', markdown, flags=re.S)
    markdown = re.sub(r'</?(?:sub|details|summary)>|<br\s*/?>', '', markdown)
    out = []
    for i, part in enumerate(re.split(r'(?m)^## ', markdown)):
        if i == 0 or not part.strip(): continue
        title, _, body = part.partition('\n')
        content = []
        for piece in re.split('(' + prefix + r'\d+END)', body):
            if piece in blocks: content.append(blocks[piece])
            elif piece.strip(): content.append({'type': 'html', 'html': render_markdown(piece, emphasize_tables=not bool(re.search('Executive Summary|요약', title, re.I)))})
        out.append({'key': f'report-{i}', 'title': title.strip(), 'blocks': content})
    missing = set(by_key) - used
    if missing:
        raise ValueError('Report diagram slots missing: ' + ', '.join(sorted(missing)))
    return out
