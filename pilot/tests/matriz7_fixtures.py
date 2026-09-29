"""Synthetic review records; these fixtures do not establish physical validity."""
from triz import knowledge as K

KINDS = ('SPACE', 'TIME', 'CONDITION', 'DIRECTION', 'SYSTEM_LEVEL', 'SATISFY', 'BYPASS')
ACTUAL = {'SPACE': 1, 'TIME': 9, 'CONDITION': 3, 'DIRECTION': 4,
          'SYSTEM_LEVEL': 1, 'SATISFY': 13, 'BYPASS': 24}


def payload(active=('TIME',)):
    return {'applications': [dict(
        kind=kind, applicable=kind in active,
        not_applicable_reason='' if kind in active else 'Necessary operating conditions remain unconfirmed.',
        how='Separate the actual operating phases while retaining both required functions.' if kind in active else '',
        title=kind+' proposal' if kind in active else '',
        idea='Use available resources during the required phase and validate both original functional requirements.' if kind in active else '',
        supporting_principles=[ACTUAL[kind]] if kind in active else [],
        mechanism='Operate the existing resource during the specified phase.',
        mechanism_key='phase/resource', intervention_variable='phase',
        conditions=['Operational conditions unconfirmed'], strongest_objection='No physical validation yet.',
        validation_test='Measure both original requirements.', hypothesis_ids=[],
    ) for kind in KINDS], 'redefine_hint': ''}


def legacy_payload():
    return {'applications': [dict(kind=kind, applicable=kind == 'TIME', how='Old broad condition interpretation',
        title='Legacy '+kind, idea='Stored four-approach proposal', supporting_principles=[9] if kind == 'TIME' else [])
        for kind in ('TIME', 'SPACE', 'CONDITION', 'SYSTEM_LEVEL')], 'redefine_hint': ''}


def legacy_bundle():
    from triz.ax import runtime
    from triz.ax.contracts import digest
    bundle = runtime.bundle()
    bundle.pop('bundle_id')
    bundle.pop('separation_catalog')
    bundle['prompts']['P_S5_TRACK_B'] = 'Legacy four approaches TIME SPACE CONDITION SYSTEM_LEVEL\n{{separation_block}}'
    bundle['prompts']['P_S5_ARIZ_PART5'] = 'Legacy ARIZ knowledge review\n{{separation_block}}'
    bundle['rubrics']['R5_B'] = {'description': 'Legacy four separation principles', 'criteria': [
        {'id':'C1', 'weight':.4, 'text':'Review TIME SPACE CONDITION SYSTEM_LEVEL'},
        {'id':'C2', 'weight':.35, 'text':'Explain separation axis'},
        {'id':'C3', 'weight':.25, 'text':'Retain original demands'}]}
    bundle['bundle_id'] = 'bundle-'+digest(bundle)
    return bundle
