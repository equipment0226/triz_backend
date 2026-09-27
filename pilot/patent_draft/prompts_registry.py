"""Stage prompts live in prompts/, separate from the execution service."""
from pathlib import Path

ROOT = Path(__file__).parent / 'prompts'
NAMES = ('common', 'invention', 'questions', 'search_plan', 'claim_chart', 'economics',
         'claims', 'specification', 'drawings', 'reconciliation',
         'review_technical', 'review_patent', 'review_final',
         'synthesized_solution','drafting_keywords','document_coherence')


def load_prompts():
    return {name: (ROOT / (name + '.md')).read_text(encoding='utf-8').strip() for name in NAMES}


def review_instruction(role, material=None):
    name = {'TECHNICAL_CONTENT':'review_technical', 'PATENT_CONTENT':'review_patent',
            'GLOBAL_FINAL':'review_final'}[role]
    return (material or {}).get('workflow_contract', {}).get('prompts', {}).get(name) or load_prompts()[name]
