# UROP explanation video

**9:49 · 1080p · English narration · 18 chapters · burned-in captions**

- Watch MP4: `data/presentations/urop_explainer_20261028/UROP_Beginner_to_Architecture.mp4`
- Open `WATCH.html` for a local player with chapter buttons.
- Read `TRANSCRIPT.md` and `VIVA_FAQ.md`; use `captions.srt` for subtitles.
- `VIDEO_RECEIPT.json` records SHA256, duration, complete audio/video decoding and visual review.
- `storyboard.json`, `build_video.py` and Swift source retain editable source. Media/audio caches are ignored in data/.

DevMotion was explicitly attempted, but its backend returned Unknown tool for design-guide and project creation. No DevMotion project/link/export exists. The actual MP4 was rendered locally. See `DEVMOTION_HANDOFF.md` for a future rebuild. No model/data/experiment changes or training were performed.

## Chapters

- 00:00 — What are we building?
- 00:28 — Understand the six classes
- 00:59 — The faculty dataset and lineage
- 01:32 — Train, validate, then test
- 02:00 — Turn titles into model inputs
- 02:32 — Prepare images consistently
- 03:03 — Two pretrained encoders
- 03:35 — Make the feature sizes compatible
- 04:06 — What maximum fusion really does
- 04:36 — From fused features to six probabilities
- 05:13 — How learning changes the weights
- 05:41 — Fit the experiment onto a T4
- 06:11 — Four epochs, four validations, one test
- 06:42 — Which checkpoint won—and why?
- 07:11 — Read the final metrics correctly
- 07:55 — What does the paper comparison prove?
- 08:28 — Why preparation and recovery mattered
- 09:06 — Defend the design—and know what is next

## Rebuild

Run from the UROP root: compile the two Swift sources to the private output directory, then run `.venv-urop/bin/python docs/explainers/urop_20261028/build_video.py`. The builder refuses to overwrite an existing final MP4; use a new output directory when revising. The script uses native installed speech and H264 support, without FFmpeg downloads.
