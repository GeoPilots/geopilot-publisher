import hashlib
import hashlib
import math
import os
import subprocess
import tempfile
from pathlib import Path
from random import Random

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except Exception as exc:  # pragma: no cover - dependency guard
    raise RuntimeError(
        "Pillow is required for the particle renderer. "
        "Install it with: pip install Pillow"
    ) from exc


def render_video(script: str, audio_path: str) -> str:
    """
    GeoPilots-themed particle network animation.
    Frames are rendered in Python; ffmpeg encodes and muxes audio.
    Output: artifacts/video.mp4
    """
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    out_path = artifacts_dir / "video.mp4"
    tmp_video = artifacts_dir / "video_tmp.mp4"
    audio_path = str(audio_path)

    ffmpeg = os.getenv("FFMPEG_BIN", "ffmpeg")
    ffprobe = os.getenv("FFPROBE_BIN", "ffprobe")
    W, H, FPS = 1080, 1920, 30

    tracking = 2.0
    duration = _get_audio_duration(ffprobe, audio_path)
    if duration <= 0:
        raise RuntimeError(f"Invalid audio duration from ffprobe: {duration}")

    total_frames = max(1, int(math.ceil(duration * FPS)))

    # Visual tuning (GeoPilots theme)
    particle_count = 64
    max_speed = 0.35
    min_speed = 0.12
    connect_dist = 205.0
    line_max_alpha = 170
    point_min_r = 2.1
    point_max_r = 3.1

    bg_top = (9, 24, 58)
    bg_bottom = (6, 36, 88)
    grid_color = (45, 70, 110, 11)
    point_color = (120, 200, 220, 255)
    line_color = (90, 200, 210)
    keyword_color = (220, 240, 255, 190)

    rng = Random(42)
    particles = []
    for _ in range(particle_count):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        speed = rng.uniform(min_speed, max_speed)
        angle = rng.uniform(0, math.tau)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        r = rng.uniform(point_min_r, point_max_r)
        particles.append([x, y, vx, vy, r])

    base_bg = _build_background(W, H, bg_top, bg_bottom, grid_color)
    keywords = _load_keywords(Path("artifacts") / "keywords.txt")
    keyword_font = _load_keyword_font(size=34)
    keyword_nodes = _init_keyword_nodes(
        script,
        keywords,
        W,
        H,
        keyword_font,
        tracking,
    )

    with tempfile.TemporaryDirectory(prefix="geopilot_frames_") as frames_dir:
        frames_path = Path(frames_dir)
        for idx in range(total_frames):
            frame = base_bg.copy()
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay, "RGBA")

            # Connections
            for i in range(particle_count):
                x1, y1, _, _, _ = particles[i]
                for j in range(i + 1, particle_count):
                    x2, y2, _, _, _ = particles[j]
                    dx = x2 - x1
                    dy = y2 - y1
                    dist = math.hypot(dx, dy)
                    if dist < connect_dist:
                        alpha = int((1.0 - dist / connect_dist) * line_max_alpha)
                        if alpha > 0:
                            draw.line(
                                (x1, y1, x2, y2),
                                fill=(line_color[0], line_color[1], line_color[2], alpha),
                                width=2,
                            )

            # Points
            for i in range(particle_count):
                x, y, vx, vy, r = particles[i]
                draw.ellipse(
                    (x - r, y - r, x + r, y + r),
                    fill=point_color,
                )

                # Update position with soft bounds
                nx = x + vx
                ny = y + vy
                if nx < 0 or nx > W:
                    vx = -vx
                    nx = x + vx
                if ny < 0 or ny > H:
                    vy = -vy
                    ny = y + vy
                particles[i][0] = nx
                particles[i][1] = ny
                particles[i][2] = vx
                particles[i][3] = vy

            # Soft glow to slightly lift particles and edges
            overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.2))
            frame = Image.alpha_composite(frame, overlay)

            # Keyword semantic nodes (persistent, moving, opacity-scheduled)
            if keyword_nodes:
                t = idx / FPS
                text_draw = ImageDraw.Draw(frame, "RGBA")
                _update_keyword_nodes(keyword_nodes, t, idx, W, H, particles)
                for node in keyword_nodes:
                    alpha = node["alpha"]
                    if alpha <= 0:
                        continue
                    color = (keyword_color[0], keyword_color[1], keyword_color[2], alpha)
                    _draw_text_with_tracking(
                        text_draw,
                        (int(node["x"]), int(node["y"])),
                        node["text"],
                        keyword_font,
                        color,
                        tracking,
                    )
                    if node["active"]:
                        ax, ay = particles[node["anchor"]][0], particles[node["anchor"]][1]
                        line_alpha = int(alpha * 0.15)
                        if line_alpha > 0:
                            text_draw.line(
                                (
                                    int(node["x"] + node["w"] / 2),
                                    int(node["y"] + node["h"] / 2),
                                    ax,
                                    ay,
                                ),
                                fill=(90, 200, 210, line_alpha),
                                width=1,
                            )
            frame_path = frames_path / f"frame_{idx:06d}.png"
            frame.save(frame_path)

        _encode_video(ffmpeg, frames_path, FPS, tmp_video)
        _mux_audio(ffmpeg, tmp_video, audio_path, out_path)

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError("video.mp4 was not created or is empty")

    return str(out_path)


