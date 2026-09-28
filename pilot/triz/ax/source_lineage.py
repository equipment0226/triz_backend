"""Resolve recorded idea ancestry, including representatives retaining a leaf ID.

This reads saved sources only. An effect in a returned source is provenance, not
evidence that a candidate retained that effect in its final mechanism.
"""
import copy
from .contracts import digest


def _record(value):
    detail = value.get('detail')
    return {**(detail if isinstance(detail, dict) else {}),
            **{k: v for k, v in value.items() if k != 'detail'}}


def _id(value):
    return value.get('source_idea_id') or value.get('id')


def trace(state, source_ids=None):
    """Return saved leaves/records and explicit uncertainty; never guess sources.

    ``records`` contains flattened saved leaf records, keyed by source ID.
    ``complete`` is false for missing references, cycles or conflicting effects.
    None traces all inventory/current roots; an empty iterable traces no sources.
    """
    inventory = {_id(row): row for row in state.scratch.get('ax_idea_inventory', [])
                 if isinstance(row, dict) and isinstance(_id(row), str) and _id(row)}
    current = {idea.id: idea.model_dump(mode='json') for idea in state.solve.raw_ideas}
    roots = {**inventory, **current}
    nested = {}

    def index(row):
        value = _record(row)
        for child in value.get('source_details') or []:
            if not isinstance(child, dict):
                continue
            ident = _id(child)
            if isinstance(ident, str) and ident:
                nested.setdefault(ident, child)
            index(child)
    for row in roots.values():
        index(row)

    records, versions, missing, cycles, conflicts = {}, set(), set(), set(), set()
    visiting, visited = set(), set()

    def leaf(ident, row):
        value = _record(row)
        prior = records.get(ident)
        if prior is not None and prior.get('source_effect_id') != value.get('source_effect_id'):
            conflicts.add(ident)
        else:
            records.setdefault(ident, copy.deepcopy(value))

    def walk(ident, supplied=None):
        row = supplied if supplied is not None else roots.get(ident, nested.get(ident))
        if row is None:
            missing.add(ident)
            return
        version = digest(row)
        key = (ident, version)
        if key in visiting:
            cycles.add(ident)
            return
        if key in visited:
            return
        visiting.add(key)
        versions.add(version)
        value = _record(row)
        details = {}
        for child in value.get('source_details') or []:
            if isinstance(child, dict) and isinstance(_id(child), str) and _id(child):
                sid = _id(child)
                if sid in details and digest(details[sid]) != digest(child):
                    conflicts.add(sid)
                details[sid] = child
        sources = {sid for sid in value.get('source_idea_ids') or []
                   if isinstance(sid, str) and sid} | set(details)
        if not sources:
            leaf(ident, row)
        else:
            for sid in sorted(sources):
                child = details.get(sid)
                if sid == ident:
                    # Consolidation retains the first raw ID as representative.
                    # Its original same-ID source is a distinct saved record.
                    if child is not None and digest(child) != version:
                        walk(sid, child)
                    elif sources == {ident}:
                        leaf(ident, row)
                    elif ident in inventory and digest(inventory[ident]) != version:
                        walk(ident, inventory[ident])
                    else:
                        missing.add(ident)
                else:
                    # A local source packet identifies the historical source,
                    # even if the current representative reuses that source ID.
                    walk(sid, child if child is not None else
                         inventory.get(sid, roots.get(sid, nested.get(sid))))
        visiting.remove(key)
        visited.add(key)

    for ident in sorted(set(roots if source_ids is None else source_ids)):
        if isinstance(ident, str) and ident:
            walk(ident)
    return dict(leaves=sorted(records), records=records, versions=sorted(versions),
                missing=sorted(missing), cycles=sorted(cycles), conflicts=sorted(conflicts),
                complete=not (missing or cycles or conflicts))
