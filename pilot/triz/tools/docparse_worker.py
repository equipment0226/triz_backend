"""Fixed subprocess entrypoint for untrusted attachment parsers.

No application settings, database or model client is imported in this worker.
The parent applies a wall-clock deadline and bounds the returned JSON bytes.
"""
import json
import os
from pathlib import Path
import sys


def apply_limits():
    if sys.platform.startswith("linux"):
        import resource
        memory = int(os.getenv("DOCUMENT_PARSE_MEMORY_MB", "1536")) * 1024 * 1024
        if not 64 * 1024 * 1024 <= memory <= 4096 * 1024 * 1024:
            raise ValueError("Invalid memory limit")
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        limit = min(value for value in (memory, soft, hard) if value != resource.RLIM_INFINITY)
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))


def main():
    apply_limits()
    raw = sys.stdin.buffer.read(65537)
    if len(raw) > 65536:
        raise ValueError("Invalid request")
    request = json.loads(raw)
    # -I excludes cwd/PYTHONPATH; import only the fixed sibling implementation.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from docparse import _extract_local
    text, facts = _extract_local(Path(request["path"]), request["filename"])
    sys.stdout.buffer.write(json.dumps({"text": text, "facts": facts}, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    main()
