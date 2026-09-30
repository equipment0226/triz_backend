"""Isolated extraction with page/sheet/row provenance and bounded OCR."""
import csv
import io
import json
import math
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from zipfile import ZipFile

MAX_PIXELS = 25_000_000
PDF_OCR_DPI = 130
XLSX_MAX_MEMBERS = 2048
XLSX_MAX_MEMBER_BYTES = 128 * 1024 * 1024
XLSX_MAX_EXPANDED_BYTES = 256 * 1024 * 1024
MAX_RESULT_BYTES = 2 * 1024 * 1024
_WORKER_SLOTS = None
_WORKER_SLOTS_LOCK = threading.Lock()
TEXT_EXT = {".txt", ".md", ".csv", ".json", ".yaml", ".yml", ".log"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
ALLOWED_EXT = TEXT_EXT | IMAGE_EXT | {".pdf", ".xlsx"}
def kind_of(filename):
    ext = Path(filename).suffix.lower()
    return "REPORT" if ext == ".pdf" else "DRAWING" if ext in IMAGE_EXT else "DATA" if ext in {".csv", ".xlsx"} else "SPEC"
def ocr(image):
    import pytesseract
    try:
        return pytesseract.image_to_string(image, lang=os.getenv("OCR_LANG", "eng"), timeout=20)
    except (pytesseract.TesseractNotFoundError, RuntimeError) as exc:
        return "[미추출: OCR 실행 파일 또는 언어팩 확인 필요. 도면 관계는 텍스트로 보완해 주세요.]"
def _bounded_setting(name, default, minimum, maximum):
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        raise ValueError("첨부 추출 제한 설정을 확인해 주세요.")
    if not minimum <= value <= maximum:
        raise ValueError("첨부 추출 제한 설정을 확인해 주세요.")
    return value


def _worker_slots():
    global _WORKER_SLOTS
    # One pool per API/MCP process, initialized once rather than per request.
    # Changing this deployment setting takes effect after process restart.
    with _WORKER_SLOTS_LOCK:
        if _WORKER_SLOTS is None:
            _WORKER_SLOTS = threading.BoundedSemaphore(
                _bounded_setting("DOCUMENT_PARSE_CONCURRENCY", 2, 1, 4))
        return _WORKER_SLOTS


def _terminate_worker(process):
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    else:
        # Target only this Popen worker's PID and descendants. Use the system
        # executable, no shell/PATH lookup, and no visible console window.
        pid = process.pid
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("Invalid parser process ID")
        taskkill = str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "taskkill.exe")
        try:
            result = subprocess.run(
                [taskkill, "/PID", str(pid), "/T", "/F"], shell=False,
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                timeout=10, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            if result.returncode:
                process.kill()
        except (OSError, subprocess.TimeoutExpired):
            process.kill()


def extract(path: Path, filename=""):
    """Keep untrusted parsers and their allocations outside the API process.

    660 seconds accommodates the existing maximum of 30 pages × 20s OCR.
    The operator may change DOCUMENT_PARSE_TIMEOUT_SECONDS and
    DOCUMENT_PARSE_MEMORY_MB (Linux address-space limit, default 1536 MiB).
    DOCUMENT_PARSE_CONCURRENCY limits active workers per process (default 2).
    Waiting for a slot has its own timeout with the same configured duration.
    """
    path = Path(path).resolve()
    name = filename or path.name
    if Path(name).suffix.lower() not in ALLOWED_EXT or len(name) > 4096:
        raise ValueError("지원하지 않는 첨부 형식입니다.")
    request = json.dumps({"path": str(path), "filename": name}, ensure_ascii=False).encode("utf-8")
    if len(request) > 65536:
        raise ValueError("첨부 파일 이름이 너무 깁니다.")
    timeout = _bounded_setting("DOCUMENT_PARSE_TIMEOUT_SECONDS", 660, 1, 3600)
    # Validate in the parent too; never silently run without the configured cap.
    _bounded_setting("DOCUMENT_PARSE_MEMORY_MB", 1536, 64, 4096)
    slots = _worker_slots()
    if not slots.acquire(timeout=timeout):
        raise ValueError("첨부 추출 대기 시간이 제한을 초과했습니다.")
    try:
        return _run_worker(request, timeout)
    finally:
        slots.release()


def _run_worker(request, timeout):
    env = dict(os.environ, OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1")
    with tempfile.TemporaryFile() as output:
        process = subprocess.Popen(
            [sys.executable, "-I", str(Path(__file__).resolve().with_name("docparse_worker.py"))],
            stdin=subprocess.PIPE, stdout=output, stderr=subprocess.DEVNULL,
            env=env, start_new_session=(os.name == "posix"),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
        try:
            process.communicate(input=request, timeout=timeout)
        except subprocess.TimeoutExpired:
            # OCR launches its own child; stop the worker tree, then reap it.
            _terminate_worker(process)
            process.communicate()
            raise ValueError("첨부 추출 시간이 제한을 초과했습니다.") from None
        if process.returncode:
            raise ValueError("첨부 내용을 읽을 수 없거나 추출 자원 제한을 초과했습니다.")
        output.seek(0)
        raw = output.read(MAX_RESULT_BYTES + 1)
    try:
        if len(raw) > MAX_RESULT_BYTES:
            raise ValueError()
        value = json.loads(raw)
        text, facts = value["text"], value["facts"]
        if (not isinstance(text, str) or len(text) > 40100 or not isinstance(facts, list)
                or len(facts) > 60 or any(not isinstance(f, str) or len(f) > 6000 for f in facts)):
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise ValueError("첨부 추출 결과를 확인할 수 없습니다.") from None
    return text, facts


def _check_xlsx_archive(path):
    # read_only/max_row do not bound sharedStrings, styles or ZIP expansion.
    with ZipFile(path) as archive:
        members = archive.infolist()
        if (len(members) > XLSX_MAX_MEMBERS
                or any(m.file_size > XLSX_MAX_MEMBER_BYTES or m.flag_bits & 1 for m in members)
                or sum(m.file_size for m in members) > XLSX_MAX_EXPANDED_BYTES):
            raise ValueError("스프레드시트의 압축 해제 크기가 제한을 초과했습니다.")


def _pdf_ocr_allowed(page):
    # Include both boxes: the renderer may allocate the original page before
    # cropping it. A small crop must not hide an oversized media box.
    dimensions = [(page.width, page.height)]
    for key in ("mediabox", "cropbox"):
        box = getattr(page, key, None)
        if box is not None:
            dimensions.append((box[2] - box[0], box[3] - box[1]))
    return all(math.isfinite(w) and math.isfinite(h) and w > 0 and h > 0
               and math.ceil(w * PDF_OCR_DPI / 72) * math.ceil(h * PDF_OCR_DPI / 72) <= MAX_PIXELS
               for w, h in dimensions)


def _extract_local(path: Path, filename=""):
    """Worker-only implementation; callers should use extract()."""
    name = filename or path.name
    ext = Path(name).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValueError("지원하지 않는 첨부 형식입니다.")
    lines = []
    def add(location, text):
        for line in str(text or "").splitlines():
            if line.strip():
                lines.append(f"[{name} · {location}] {line.strip()[:1200]}")
    if ext == ".pdf":
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages[:30], 1):
                text = page.extract_text() or ""
                if not text.strip():
                    try:
                        if _pdf_ocr_allowed(page):
                            text = ocr(page.to_image(resolution=PDF_OCR_DPI).original)
                        else:
                            text = "[미추출: 페이지 해상도가 너무 큽니다. 원본 확인과 설명이 필요합니다.]"
                    except Exception:
                        text = "[미추출: 스캔 페이지. 원본 확인과 설명이 필요합니다.]"
                add(f"p.{i}", text)
                for t, rows in enumerate(page.extract_tables()[:4], 1):
                    for r, row in enumerate(rows[:40], 1):
                        add(f"p.{i} 표{t} 행{r}", " | ".join(str(v or "") for v in row))
            if len(pdf.pages) > 30:
                add("범위", "[일부 추출: 첫 30페이지만 분석]")
    elif ext == ".xlsx":
        _check_xlsx_archive(path)
        from openpyxl import load_workbook
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            for sheet in book.worksheets[:8]:
                for i, row in enumerate(sheet.iter_rows(max_row=200, max_col=25, values_only=True), 1):
                    add(f"{sheet.title} 행{i}", " | ".join(str(v) if v is not None else "" for v in row))
        finally:
            book.close()
        add("범위", "[일부 추출: 최대 8시트·200행·25열. 수식은 저장된 계산값을 사용]")
    elif ext in IMAGE_EXT:
        from PIL import Image
        with Image.open(path) as image:
            if image.width * image.height > MAX_PIXELS:
                raise ValueError("이미지 해상도가 너무 큽니다.")
            add("OCR", ocr(image))
            add("주의", "OCR은 문자 추출입니다. 도면의 연결·치수·기호 관계는 사용자 확인이 필요합니다.")
    else:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp949", errors="replace")
        if ext == ".csv":
            for i, row in enumerate(csv.reader(io.StringIO(text)), 1):
                if i > 200:
                    add("범위", "[일부 추출: 첫 200행]")
                    break
                add(f"행{i}", " | ".join(row[:25]))
        else:
            for i, line in enumerate(text.splitlines()[:1200], 1):
                add(f"행{i}", line)
    # Select measurements and problem-bearing lines across the whole document, not just page 1.
    priority = re.compile(r"\d\s*(nm|mm|um|μm|℃|°C|Pa|MPa|rpm|%|ms|V|A)|불량|제약|결함|온도|압력|failure|defect", re.I)
    ranked = sorted(enumerate(lines), key=lambda pair: (not bool(priority.search(pair[1])), pair[0]))
    facts = [line for _, line in sorted(ranked[:60])]
    selected = "\n".join(lines)
    if len(selected) > 40000:
        selected = selected[:40000] + "\n[일부 추출: 텍스트 길이 제한]"
    return selected, facts
