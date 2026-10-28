# Beyond the caption

**Verified final video: 1920×1080, 30 fps, 3 minutes 53 seconds (rounded), Bella / Eleven v4.**

Telugu-English research explainer about multimodal misinformation classification.

Voice: **Bella — Professional, Bright, Warm** (`hpp4J3VqNfWAUOO0d1Us`). Model: **Eleven v4**, whose provider model inventory explicitly includes Telugu (`te`). All voice access used the existing **composio dev62** connection. Bella is a multilingual preset; no claim of a native Telugu voice actor is made. No API keys, authentication material, purchases or overages are part of this project.

## Open and edit

- `UROP_Telugu_English_Bella.mp4`: final output, once the production receipt records completed verification.
- [WATCH.html](WATCH.html): offline player with section buttons.
- [NARRATION.md](NARRATION.md): final Telugu-English narration.
- [script.json](script.json): editable script, headings and story structure.
- [subtitles.srt](subtitles.srt): matching captions, wrapped with the rendered font.
- [src/video.tsx](src/video.tsx): complete editable Remotion composition.
- [src/timeline.json](src/timeline.json): narration, caption and section timing.
- [render.mjs](render.mjs): Remotion bundling, review-frame generation and H264 render.
- [evidence/PRODUCTION_RECEIPT.json](evidence/PRODUCTION_RECEIPT.json): current verification status, voice/model, provenance and final file hash.

Run from this directory:

```bash
npm ci --cache .npm-cache --no-audit --no-fund
npm run studio
npm run typecheck
STILLS_ONLY=1 npm run render
```

`npm run render` creates the MP4 with Remotion; it refuses to overwrite an existing output. Preserve the original or choose a new output filename before a revision. Dependencies are locked to compatible versions. The render uses installed Google Chrome in an isolated headless session, not a user browser profile, with concurrency three. It needs no cloud GPU or model-training runtime. The current production audio is already saved; rendering requires no ElevenLabs access or credits.

`prepare_audio.py` is an optional offline assembly step. It reads the retained private `evidence/provider_sources.zip`, converts accepted MP3 files to WAV, assembles narration and constructs captions/animation markers from provider character timing. **It overwrites derived audio, timeline and SRT files**, so use a copy for revisions. It makes no external service calls. The published SRT is subsequently wrapped using actual font measurements captured from Remotion.

`verify_video.py` uses the existing UROP Python environment (OpenCV/Pillow) and the previously retained native audio-decoding helper to independently decode the output. The main MP4 and the editable composition were both produced with Remotion; native tools are used only for offline audio assembly and independent verification.

## Research evidence and scope

The narrative was checked against the current [completion receipt](../../../results/MM_FINAL_COMPLETION_RECEIPT_20261028.json), [authoritative report](../../../results/MULTIMODAL_FINAL_REPORT_20261028.md), [registered config](../../../configs/multimodal_usable_6way_v2.json), and actual `MaximumFusion` implementation at [train_usable_multimodal_v2.py](../../../scripts/train_usable_multimodal_v2.py).

Confirmed: BERT-base text CLS representation; ResNet-50 pooled image representation; independent linear projections to 512 with LayerNorm; elementwise maximum fusion; 256-unit GELU/dropout classification head producing category scores. Both encoders are fine-tuned. The video explains separate training, validation selection, frozen final testing and complementary evaluation measures, with no performance numbers or completion claims.

The images/cards and feature bars are original illustrative SVG shapes. No dataset rows, post text, usernames or actual images were used. Architecture dimensions explain the implementation; they are not performance metrics. The on-screen narrative contains no dates, timestamps, cohort counts, completion percentages or future-work claims. A research-category prediction is explicitly distinguished from factual verification.

## ECC Remotion rule application

Applied the installed `ecc:remotion-video-creation` skill and its relevant rules:

- All motion uses `useCurrentFrame()` and deterministic interpolation/easing. No CSS animations, transitions, random motion, requestAnimationFrame or wall-clock animation.
- Audio uses `Audio` from `@remotion/media`; audio/font assets use `staticFile()` and are retained locally.
- Narration-derived timing fixes composition duration. The transition overlap is included in the frame count; crossfades last twelve frames. Sequences are premounted.
- Local OFL Noto Sans Telugu is loaded before measuring or rendering. `measureText`/`fitText` bound headings, node labels and captions. Captions allow at most two lines; only a few technical terms receive emphasis.
- The progress line follows the narration section, not model-training progress. Illustrative feature bars explain max fusion; they report no measurements.
- A clean 2D architecture was chosen because it exposes both streams and their join without decorative complexity. No 3D, shaders or independent scene loops were used.

## Narration quality and retained history

A longer Bella preview was generated before production. ElevenLabs Scribe v2 recovered the Telugu and English technical terms; this is an intelligibility/semantic readback, not a human native-speaker listening assessment. Each accepted narration scene was also independently transcribed and compared with the intended content.

The first dataset-section generation was truncated even though the synthesis response contained timing for the whole requested text. A shorter retry also truncated. Both were rejected; successful synthesis/alignment alone was not treated as content proof. The accepted dataset section is three short, individually transcribed clauses (`scene_01_part0`, `part1`, `part2`), joined with short pauses and correctly offset timing. The takeaway was revised to say “text encoder, image encoder” after a technical-name ambiguity in its transcript. Rejected generations remain evidence and are excluded from the rendered audio.

An initial build exposed an incompatible top-level Mediabunny version. It was corrected to **1.62.0**, matching `@remotion/media`'s pinned dependency; TypeScript and bundling then passed. Earlier Chaitra/library payment blockers are historical: the user explicitly chose the working free Bella preset. No fallback to another provider or rendering backend occurred.

Provider quota observations and rejected-generation details are retained in the private production receipt. No purchase or overage occurred.

Large media, provider responses, rejected generations, dependencies and caches remain in this ignored presentation directory. Existing explainers, research data, model code, weights and experiment results are unchanged. Never regenerate narration merely to fix a render: reuse the retained production WAV and timing.
