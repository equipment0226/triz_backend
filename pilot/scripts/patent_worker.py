"""Dedicated Railway job: resumes sync, then exits. Redeploy to refresh again."""
import json
import os
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from triz import patent_corpus as corpus, patent_ingest as ingest
from triz.tools import vector_patents as vector


def emit(**data):
    print(json.dumps(data, ensure_ascii=False, default=str), flush=True)


def main():
    corpus.init()
    page_size = int(os.getenv('PATENT_IMPORT_PAGE_SIZE', '1000'))
    batch_size = int(os.getenv('PATENT_INDEX_BATCH_SIZE', '64'))
    if not 1 <= page_size <= 10000 or not 1 <= batch_size <= 256:
        raise RuntimeError('INVALID_WORKER_BATCH_SIZE')
    # Retries are bounded and use committed checkpoints. No paid queries exist.
    for attempt in range(4):
        try:
            ingest.import_pages(page_size=page_size, emit=emit,
                after_page=lambda: vector.index_pending(batch_size=batch_size, emit=emit))
            vector.index_pending(batch_size=batch_size, emit=emit)
            emit(phase='COMPLETE', **corpus.status())
            return 0
        except Exception as exc:
            reason = str(exc)
            if not reason.isupper() or not reason.replace('_', '').isalnum() or len(reason) > 80:
                reason = type(exc).__name__
            emit(phase='PAUSED', reason=reason, attempt=attempt+1)
            if ('CAPACITY' in reason or 'REBUILD' in reason or attempt == 3):
                return 1
            time.sleep(30)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
