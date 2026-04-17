"""
기존 Qdrant 포인트들의 sort_date 를 실제 EXIF DateTimeOriginal 기반으로 재계산하는
일회성 마이그레이션 스크립트.

배경: 과거 vector_indexer.py 가 EXIF 의 일(day) 정보를 버리고 월까지만 파싱해
      모든 사진이 해당 월 1일(YYYYMM01)로 저장되는 버그가 있었다.
목적: 현재 Qdrant 에 존재하는 26000여 장의 사진에 대해 EXIF 를 다시 읽어
      sort_date 를 올바른 YYYYMMDD 값으로 복구한다.

사용:
    docker exec gumaphoto_celery python Scripts/migrate_sort_date_from_exif.py
    docker exec gumaphoto_celery python Scripts/migrate_sort_date_from_exif.py --dry-run
    docker exec gumaphoto_celery python Scripts/migrate_sort_date_from_exif.py --year 2026

옵션:
  --dry-run     실제 업데이트 없이 변경 예정 건수만 출력
  --year YYYY   특정 연도의 사진만 처리 (기본: 전체)
  --batch N     EXIF 배치 크기 (기본: 50)
"""

import argparse
import json
import os
import subprocess
import sys
import time

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, Range

QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
COLLECTION_NAME = "gumaphoto_hybrid_kr"


def exif_sort_date(filepaths):
    """exiftool 배치 호출로 여러 파일의 YYYYMMDD sort_date 를 한 번에 추출."""
    if not filepaths:
        return {}
    try:
        cmd = ["exiftool", "-j", "-DateTimeOriginal", "-CreateDate"] + filepaths
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if res.returncode != 0 or not res.stdout.strip():
            return {}
        parsed = json.loads(res.stdout)
    except Exception as e:
        print(f"  [!] exiftool 배치 호출 실패: {e}")
        return {}

    out = {}
    for d in parsed:
        fpath = d.get("SourceFile")
        if not fpath:
            continue
        date_val = d.get("DateTimeOriginal") or d.get("CreateDate")
        if not date_val:
            continue
        raw_dt = str(date_val).split(" ")[0]
        parts = raw_dt.split(":")
        if len(parts) < 3:
            continue
        try:
            y, m, dd = int(parts[0]), int(parts[1]), int(parts[2])
            out[fpath] = y * 10000 + m * 100 + dd
        except ValueError:
            continue
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--year", type=int, default=None)
    ap.add_argument("--batch", type=int, default=50)
    args = ap.parse_args()

    print(f"[*] Qdrant 접속: {QDRANT_URL}")
    client = QdrantClient(url=QDRANT_URL)

    scroll_filter = None
    if args.year:
        scroll_filter = Filter(must=[FieldCondition(
            key="sort_date",
            range=Range(gte=args.year * 10000, lte=args.year * 10000 + 1231)
        )])
        print(f"[*] 대상: {args.year}년 사진만")
    else:
        print(f"[*] 대상: 전체")
    print(f"[*] 모드: {'DRY-RUN' if args.dry_run else 'LIVE UPDATE'}")

    total_scanned = 0
    total_would_change = 0
    total_updated = 0
    total_skip_no_file = 0
    total_skip_no_exif = 0

    offset = None
    t_start = time.time()
    while True:
        points, offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=scroll_filter,
            limit=args.batch,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        if not points:
            break

        fp_to_pt = {}
        for pt in points:
            total_scanned += 1
            p = pt.payload or {}
            fpath = p.get("filepath")
            if not fpath or not os.path.exists(fpath):
                total_skip_no_file += 1
                continue
            fp_to_pt[fpath] = pt

        new_sort_dates = exif_sort_date(list(fp_to_pt.keys()))

        for fpath, pt in fp_to_pt.items():
            new_sd = new_sort_dates.get(fpath)
            if new_sd is None:
                total_skip_no_exif += 1
                continue
            old_sd = (pt.payload or {}).get("sort_date", 0)
            if new_sd == old_sd:
                continue
            total_would_change += 1
            if not args.dry_run:
                try:
                    client.set_payload(
                        collection_name=COLLECTION_NAME,
                        payload={"sort_date": new_sd},
                        points=[pt.id],
                    )
                    total_updated += 1
                except Exception as e:
                    print(f"  [!] 업데이트 실패 {pt.id}: {e}")

        if total_scanned % 500 < args.batch:
            elapsed = time.time() - t_start
            print(f"  ... 진행 {total_scanned}장 ({elapsed:.1f}s), 변경 예정={total_would_change}, 실제 변경={total_updated}")

        if offset is None:
            break

    elapsed = time.time() - t_start
    print("")
    print("=" * 60)
    print(f"[✅ 완료] 총 스캔 {total_scanned}장 / 소요 {elapsed:.1f}s")
    print(f"  - 변경 예정: {total_would_change}장")
    print(f"  - 실제 업데이트: {total_updated}장")
    print(f"  - 스킵(파일 없음): {total_skip_no_file}장")
    print(f"  - 스킵(EXIF 날짜 없음): {total_skip_no_exif}장")
    print("=" * 60)
    if args.dry_run:
        print("[!] DRY-RUN 이었으므로 실제 Qdrant 업데이트는 하지 않았습니다.")
    else:
        print("[!] 타임라인 캐시도 재생성해야 메인 화면에 반영됩니다:")
        print("    curl -X POST http://localhost:8085/api/rebuild_cache")


if __name__ == "__main__":
    sys.exit(main())
