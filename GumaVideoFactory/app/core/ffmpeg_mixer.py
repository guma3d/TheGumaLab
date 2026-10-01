import subprocess
import shutil
import logging
from pathlib import Path
from typing import List, Optional
import imageio_ffmpeg

logger = logging.getLogger(__name__)


def render_product_still(image_path: Path, output_path: Path, aspect_ratio: str, duration: int = 4) -> Path:
    """최종 실제 상품 이미지는 생성 모델로 변형하지 않고 원본을 영상화."""
    width, height = (720, 1280) if aspect_ratio == "9:16" else (1280, 720)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([
        get_ffmpeg_bin(), "-y", "-loop", "1", "-i", str(image_path), "-t", str(duration),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1",
        "-r", "24", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path),
    ], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("실제 상품 이미지 영상화에 실패했습니다.")
    return output_path

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
            "-af", "apad",
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
