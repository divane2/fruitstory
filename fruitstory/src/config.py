"""Réglages de l'outil. Tout peut être changé via variables d'environnement (secrets/variables GitHub)."""
import os

TZ = os.getenv("TZ_NAME", "Africa/Douala")
PUBLISH_TIME = os.getenv("PUBLISH_TIME", "20:30")      # même heure TikTok + Facebook
FACEBOOK_TIME = os.getenv("FACEBOOK_TIME", "")         # optionnel : si rempli, Facebook part à une autre heure

MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
VOICE = os.getenv("TTS_VOICE", "fr-FR-HenriNeural")    # autres : fr-FR-DeniseNeural, fr-FR-EloiseNeural
RATE = os.getenv("TTS_RATE", "+5%")

W, H, FPS = 1080, 1920, 30
MIN_SECONDS = int(os.getenv("MIN_SECONDS", "62"))      # > 1 minute garantie
MAX_SECONDS = int(os.getenv("MAX_SECONDS", "88"))      # Reels Facebook : 90 s max
SCENE_PAD = 0.35                                       # petite respiration entre les scènes (s)

IMAGE_STYLE = (
    "3D Pixar-style animated scene, anthropomorphic fruit characters with expressive cartoon faces, "
    "small arms and legs, vibrant colors, cinematic lighting, vertical 9:16 composition, "
    "no text, no letters, no watermark"
)
