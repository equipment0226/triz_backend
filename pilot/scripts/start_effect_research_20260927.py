"""Archive the 1,500-card baseline and initialize the requested 2,000-card campaign."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'research/effects'

def main():
    archive=D/'audit-2026-09-27-before2000'
    progress=D/'resume-2026-09-27.json'
    assert not archive.exists() and not progress.exists(),'Campaign already initialized'
    text=(D/'catalog.tsv').read_text(encoding='utf-8')
    count=sum(bool(line) and not line.startswith(('#','@')) for line in text.splitlines())
    assert count==1500,count
    archive.mkdir()
    names=['catalog.tsv','identifiers.json','editorial_metadata.json','literature_links.json',
           'accepted_literature_sources.json','mechanism_redirects.json','publication.json',
           'references.json','reference_observations.json','manual-progress.json']
    for name in names:shutil.copy2(D/name,archive/name)
    for name in ('effects.json','effects_sources.json'):
        shutil.copy2(ROOT/'triz/knowledge'/name,archive/name)
    record=dict(status='IN_PROGRESS',started_at=datetime.now(timezone.utc).isoformat(),
        target=2000,campaign_initial_effects=count,after_existing_merge=count,effects=count,
        remaining_to_target=500,campaign_new_effects=0,new_effects=0,completed_batches=0,
        baseline_directory=archive.name,baseline_sha256=hashlib.sha256(text.encode()).hexdigest(),
        inference_mode='conversation_only',external_llm_calls=0,
        duplicate_review='IN_PROGRESS',current_campaign_validation='PENDING',
        git_publish_requested=True,service_deployment_deferred=False,service_deployed=False)
    progress.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record))

if __name__=='__main__':main()
