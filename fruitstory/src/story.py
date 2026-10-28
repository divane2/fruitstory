"""Génération du scénario avec Claude : histoire drama/amusante racontée par des fruits."""
import json
import os
import re

from anthropic import Anthropic

import config

SYSTEM = """Tu écris des scénarios de vidéos verticales (TikTok / Facebook Reels) en français.
Format : histoires réelles et amusantes de la vie quotidienne, ton drama / anecdote qui accroche,
racontées par des avatars de fruits. Les personnages sont des fruits (jamais de vraies personnes
identifiables). Pas de contenu sexuel, violent, haineux ni de désinformation. Reste fun et tout public.
Tu réponds UNIQUEMENT avec un objet JSON valide, sans texte autour."""

PROMPT = """Écris le scénario d'une vidéo de 70 à 85 secondes.

Contraintes :
- Narration totale en français : entre 200 et 240 mots (voix off unique, ton vivant).
- Première phrase = accroche forte qui donne envie de rester. Fin = chute + question qui pousse à commenter.
- Entre 12 et 16 scènes ; chaque scène a une narration de 10 à 20 mots.
- 2 ou 3 personnages fruits maximum, avec une apparence fixe décrite EN ANGLAIS (pour garder la cohérence des images).
{theme}
Thèmes déjà traités (ne pas répéter) :
{history}

Schéma JSON exact :
{{
  "title": "titre court",
  "caption": "légende TikTok/Facebook en français, 150 caractères max, sans hashtags",
  "hashtags": ["#mot1", "#mot2", "#mot3", "#mot4", "#mot5"],
  "characters": [{{"name": "Prénom", "look": "description visuelle en anglais, ex: a grumpy red strawberry with tiny glasses and a green leaf hat"}}],
  "scenes": [{{"narration": "texte lu à voix haute", "characters": ["Prénom"], "image_prompt": "décor + action + émotion, en anglais"}}]
}}"""


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Pas de JSON dans la réponse")
    return json.loads(text[start:end + 1])


def validate(story: dict) -> None:
    scenes = story.get("scenes", [])
    if len(scenes) < 8:
        raise ValueError(f"Pas assez de scènes ({len(scenes)})")
    for s in scenes:
        if not s.get("narration") or not s.get("image_prompt"):
            raise ValueError("Scène incomplète")
    words = sum(len(s["narration"].split()) for s in scenes)
    if words < 150:
        raise ValueError(f"Narration trop courte ({words} mots)")
    for key in ("title", "caption", "characters"):
        if not story.get(key):
            raise ValueError(f"Champ manquant : {key}")


def generate_story(history: list[str], theme: str = "") -> dict:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    theme_line = f"- Thème imposé : {theme}\n" if theme else "- Choisis toi-même un thème drama / histoire vraie amusante.\n"
    prompt = PROMPT.format(theme=theme_line, history="\n".join(f"- {h}" for h in history[-40:]) or "- (aucun)")
    last_err = None
    for _ in range(3):
        msg = client.messages.create(
            model=config.MODEL, max_tokens=3500, system=SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in msg.content if b.type == "text")
        try:
            story = _extract_json(text)
            validate(story)
            return story
        except Exception as e:  # on réessaie avec une nouvelle génération
            last_err = e
    raise RuntimeError(f"Scénario invalide après 3 essais : {last_err}")


def image_prompt(story: dict, scene: dict) -> str:
    looks = {c["name"]: c["look"] for c in story["characters"]}
    present = [looks[n] for n in scene.get("characters", []) if n in looks]
    parts = [config.IMAGE_STYLE, "; ".join(present), scene["image_prompt"]]
    return re.sub(r"\s+", " ", ". ".join(p for p in parts if p))[:900]
