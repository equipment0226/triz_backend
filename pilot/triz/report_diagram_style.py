"""Introduction's visual language, applied to report data without example content.

GuideVisual.jsx is the design reference. These helpers choose only coordinates
and colors; they never create, remove, relabel or reverse graph relationships.
"""
from collections import defaultdict

BACKGROUND = '#f4f7ed'
INK = '#284c42'
STROKE = '#b8c8b9'
ARROW = '#78917d'
USEFUL = '#43684f'
HARMFUL = '#a77058'


def kind_for(key):
    if key.startswith('tc-'): return 'contradiction'
    if key.startswith('pc-'): return 'physical-contradiction'
    if key.startswith('sufield-'): return 'sufield'
    if key.startswith('matrix-'): return 'matrix'
    if key.startswith('separation-'): return 'separation'
    if key.startswith('ariz-step-'): return 'ariz'
    if key.startswith('concept-'): return 'validation'
    return {'functions':'function', 'nine-windows':'windows', 'ifr':'flow'}.get(key, key)


def fill_for(tone, kind):
    if kind == 'separation': return '#e4eccf' if tone == 'good' else '#ffffff'
    if kind == 'physical-contradiction' and tone == 'bad': return '#edf0df'
    return {'bad':'#f3e4d9', 'good':'#e1ebc8', 'field':'#e4ebdb',
            'changed':'#fff0d5', 'added':'#eae1f9'}.get(tone, '#ffffff')


def cells_for(kind, nodes, edges, columns):
    """Return (columns, node->(row,column)); fractional columns center parents."""
    keys = [n[0] for n in nodes]
    if kind in ('contradiction', 'physical-contradiction'):
        root = 'action' if kind == 'contradiction' else 'element'
        children = ['good', 'bad'] if kind == 'contradiction' else ['a', 'b']
        if set(keys) == {root, *children}:
            return 2, {root:(0,.5), children[0]:(1,0), children[1]:(1,1)}
    if kind == 'sufield' and {'F','S1','S2'} <= set(keys) and set(keys) <= {'F','S1','S2','S3'}:
        cells = {'F':(0,.5), 'S2':(1,0), 'S1':(1,1)}
        if 'S3' in keys: cells['S3'] = (2,.5)
        return 2, cells
    if kind == 'matrix' and 'pair' in keys and len(keys) > 1:
        leaves = [k for k in keys if k != 'pair']
        columns = min(3, len(leaves))
        return columns, {'pair':(0,(columns-1)/2),
                         **{k:(1+i//columns,i%columns) for i,k in enumerate(leaves)}}
    if kind in ('ceca','ariz') and edges and len(nodes) <= 16:
        parents, levels = defaultdict(set), {}
        for a,b,*_ in edges:
            if a in keys and b in keys: parents[b].add(a)
        while len(levels) < len(keys):
            ready = [k for k in keys if k not in levels and parents[k] <= levels.keys()]
            if not ready: break  # Cycles retain the general graph layout.
            for k in ready: levels[k] = 1+max((levels[p] for p in parents[k]), default=-1)
        if len(levels) == len(keys) and 1 < max(levels.values())+1 <= 4:
            groups = [[k for k in keys if levels[k] == i] for i in range(max(levels.values())+1)]
            tallest = max(map(len,groups))
            cells = {k:(tallest-len(group)+2*i,col) for col,group in enumerate(groups) for i,k in enumerate(group)}
            rows = {r:i for i,r in enumerate(sorted({r for r,c in cells.values()}))}
            return len(groups), {k:(rows[r],c) for k,(r,c) in cells.items()}
    if kind == 'separation': columns = 2
    columns = max(1,min(columns,len(nodes) or 1))
    return columns, {k:(i//columns,i%columns) for i,k in enumerate(keys)}


def direct_path(a, b, positions, box_width):
    """A short diagonal for the three-role Introduction layouts, if unobstructed."""
    x1,y1,h1 = positions[a]; x2,y2,h2 = positions[b]
    dx,dy = x2-x1,y2-y1
    if not dx and not dy: return None
    def boundary(x,y,h,dx,dy):
        scale = 1 / max(abs(dx)/(box_width/2+5), abs(dy)/(h/2+5))
        return x+dx*scale,y+dy*scale
    p,q = boundary(x1,y1,h1,dx,dy),boundary(x2,y2,h2,-dx,-dy)
    # Slab intersection with every other rectangle, including label clearance.
    for key,(x,y,h) in positions.items():
        if key in (a,b): continue
        low,high = 0.,1.
        for start,delta,lo,hi in ((p[0],q[0]-p[0],x-box_width/2-15,x+box_width/2+15),
                                (p[1],q[1]-p[1],y-h/2-15,y+h/2+15)):
            if not delta:
                if not lo <= start <= hi: low,high = 1,0; break
            else:
                t1,t2 = sorted(((lo-start)/delta,(hi-start)/delta))
                low,high = max(low,t1),min(high,t2)
        if low <= high: return None
    return [p,q]
