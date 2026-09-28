"""Reproducible offline acceptance; pytest owns temporary SQLite and network guards.

Run from any directory with the project Python: python pilot/scripts/ax_offline_smoke.py
No production configuration, DB migration, policy promotion or provider calls.
"""
import subprocess
import sys
from pathlib import Path


def main():
    root=Path(__file__).resolve().parents[2]
    suite='pilot/tests/test_ax_refactor.py'
    tests=[
        'test_offline_deep_tracks_merge_gate_frozen_report',
        'test_expansion_chooses_real_track_and_preserves_original',
        'test_full_q_selects_other_candidate_actual_repair_and_independent_audit',
        'test_action_dependent_q_changes_choices_by_state_and_masks',
        'test_history_changes_priority_only_with_matching_conditions',
        'test_condition_recheck_transport_failure_retains_response',
        'test_isolated_review_queue_train_shadow_next_run_end_to_end',
    ]
    return subprocess.call([sys.executable,'-m','pytest','-q',*[suite+'::'+name for name in tests]],cwd=root)


if __name__=='__main__':
    raise SystemExit(main())
