# UROP explanation video — ElevenLabs edition

Open [WATCH.html](WATCH.html) for the chapter player, or open the MP4 at
`data/presentations/urop_elevenlabs_20261028/UROP_Beginner_to_Architecture_ElevenLabs.mp4`.

The full 18-chapter beginner-to-architecture explanation now uses **ElevenLabs Alice — Clear, Engaging Educator**, synthesized with Multilingual v2 through the user-selected Composio connection. No voice cloning was used. The original local Samantha version remains intact.

- [Transcript](TRANSCRIPT.md)
- [Sentence captions](captions.srt)
- [Verification receipt](VIDEO_RECEIPT.json)
- [Architecture and faculty Q&A](../urop_20261028/VIVA_FAQ.md)
- [Original verified storyboard](../urop_20261028/storyboard.json)
- [Scientific completion receipt](../../../results/MM_FINAL_COMPLETION_RECEIPT_20261028.json)

## Audio, timing and provenance

Eighteen production requests generated the complete script; the first chapter served as the compatibility check and was retained. The initial missing `user_read` scope was corrected by the user, then subscription/voices/model reads and actual synthesis succeeded. The selected Composio profile was the one explicitly requested by the user; the connection alias is not proof of the underlying ElevenLabs account email. No API key was retrieved or stored in project files.

Live provider usage changed from 0 to **9,422 / 10,000** characters. There was no purchase or overage. Available characters after generation: **578**. Provider input character totals and billing counts can differ; the provider subscription counter is the usage source of truth.

The provider supplied original-text character timestamps using its documented [speech-with-timing endpoint](https://elevenlabs.io/docs/api-reference/text-to-speech/convert-with-timestamps). Sentence cues are derived from those returned positions. Narration was synthesized at speed 1.08, then the complete recording was adjusted by a **1.1461 tempo factor with zero pitch shift** using native macOS AVAudioUnitTimePitch, reducing 664.7186 seconds including chapter pauses to approximately 580 seconds. Captions and chapter times were scaled by the same factor. This retains every spoken sentence while meeting the under-ten-minute requirement; it is not a regenerated or shortened script.

The final verification receipt records actual encoded duration, dimensions, complete video/audio decoding, layout bounds, and SHA-256. Decoding establishes media integrity; it does not establish a human pronunciation or listening review. The scientific content and architecture diagrams match the original verified storyboard. Research data, weights, code, metrics and experiment status were not changed.

Visual rendering remains local Pillow/OpenCV/AVFoundation. DevMotion's earlier backend failure is preserved in the [original handoff](../urop_20261028/DEVMOTION_HANDOFF.md); this video is not a DevMotion export.

## Private assets and rebuilding

Generated MP3 chapters, complete provider alignment responses, the downloaded source ZIP, unprocessed and processed WAVs, timing JSON, frame images and MP4 stay under ignored `data/presentations/urop_elevenlabs_20261028/`. They are not committed to GitHub. Source and small sanitized documentation/receipts are suitable for Git backup.

The following are offline postproduction commands, not synthesis calls. They require installed Python dependencies and native compiled helpers retained from the original video. They write substantial media and refuse to overwrite prepared narration/final video. For a new revision use a new output folder first; do not rerun generation to recover a rendering problem.

```bash
cd /Users/panveenaidu/Downloads/SEM7/UROP
swiftc docs/explainers/urop_20261028/tempo.swift -o data/presentations/urop_explainer_20261028/tempo
.venv-urop/bin/python docs/explainers/urop_20261028/assemble_elevenlabs_audio.py
.venv-urop/bin/python docs/explainers/urop_20261028/build_elevenlabs_video.py
```

The assembler requires the already-downloaded, retained `urop_elevenlabs_sources.zip`; it checks ZIP integrity, per-chapter audio hashes, exact alignment text and timing lengths. There are no account credentials or API calls in these scripts. Keep the private source archive rather than generating the same narration again.
