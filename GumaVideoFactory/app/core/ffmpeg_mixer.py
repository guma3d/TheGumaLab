import subprocess
import shutil
import logging
from pathlib import Path
from typing import List, Optional
import imageio_ffmpeg

logger = logging.getLogger(__name__)

def get_ffmpeg_bin() -> str:
    """시스템 ffmpeg 우선 사용, 없으면 imageio-ffmpeg 번들 경로 반환"""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

def concatenate_clips_with_audio(
    clip_paths: List[Path],
    audio_path: Optional[Path],
    output_path: Path,
    aspect_ratio: str = "9:16"
) -> Path:
    """비디오 클립들을 순서대로 결합하고 오디오를 입혀 최종 비디오를 생성합니다."""
    ffmpeg_bin = get_ffmpeg_bin()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 1. Concat 파일 목록 작성
    concat_list_file = output_path.parent / f"concat_{output_path.stem}.txt"
    with open(concat_list_file, "w", encoding="utf-8") as f:
        for p in clip_paths:
            escaped_path = str(p.resolve()).replace("\\", "/")
            f.write(f"file '{escaped_path}'\n")

    # 2. FFmpeg 명령어 구성
    cmd = [
        ffmpeg_bin,
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_list_file),
    ]

    if audio_path and audio_path.exists():
        cmd.extend([
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
        ])
    else:
        cmd.extend([
            "-c:v", "copy",
        ])

    cmd.append(str(output_path))

    logger.info(f"Running FFmpeg: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Concat 임시 파일 삭제
    if concat_list_file.exists():
        concat_list_file.unlink()

    if result.returncode != 0:
        logger.error(f"FFmpeg failed: {result.stderr}")
        raise RuntimeError(f"FFmpeg rendering failed: {result.stderr}")

    logger.info(f"Final video rendered successfully: {output_path}")
    return output_path
