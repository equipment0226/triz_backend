"""Contradiction_Matrix_V11.pdf 에서 Altshuller 39x39 행렬을 추출해 JSON으로 저장한다.

PDF는 셀마다 숫자를 2~3줄로 잘게 쪼개 그리므로, 텍스트 추출 대신
**문자 좌표를 격자에 투영**해 셀을 복원한다.

사용:  python scripts/import_matrix.py [--dry] [--pdf 경로]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PDF = ROOT / "docs" / "Contradiction_Matrix_V11.pdf"
OUT = Path(__file__).resolve().parents[1] / "triz" / "knowledge" / "matrix_39x39.json"
N = 39


def column_grid(page) -> list[float]:
    """상단 헤더의 1~39 숫자 위치로 열 경계를 잡는다."""
    words = [w for w in page.extract_words() if w["text"].isdigit()]
    bands: dict[int, list] = {}
    for w in words:
        bands.setdefault(round(w["top"] / 3) * 3, []).append(w)
    for _, line in sorted(bands.items()):
        seq = sorted(line, key=lambda w: w["x0"])
        labels = [w["text"] for w in seq]
        if labels[:N] == [str(i) for i in range(1, N + 1)]:
            centers = [(w["x0"] + w["x1"]) / 2 for w in seq[:N]]
            pitch = (centers[-1] - centers[0]) / (N - 1)
            return [centers[0] - pitch / 2 + pitch * i for i in range(N + 1)]
    raise SystemExit("열 헤더(1~39)를 찾지 못했습니다.")


def row_grid(page, x_left: float) -> list[float]:
    """행 번호 열(격자 왼쪽)의 숫자 위치로 행 경계를 잡는다."""
    labels = [w for w in page.extract_words()
              if w["text"].isdigit() and w["x1"] < x_left and 1 <= int(w["text"]) <= N]
    by_value: dict[int, float] = {}
    for w in labels:
        by_value.setdefault(int(w["text"]), (w["top"] + w["bottom"]) / 2)
    if len(by_value) < N:
        raise SystemExit(f"행 번호를 {len(by_value)}개만 찾았습니다.")
    centers = [by_value[i] for i in range(1, N + 1)]
    pitch = (centers[-1] - centers[0]) / (N - 1)
    return [centers[0] - pitch / 2 + pitch * i for i in range(N + 1)]


def bucket(value: float, edges: list[float]) -> int | None:
    if value < edges[0] or value >= edges[-1]:
        return None
    lo, hi = 0, len(edges) - 1
    while lo < hi - 1:
        mid = (lo + hi) // 2
        if value < edges[mid]:
            hi = mid
        else:
            lo = mid
    return lo


def extract(page) -> dict[str, dict[str, list[int]]]:
    xs = column_grid(page)
    ys = row_grid(page, xs[0])

    grid: dict[tuple[int, int], list[tuple[int, float, str]]] = {}
    for ch in page.chars:
        text = ch["text"]
        if not (text.isdigit() or text == ","):
            continue
        cx = (ch["x0"] + ch["x1"]) / 2
        cy = (ch["top"] + ch["bottom"]) / 2
        col, row = bucket(cx, xs), bucket(cy, ys)
        if col is None or row is None:
            continue
        grid.setdefault((row, col), []).append((round(ch["top"] / 2), ch["x0"], text))

    cells: dict[str, dict[str, list[int]]] = {}
    for (row, col), chars in grid.items():
        if row == col:
            continue
        chars.sort(key=lambda t: (t[0], t[1]))
        raw = "".join(t[2] for t in chars)
        ids, seen = [], set()
        for part in raw.split(","):
            part = part.strip()
            if not part.isdigit():
                continue
            pid = int(part)
            if 1 <= pid <= 40 and pid not in seen:
                seen.add(pid)
                ids.append(pid)
        if ids:
            cells.setdefault(str(row + 1), {})[str(col + 1)] = ids
    return cells


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=str(DEFAULT_PDF))
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    pdf = Path(args.pdf)
    if not pdf.exists():
        print(f"PDF를 찾을 수 없습니다: {pdf}")
        return 2

    try:
        import pdfplumber
    except ImportError:
        print("pdfplumber 가 필요합니다:  python -m pip install pdfplumber")
        return 2

    with pdfplumber.open(str(pdf)) as doc:
        cells = extract(doc.pages[0])

    filled = sum(len(v) for v in cells.values())
    print(f"행 {len(cells)}개 / 셀 {filled}개 (대각선 제외 최대 1482)")
    missing = [i for i in range(1, N + 1) if str(i) not in cells]
    if missing:
        print(f"비어 있는 개선 파라미터 행: {missing}")

    # 널리 알려진 셀 값으로 교차 검증
    known = {("1", "3"): [15, 8, 29, 34], ("1", "10"): [8, 10, 18, 37],
             ("9", "27"): [11, 35, 27, 28], ("10", "1"): [8, 1, 37, 18],
             ("39", "38"): [5, 12, 35, 26]}
    for (i, j), expected in known.items():
        got = cells.get(i, {}).get(j)
        mark = "OK " if got == expected else "DIFF"
        print(f"  [{mark}] ({i},{j}) 기대 {expected} / 추출 {got}")

    if args.dry:
        for k in ["1", "9", "39"]:
            row = cells.get(k, {})
            sample = dict(list(row.items())[:8])
            print(f"  {k}행({len(row)}칸): {json.dumps(sample, ensure_ascii=False)}")
        return 0

    data = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {}
    data["cells"] = cells
    data["source"] = "Contradiction_Matrix_V11.pdf (Altshuller 39x39)"
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"저장: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
