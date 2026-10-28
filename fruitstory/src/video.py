"""Montage vidéo 1080x1920 avec ffmpeg : image animée + voix off par scène, sous-titres incrustés, musique optionnelle."""
import glob
import os
import random
import re
import subprocess

import config


def _run(cmd, cwd=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("ffmpeg a échoué :\n" + r.stderr[-2000:])


def scene_clip(img: str, audio: str, dur: float, idx: int, out: str) -> None:
    frames = max(1, int(round(dur * config.FPS)))
    if idx % 2 == 0:   # zoom avant / zoom arrière en alternance
        z = f"1+0.15*on/{frames}"
    else:
        z = f"1.15-0.15*on/{frames}"
    vf = (
        "scale=1620:2880:force_original_aspect_ratio=increase,crop=1620:2880,"
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={config.W}x{config.H}:fps={config.FPS},"
        "format=yuv420p"
    )
    _run([
        "ffmpeg", "-y", "-i", img, "-i", audio,
        "-vf", vf, "-af", "apad", "-t", f"{dur:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", out,
    ])


def _ts(t: float) -> str:
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_ass(scenes: list[dict], path: str, words_per_chunk: int = 3) -> None:
    """scenes : [{'text', 'start', 'speech'}] ; les sous-titres sont répartis selon la longueur des mots."""
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {config.W}
PlayResY: {config.H}
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,DejaVu Sans,78,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,7,2,2,60,60,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for sc in scenes:
        words = re.sub(r"[{}\\]", "", sc["text"]).split()
        chunks = [" ".join(words[i:i + words_per_chunk]) for i in range(0, len(words), words_per_chunk)]
        total = sum(len(c) for c in chunks) or 1
        t = sc["start"]
        for c in chunks:
            d = sc["speech"] * len(c) / total
            lines.append(f"Dialogue: 0,{_ts(t)},{_ts(t + d)},Default,,0,0,0,,{c}")
            t += d
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(lines) + "\n")


def assemble(clips: list[str], ass: str, out: str, workdir: str) -> None:
    listing = os.path.join(workdir, "clips.txt")
    with open(listing, "w") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    joined = os.path.join(workdir, "joined.mp4")
    _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy", joined])

    music = glob.glob(os.path.join(os.path.dirname(__file__), "..", "assets", "music", "*.mp3"))
    sub = f"ass={os.path.basename(ass)}"
    cmd = ["ffmpeg", "-y", "-i", os.path.basename(joined)]
    if music:
        cmd += ["-stream_loop", "-1", "-i", os.path.abspath(random.choice(music)),
                "-filter_complex",
                f"[0:v]{sub}[v];[1:a]volume=0.10[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=0[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", sub]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", os.path.abspath(out)]
    _run(cmd, cwd=workdir)   # cwd = dossier de travail : évite les soucis de chemins dans le filtre ass
