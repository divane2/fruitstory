# FruitStory — vidéos drama de plus d'une minute, 100 % automatiques

Chaque jour, GitHub Actions :
1. demande à Claude un scénario (histoire amusante / drama racontée par des fruits, ~70-85 s) ;
2. génère la voix off (edge-tts, gratuit) et les images de chaque scène ;
3. monte une vidéo verticale 1080×1920 avec sous-titres (ffmpeg) ;
4. la met en ligne (GitHub Release = lien public) ;
5. la programme sur **TikTok + Facebook** via Metricool, à l'heure choisie (20:30 Douala par défaut).

## Installation (10 min)

1. Crée un dépôt GitHub **public** (le lien de la vidéo doit être public pour Metricool ; Actions est gratuit et illimité sur un dépôt public). Envoie-y tous ces fichiers.
2. `Settings → Secrets and variables → Actions → Secrets` :
   - `ANTHROPIC_API_KEY` (console.anthropic.com — quelques centimes par vidéo)
   - `METRICOOL_TOKEN` (Metricool → Compte → API)
   - `METRICOOL_USER_ID` et `METRICOOL_BLOG_ID` (dans l'URL de Metricool : `...?blogId=XXXX&userId=YYYY`)
   - `METRICOOL_EMAIL` (optionnel)
3. `Variables` (optionnel) : `PUBLISH_TIME` = `20:30` ; `FACEBOOK_TIME` si tu veux Facebook à une autre heure (ex. `19:30`).
4. `Settings → Actions → General → Workflow permissions` : **Read and write**.
5. Onglet **Actions → Vidéo du jour → Run workflow** avec `publish = false` pour un premier test. Regarde la vidéo dans *Releases*. Ensuite relance avec `publish = true`.

## Personnaliser
- Voix : variable `TTS_VOICE` (`fr-FR-DeniseNeural`, `fr-FR-EloiseNeural`…).
- Thème imposé : champ `theme` au lancement manuel.
- Musique : dépose des `.mp3` libres de droits dans `assets/music/` (mixée à bas volume).
- Heure de génération : `cron` dans `.github/workflows/daily.yml`.

## À savoir
- Images : Pollinations (gratuit). Si le service est lent, certaines scènes passent en carte colorée ; si plus de la moitié échoue, rien n'est publié.
- L'accès à l'API Metricool peut dépendre de ton abonnement. Sans token, `publish_metricool.py` affiche simplement la requête (mode test).
- TikTok demande d'indiquer le contenu généré par IA : active l'option dans l'application TikTok / Metricool.
