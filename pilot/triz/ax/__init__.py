"""Versioned AX execution, with an explicit legacy compatibility boundary."""
# The serialized 13-stage workflow contract stays compatible. Releases are
# separately pinned with code, prompt, model and policy hashes in each bundle.
WORKFLOW = 'triz-ax-v3.1'
RELEASE = 'triz-ax-v3.1.1'
SUPPORTED_WORKFLOWS = frozenset({WORKFLOW, RELEASE})


def enabled(state):
    return state.scratch.get('workflow_version') in SUPPORTED_WORKFLOWS
