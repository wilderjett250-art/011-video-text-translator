import math
import subprocess
import uuid
from pathlib import Path
from typing import Dict, Iterable, List

import cv2
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .jobs import JobManager
from .models import FrameAsset, ProjectState, TextSegment, VideoMetadata
from .settings import get_font_path
from .storage import media_url, project_dir, write_project


def _ffmpeg_path() -> str:
    return imageio_ffmpeg.get_ffmpeg_exe()


def has_audio_stream(path: Path) -> bool:
    ffmpeg = _ffmpeg_path()
    command = [
        ffmpeg,
        "-hide_banner",
        "-i",
        str(path),
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return "Audio:" in (result.stderr or "")


def probe_video(path: Path) -> VideoMetadata:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    cap.release()
    duration = frame_count / fps if fps > 0 else 0
    return VideoMetadata(
        width=width,
        height=height,
        fps=fps,
        frame_count=frame_count,
        duration_sec=duration,
        has_audio=has_audio_stream(path),
    )


def extract_preview_frames(project: ProjectState, sample_count: int) -> ProjectState:
    source = Path(project.source_path)
    metadata = probe_video(source)
    root = project_dir(project.id)
    frames_dir = root / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise RuntimeError("Cannot open source video")

    picks = _frame_picks(metadata.frame_count, sample_count)
    frames: List[FrameAsset] = []
    for index, frame_index in enumerate(picks):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ok, frame = cap.read()
        if not ok:
            continue
        timestamp = frame_index / metadata.fps if metadata.fps else 0
        target = frames_dir / f"frame_{index:02d}_{timestamp:.2f}s.jpg"
        cv2.imwrite(str(target), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
        frames.append(
            FrameAsset(
                id=target.stem,
                timestamp_sec=timestamp,
                frame_index=frame_index,
                path=str(target),
                url=media_url(target),
            )
        )
    cap.release()
    project.metadata = metadata
    project.frames = frames
    return write_project(project)


def _frame_picks(frame_count: int, sample_count: int) -> List[int]:
    if frame_count <= 1:
        return [0]
    sample_count = max(3, min(sample_count, frame_count))
    picks = {0, frame_count - 1}
    for i in range(1, sample_count - 1):
        ratio = i / (sample_count - 1)
        picks.add(int(round((frame_count - 1) * ratio)))
    return sorted(picks)


def render_video_job(
    job_id: str,
    jobs: JobManager,
    project: ProjectState,
    segments: List[TextSegment],
    output_name: str | None = None,
) -> Dict[str, str]:
    source = Path(project.source_path)
    metadata = project.metadata or probe_video(source)
    root = project_dir(project.id)
    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    safe_name = output_name or f"{Path(project.source_filename).stem}_translated.mp4"
    output = outputs_dir / safe_name
    temp_video = outputs_dir / f"video_only_{uuid.uuid4().hex}.mp4"

    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise RuntimeError("Cannot open source video")
    writer = cv2.VideoWriter(
        str(temp_video),
        cv2.VideoWriter_fourcc(*"mp4v"),
        metadata.fps,
        (metadata.width, metadata.height),
    )
    if not writer.isOpened():
        raise RuntimeError("Cannot create output video")

    sorted_segments = sorted(segments, key=lambda item: item.start_time)
    total = max(metadata.frame_count, 1)
    frame_index = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        timestamp = frame_index / metadata.fps if metadata.fps else 0
        active = [segment for segment in sorted_segments if segment.start_time <= timestamp <= segment.end_time]
        if active:
            frame = draw_overlays(frame, active, metadata.width, metadata.height)
        writer.write(frame)
        frame_index += 1
        if frame_index % 15 == 0:
            jobs.update(
                job_id,
                progress=min(0.95, frame_index / total),
                message=f"已处理 {frame_index}/{total} 帧",
            )
    cap.release()
    writer.release()

    _mux_audio(source, temp_video, output)
    if temp_video.exists():
        temp_video.unlink()
    project.output_path = str(output)
    project.output_url = media_url(output)
    project.segments = segments
    write_project(project)
    return {"path": str(output), "url": media_url(output)}


def draw_overlays(frame_bgr: np.ndarray, segments: Iterable[TextSegment], width: int, height: int) -> np.ndarray:
    image = Image.fromarray(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font_path = str(get_font_path())

    for segment in segments:
        x = int(segment.box.x * width)
        y = int(segment.box.y * height)
        w = int(segment.box.w * width)
        h = int(segment.box.h * height)
        style = segment.style
        text = segment.translated_text.strip()
        if not text:
            continue
        bg = _hex_to_rgba(style.background_color, style.background_opacity)
        radius = min(style.radius, max(0, math.floor(min(w, h) / 2)))
        draw.rounded_rectangle((x, y, x + w, y + h), radius=radius, fill=bg)
        font, lines = _fit_text(text, font_path, style.font_size, w - style.padding * 2, h - style.padding * 2)
        text_draw = ImageDraw.Draw(overlay)
        line_heights = [text_draw.textbbox((0, 0), line, font=font)[3] for line in lines]
        total_text_h = sum(line_heights) + max(0, len(lines) - 1) * 5
        cursor_y = y + max(style.padding, (h - total_text_h) // 2)
        for line in lines:
            bbox = text_draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            if style.align == "left":
                cursor_x = x + style.padding
            elif style.align == "right":
                cursor_x = x + w - style.padding - line_w
            else:
                cursor_x = x + (w - line_w) // 2
            text_draw.text((cursor_x, cursor_y), line, fill=_hex_to_rgba(style.text_color, 1), font=font)
            cursor_y += (bbox[3] - bbox[1]) + 5

    image = Image.alpha_composite(image, overlay).convert("RGB")
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def _fit_text(text: str, font_path: str, start_size: int, max_w: int, max_h: int) -> tuple[ImageFont.FreeTypeFont, List[str]]:
    max_w = max(20, max_w)
    max_h = max(20, max_h)
    size = start_size
    while size >= 12:
        font = ImageFont.truetype(font_path, size=size)
        lines = _wrap_text(text, font, max_w)
        draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        height = 0
        widest = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            widest = max(widest, bbox[2] - bbox[0])
            height += bbox[3] - bbox[1]
        height += max(0, len(lines) - 1) * 5
        if widest <= max_w and height <= max_h:
            return font, lines
        size -= 2
    font = ImageFont.truetype(font_path, size=12)
    return font, _wrap_text(text, font, max_w)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> List[str]:
    draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines: List[str] = []
    current = ""
    tokens = list(text) if any("\u4e00" <= char <= "\u9fff" for char in text) else text.split(" ")
    joiner = "" if tokens and len(tokens[0]) == 1 else " "
    for token in tokens:
        candidate = token if not current else current + joiner + token
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_w or not current:
            current = candidate
        else:
            lines.append(current)
            current = token
    if current:
        lines.append(current)
    return lines or [text]


def _hex_to_rgba(value: str, opacity: float) -> tuple[int, int, int, int]:
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raw = "111111"
    r = int(raw[0:2], 16)
    g = int(raw[2:4], 16)
    b = int(raw[4:6], 16)
    return (r, g, b, int(max(0, min(opacity, 1)) * 255))


def _mux_audio(source: Path, video_only: Path, output: Path) -> None:
    ffmpeg = _ffmpeg_path()
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_only),
        "-i",
        str(source),
        "-map",
        "0:v:0",
        "-map",
        "1:a?",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(output),
    ]
    subprocess.run(command, check=True)

