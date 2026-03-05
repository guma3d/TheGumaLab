import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path


def extract_youtube_video_id(url: str) -> str:
    if not url:
        return ""
    patterns = [
        r"(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)",
        r"v=([^&\n?#]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def _pick_single(files):
    if len(files) == 1:
        return files[0]
    return None


def plan_file_renames_scan(dir_path: Path, video_id: str, preferred_base: str = ""):
    renames = []
    conflicts = []

    def prefer_or_single(preferred_name, candidates, label):
        if preferred_name:
            preferred_path = dir_path / preferred_name
            if preferred_path.exists():
                return preferred_path
        if len(candidates) == 1:
            return candidates[0]
        if len(candidates) > 1:
            conflicts.append(f"{label} has multiple candidates in {dir_path}")
        return None

    # mp4
    if not (dir_path / f"{video_id}.mp4").exists():
        candidates = [
            p for p in dir_path.glob("*.mp4")
            if p.is_file() and p.name != f"{video_id}.mp4"
        ]
        src = prefer_or_single(f"{preferred_base}.mp4" if preferred_base else "", candidates, "mp4")
        if src:
            renames.append((src.name, f"{video_id}.mp4"))

    # mp3 (exclude chunks)
    if not (dir_path / f"{video_id}.mp3").exists():
        candidates = [
            p for p in dir_path.glob("*.mp3")
            if p.is_file() and "_chunk" not in p.name and p.name != f"{video_id}.mp3"
        ]
        src = prefer_or_single(f"{preferred_base}.mp3" if preferred_base else "", candidates, "mp3")
        if src:
            renames.append((src.name, f"{video_id}.mp3"))

    # srt
    if not (dir_path / f"{video_id}.srt").exists():
        candidates = [
            p for p in dir_path.glob("*.srt")
            if p.is_file() and p.name != f"{video_id}.srt"
        ]
        src = prefer_or_single(f"{preferred_base}.srt" if preferred_base else "", candidates, "srt")
        if src:
            renames.append((src.name, f"{video_id}.srt"))

    # detail html
    if not (dir_path / f"{video_id}.html").exists():
        candidates = [
            p for p in dir_path.glob("*.html")
            if p.is_file()
            and not p.name.endswith("-summary.html")
            and p.name != f"{video_id}.html"
        ]
        src = prefer_or_single(f"{preferred_base}.html" if preferred_base else "", candidates, "html")
        if src:
            renames.append((src.name, f"{video_id}.html"))

    # summary html
    if not (dir_path / f"{video_id}-summary.html").exists():
        candidates = [
            p for p in dir_path.glob("*-summary.html")
            if p.is_file() and p.name != f"{video_id}-summary.html"
        ]
        src = prefer_or_single(
            f"{preferred_base}-summary.html" if preferred_base else "",
            candidates,
            "summary html",
        )
        if src:
            renames.append((src.name, f"{video_id}-summary.html"))

    return renames, conflicts


def main():
    parser = argparse.ArgumentParser(
        description="Migrate output folders/files and task_status.json to use YouTube video id."
    )
    parser.add_argument(
        "--task-status",
        default="data/task_status.json",
        help="Path to task_status.json",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory containing task folders",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (default is dry-run)",
    )
    args = parser.parse_args()

    task_status_path = Path(args.task_status)
    output_dir = Path(args.output_dir)

    data = json.loads(task_status_path.read_text(encoding="utf-8"))

    planned_dirs = []
    planned_files = []  # (dir_target, old_name, new_name)
    conflicts = []
    skipped = []

    for task_id, task in data.items():
        if task.get("status") != "completed":
            skipped.append(f"{task_id}: not completed")
            continue

        url = task.get("url", "")
        video_id = extract_youtube_video_id(url)
        if not video_id:
            skipped.append(f"{task_id}: no video id")
            continue

        result = task.get("result", {})
        old_title = result.get("title") or task.get("safe_title")
        if not old_title:
            skipped.append(f"{task_id}: no title")
            continue

        old_dir = output_dir / old_title
        new_dir = output_dir / video_id

        if old_title != video_id and old_dir.exists():
            if new_dir.exists() and old_dir.resolve() != new_dir.resolve():
                conflicts.append(f"{task_id}: dir exists {new_dir}")
                continue
            planned_dirs.append((old_dir, new_dir))

        # Plan file renames in the target dir (after possible dir rename)
        dir_for_scan = new_dir if new_dir.exists() else old_dir
        if dir_for_scan.exists():
            renames, file_conflicts = plan_file_renames_scan(
                dir_for_scan, video_id, preferred_base=old_title
            )
            for old_name, new_name in renames:
                planned_files.append((new_dir if (old_title != video_id) else dir_for_scan, old_name, new_name))
            conflicts.extend([f"{task_id}: {c}" for c in file_conflicts])
        else:
            skipped.append(f"{task_id}: missing dir {dir_for_scan}")

        # Update task status fields
        result["title"] = video_id
        if task.get("video_title") and not result.get("original_title"):
            result["original_title"] = task.get("video_title")
        task["safe_title"] = video_id
        result["video_path"] = str(new_dir / f"{video_id}.mp4")
        result["html_path"] = str(new_dir / f"{video_id}.html")
        result["summary_html_path"] = str(new_dir / f"{video_id}-summary.html")

    if args.apply:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = task_status_path.with_suffix(f".json.bak.{timestamp}")
        shutil.copy2(task_status_path, backup_path)

        # Apply directory renames
        for src, dst in planned_dirs:
            if src.exists() and not dst.exists():
                src.rename(dst)

        # Apply file renames
        for dir_target, old_name, new_name in planned_files:
            src = dir_target / old_name
            dst = dir_target / new_name
            if src.exists() and not dst.exists():
                src.rename(dst)

        task_status_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        print(f"Backup: {backup_path}")
        print(f"Updated: {task_status_path}")
    else:
        print("Dry run only. Use --apply to perform changes.")

    print(f"Planned dir renames: {len(planned_dirs)}")
    print(f"Planned file renames: {len(planned_files)}")
    print(f"Conflicts: {len(conflicts)}")
    print(f"Skipped: {len(skipped)}")

    if conflicts:
        print("\nConflicts:")
        for item in conflicts:
            print(f"- {item}")
    if skipped:
        print("\nSkipped:")
        for item in skipped:
            print(f"- {item}")


if __name__ == "__main__":
    main()
