"""Versioned AX execution, with an explicit legacy compatibility boundary."""
WORKFLOW = 'triz-ax-v3.1'


def enabled(state):
    return state.scratch.get('workflow_version') == WORKFLOW