def _get_audio_duration(ffprobe: str, audio_path: str) -> float:
    cmd = [
        ffprobe,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nk=1:nw=1",
        audio_path,
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffprobe failed (exit {p.returncode}). stderr:\n{err}")
    try:
        return float(p.stdout.decode("utf-8").strip())
    except ValueError as exc:
        raise RuntimeError("Unable to parse ffprobe duration output") from exc


def _build_background(
    width: int,
    height: int,
    top_rgb: tuple[int, int, int],
    bottom_rgb: tuple[int, int, int],
    grid_rgba: tuple[int, int, int, int],
) -> Image.Image:
    base = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(base, "RGBA")

    for y in range(height):
        t = y / (height - 1)
        r = int(top_rgb[0] * (1 - t) + bottom_rgb[0] * t)
        g = int(top_rgb[1] * (1 - t) + bottom_rgb[1] * t)
        b = int(top_rgb[2] * (1 - t) + bottom_rgb[2] * t)
        draw.line((0, y, width, y), fill=(r, g, b, 255))

    grid_spacing = 120
    for x in range(0, width + 1, grid_spacing):
        draw.line((x, 0, x, height), fill=grid_rgba, width=1)
    for y in range(0, height + 1, grid_spacing):
        draw.line((0, y, width, y), fill=grid_rgba, width=1)

    return base


def _load_keywords(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    keywords = [line for line in lines if line and not line.startswith("#")]
    return keywords


def _assign_keyword_positions(
    width: int,
    height: int,
    keywords: list[str],
    font: ImageFont.ImageFont,
    tracking: float,
    rng: Random,
) -> dict[str, tuple[int, int]]:
    if not keywords:
        return {}

    margin_x = 60
    margin_y = 80
    max_attempts = 30
    padding = 18

    mapping: dict[str, tuple[int, int]] = {}
    boxes: list[tuple[int, int, int, int]] = []

    dummy_img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(dummy_img, "RGBA")

    # Stratified placement across full frame (respect safe margins)
    max_keywords = min(10, len(keywords))
    cols = 4
    rows = 6
    cell_w = (width - 2 * margin_x) / cols
    cell_h = (height - 2 * margin_y) / rows
    cells = [(c, r) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)

    for text, (c, r) in zip(keywords[:max_keywords], cells):
        text_w, text_h = _measure_text(draw, text, font, tracking)
        placed = False
        cell_x0 = margin_x + int(c * cell_w)
        cell_y0 = margin_y + int(r * cell_h)
        cell_x1 = margin_x + int((c + 1) * cell_w)
        cell_y1 = margin_y + int((r + 1) * cell_h)
        for _ in range(max_attempts):
            x = rng.randint(cell_x0, max(cell_x0, cell_x1 - text_w))
            y = rng.randint(cell_y0, max(cell_y0, cell_y1 - text_h))
            x, y = _clamp_text_position(
                draw, (x, y), text, font, tracking, width, height, margin_x, margin_y
            )
            box = (x - padding, y - padding, x + text_w + padding, y + text_h + padding)
            if all(
                box[2] <= b[0]
                or box[0] >= b[2]
                or box[3] <= b[1]
                or box[1] >= b[3]
                for b in boxes
            ):
                mapping[text] = (x, y)
                boxes.append(box)
                placed = True
                break

        if not placed:
            # Skip if we cannot place without overlap.
            continue

    return mapping


def _init_keyword_nodes(
    script: str,
    keywords: list[str],
    width: int,
    height: int,
    font: ImageFont.ImageFont,
    tracking: float,
) -> list[dict]:
    if not keywords:
        return []

    seed = int(hashlib.sha256(script.encode("utf-8")).hexdigest()[:8], 16)
    rng = Random(seed)
    positions = _assign_keyword_positions(width, height, keywords, font, tracking, rng)
    if not positions:
        return []

    dummy = ImageDraw.Draw(Image.new("RGBA", (width, height)))
    nodes: list[dict] = []
    for text in keywords[:10]:
        pos = positions.get(text)
        if pos is None:
            continue
        w, h = _measure_text(dummy, text, font, tracking)
        vx = rng.uniform(-0.6, 0.6)
        vy = rng.uniform(-0.3, 0.3)
        base_opacity = rng.uniform(0.13, 0.15)
        peak_opacity = rng.uniform(0.70, 0.74)
        nodes.append(
            {
                "text": text,
                "x": float(pos[0]),
                "y": float(pos[1]),
                "vx": vx,
                "vy": vy,
                "w": w,
                "h": h,
                "base": base_opacity,
                "peak": peak_opacity,
                "alpha": int(base_opacity * 255),
                "active": False,
                "phase": rng.uniform(0.0, 2.0),
                "hold": rng.uniform(2.5, 4.0),
                "gap": rng.uniform(0.8, 1.6),
                "anchor": None,
            }
        )
    return nodes


def _update_keyword_nodes(
    nodes: list[dict],
    t: float,
    frame_idx: int,
    width: int,
    height: int,
    particles: list[list[float]],
) -> None:
    if not nodes:
        return

    margin_x = 60
    margin_y = 80
    for node in nodes:
        fade = 0.6
        cycle = fade * 2 + node["hold"] + node["gap"]
        local = (t + node["phase"]) % cycle
        if local < fade:
            x = local / fade
            eased = 0.5 - 0.5 * math.cos(math.pi * x)
            target = node["base"] + (node["peak"] - node["base"]) * eased
            node["active"] = True
        else:
            local -= fade
            if local < node["hold"]:
                target = node["peak"]
                node["active"] = True
            else:
                local -= node["hold"]
                if local < fade:
                    x = 1.0 - local / fade
                    eased = 0.5 - 0.5 * math.cos(math.pi * x)
                    target = node["base"] + (node["peak"] - node["base"]) * eased
                    node["active"] = False
                else:
                    target = node["base"]
                    node["active"] = False

        target = max(node["base"], target)
        node["alpha"] = int(max(0.0, min(1.0, target)) * 255)

        node["x"] += node["vx"]
        node["y"] += node["vy"]

        if abs(node["vx"]) < 0.15:
            node["vx"] = math.copysign(0.15, node["vx"] if node["vx"] != 0 else 1.0)
        if abs(node["vy"]) < 0.08:
            node["vy"] = math.copysign(0.08, node["vy"] if node["vy"] != 0 else 1.0)

        min_x = margin_x
        max_x = width - margin_x - node["w"]
        min_y = margin_y
        max_y = height - margin_y - node["h"]
        if node["x"] < min_x:
            node["x"] = max_x
        elif node["x"] > max_x:
            node["x"] = min_x
        if node["y"] < min_y:
            node["y"] = max_y
        elif node["y"] > max_y:
            node["y"] = min_y

        node["anchor"] = _nearest_particle_index(
            node["x"] + node["w"] / 2, node["y"] + node["h"] / 2, particles
        )

    if frame_idx % 10 == 0:
        for i in range(len(nodes)):
            a = nodes[i]
            for j in range(i + 1, len(nodes)):
                b = nodes[j]
                if _boxes_overlap(a, b, pad=6):
                    dx = (a["x"] + a["w"] / 2) - (b["x"] + b["w"] / 2)
                    dy = (a["y"] + a["h"] / 2) - (b["y"] + b["h"] / 2)
                    dist = math.hypot(dx, dy) or 1.0
                    push = 0.15
                    cap = 1.0
                    ax = max(-cap, min(cap, (dx / dist) * push))
                    ay = max(-cap, min(cap, (dy / dist) * push))
                    bx = max(-cap, min(cap, (dx / dist) * push))
                    by = max(-cap, min(cap, (dy / dist) * push))
                    a["x"] += ax
                    a["y"] += ay
                    b["x"] -= bx
                    b["y"] -= by


def _boxes_overlap(a: dict, b: dict, pad: int = 0) -> bool:
    ax1, ay1 = a["x"] - pad, a["y"] - pad
    ax2, ay2 = a["x"] + a["w"] + pad, a["y"] + a["h"] + pad
    bx1, by1 = b["x"] - pad, b["y"] - pad
    bx2, by2 = b["x"] + b["w"] + pad, b["y"] + b["h"] + pad
    return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)


def _nearest_particle_index(x: float, y: float, particles: list[list[float]]) -> int | None:
    if not particles:
        return None
    best_idx = 0
    best_dist = float("inf")
    for i, p in enumerate(particles):
        dx = p[0] - x
        dy = p[1] - y
        dist = dx * dx + dy * dy
        if dist < best_dist:
            best_dist = dist
            best_idx = i
    return best_idx


def _load_keyword_font(size: int) -> ImageFont.ImageFont:
    candidates = [
        os.getenv("GEOPILOT_FONT", ""),
        "/System/Library/Fonts/SFNSDisplay-Medium.otf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Helvetica Neue Medium.ttf",
        "/Library/Fonts/HelveticaNeue.ttf",
    ]
    for path in candidates:
        if path and Path(path).exists():
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_text_with_tracking(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int, int],
    tracking: float,
) -> None:
    x, y = position
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        try:
            advance = font.getlength(ch)
        except AttributeError:
            advance = font.getsize(ch)[0]
        x += advance + tracking


