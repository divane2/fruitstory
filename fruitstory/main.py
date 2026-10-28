"""Génère la vidéo du jour : scénario -> voix -> images -> montage. Résultat dans output/."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import config                      # noqa: E402
import images                      # noqa: E402
import story as story_mod          # noqa: E402
import tts                         # noqa: E402
import video                       # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
HISTORY = os.path.join(ROOT, "data", "history.json")
OUT = os.path.join(ROOT, "output")
WORK = os.path.join(OUT, "work")


def load_history() -> list[str]:
    try:
        return json.load(open(HISTORY, encoding="utf-8"))
    except Exception:
        return []


def narrate(story: dict):
    """Voix off de toutes les scènes ; renvoie les durées."""
    durs = []
    for i, sc in enumerate(story["scenes"]):
        path = os.path.join(WORK, f"a{i:02d}.mp3")
        durs.append(tts.synth(sc["narration"], path))
    return durs


def main() -> None:
    os.makedirs(WORK, exist_ok=True)
    history = load_history()
    theme = os.getenv("THEME", "").strip()

    # 1) scénario + voix ; on recommence si la vidéo n'est pas dans la fenêtre de durée voulue
    story, durs = None, []
    for attempt in range(1, 4):
        story = story_mod.generate_story(history, theme)
        durs = narrate(story)
        total = sum(d + config.SCENE_PAD for d in durs)
        print(f"Essai {attempt} : '{story['title']}' -> {total:.1f}s")
        if config.MIN_SECONDS <= total <= config.MAX_SECONDS:
            break
        if attempt == 3:
            raise SystemExit(f"Durée hors limites après 3 essais ({total:.1f}s) : abandon.")

    # 2) images
    ok_count = 0
    for i, sc in enumerate(story["scenes"]):
        p = story_mod.image_prompt(story, sc)
        ok = images.make_image(p, os.path.join(WORK, f"i{i:02d}.jpg"), i, seed=int(time.time()) % 100000 + i)
        ok_count += ok
        print(f"Image {i + 1}/{len(story['scenes'])} {'OK' if ok else 'REPLI'}")
    if ok_count < len(story["scenes"]) / 2:
        raise SystemExit("Trop d'images ont échoué : on ne publie pas une vidéo vide.")

    # 3) clips + sous-titres + assemblage
    clips, subs, t = [], [], 0.0
    for i, sc in enumerate(story["scenes"]):
        dur = durs[i] + config.SCENE_PAD
        clip = os.path.join(WORK, f"c{i:02d}.mp4")
        video.scene_clip(os.path.join(WORK, f"i{i:02d}.jpg"), os.path.join(WORK, f"a{i:02d}.mp3"), dur, i, clip)
        clips.append(clip)
        subs.append({"text": sc["narration"], "start": t, "speech": durs[i]})
        t += dur
    ass = os.path.join(WORK, "subs.ass")
    video.build_ass(subs, ass)
    final = os.path.join(OUT, "video.mp4")
    video.assemble(clips, ass, final, WORK)

    tags = " ".join(story.get("hashtags", []))
    meta = {
        "title": story["title"],
        "caption": story["caption"],
        "hashtags": story.get("hashtags", []),
        "text": f"{story['caption']}\n\n{tags}".strip(),
        "duration": round(t, 1),
    }
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    history.append(story["title"])
    json.dump(history[-200:], open(HISTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"Vidéo prête : {final} ({t:.1f}s)")


if __name__ == "__main__":
    main()
