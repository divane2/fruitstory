"""Programme la vidéo sur TikTok + Facebook via l'API Metricool.
Sans METRICOOL_TOKEN, affiche seulement ce qui serait envoyé (mode test)."""
import json
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import config  # noqa: E402

API = "https://app.metricool.com/api"


def next_slot(hhmm: str) -> str:
    tz = ZoneInfo(config.TZ)
    now = datetime.now(tz)
    h, m = map(int, hhmm.split(":"))
    slot = now.replace(hour=h, minute=m, second=0, microsecond=0)
    if slot <= now + timedelta(minutes=10):   # trop tard pour aujourd'hui -> demain
        slot += timedelta(days=1)
    return slot.strftime("%Y-%m-%dT%H:%M:%S")


def main() -> None:
    url = os.environ["VIDEO_URL"]
    meta = json.load(open("output/meta.json", encoding="utf-8"))
    token = os.getenv("METRICOOL_TOKEN", "")
    user_id, blog_id = os.getenv("METRICOOL_USER_ID", ""), os.getenv("METRICOOL_BLOG_ID", "")
    params = {"userId": user_id, "blogId": blog_id}
    headers = {"X-Mc-Auth": token, "Content-Type": "application/json"}

    # même heure partout, sauf si FACEBOOK_TIME est défini
    plan = [(["tiktok", "facebook"], config.PUBLISH_TIME)]
    if config.FACEBOOK_TIME and config.FACEBOOK_TIME != config.PUBLISH_TIME:
        plan = [(["tiktok"], config.PUBLISH_TIME), (["facebook"], config.FACEBOOK_TIME)]

    media = url
    if token:  # Metricool veut un lien public ; on le "normalise" pour obtenir un mediaId
        try:
            r = requests.get(f"{API}/actions/normalize/image/url", params={**params, "url": url}, headers=headers, timeout=120)
            if r.ok and r.text.strip():
                try:
                    data = r.json()
                    media = data if isinstance(data, str) else (data.get("mediaId") or data.get("id") or url)
                except ValueError:
                    media = r.text.strip().strip('"')
        except requests.RequestException as e:
            print("Normalisation du média impossible, on envoie l'URL directe :", e)

    for networks, hhmm in plan:
        body = {
            "text": meta["text"],
            "providers": [{"network": n} for n in networks],
            "publicationDate": {"dateTime": next_slot(hhmm), "timezone": config.TZ},
            "media": [media],
            "saveExternalMediaFiles": True,
            "autoPublish": True,
        }
        if "tiktok" in networks:
            body["tiktokData"] = {"privacyOption": "PUBLIC_TO_EVERYONE", "disableComment": False,
                                  "disableDuet": False, "disableStitch": False}
        if "facebook" in networks:
            body["facebookData"] = {"type": "REEL"}
        if os.getenv("METRICOOL_EMAIL"):
            body["creatorUserMail"] = os.environ["METRICOOL_EMAIL"]

        if not token:
            print("[TEST] rien envoyé. Requête qui serait faite :\n", json.dumps(body, ensure_ascii=False, indent=2))
            continue
        r = requests.post(f"{API}/v2/scheduler/posts", params=params, headers=headers, json=body, timeout=120)
        print(networks, hhmm, "->", r.status_code, r.text[:500])
        r.raise_for_status()


if __name__ == "__main__":
    main()