def _clamp_text_position(
    draw: ImageDraw.ImageDraw,
    position: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    tracking: float,
    width: int,
    height: int,
    margin_x: int = 60,
    margin_y: int = 80,
) -> tuple[int, int]:
    x, y = position
    text_w, text_h = _measure_text(draw, text, font, tracking)
    x = max(margin_x, min(x, width - margin_x - text_w))
    y = max(margin_y, min(y, height - margin_y - text_h))
    return int(x), int(y)


def _measure_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    tracking: float,
) -> tuple[int, int]:
    if not text:
        return 0, 0
    total_w = 0.0
    max_h = 0.0
    for ch in text:
        try:
            bbox = draw.textbbox((0, 0), ch, font=font)
            ch_w = bbox[2] - bbox[0]
            ch_h = bbox[3] - bbox[1]
        except Exception:
            ch_w, ch_h = font.getsize(ch)
        total_w += ch_w + tracking
        max_h = max(max_h, ch_h)
    total_w = max(0.0, total_w - tracking)
    return int(math.ceil(total_w)), int(math.ceil(max_h))

def _encode_video(ffmpeg: str, frames_dir: Path, fps: int, out_path: Path) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-framerate",
        str(fps),
        "-i",
        str(frames_dir / "frame_%06d.png"),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        str(out_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg encode failed (exit {p.returncode}). stderr:\n{err}")


def _mux_audio(ffmpeg: str, video_path: Path, audio_path: str, out_path: Path) -> None:
    cmd = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(video_path),
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        str(out_path),
    ]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        err = p.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"ffmpeg mux failed (exit {p.returncode}). stderr:\n{err}")
