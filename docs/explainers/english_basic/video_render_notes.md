# DevMotion rebuild handoff

The user explicitly requested DevMotion. Its exposed tools `get_design_guide` and `create_project` both returned backend `Unknown tool`; plugin search returned no DevMotion result. No DevMotion project ID, hosted preview or plugin export was created, and no AI/export credits were consumed through those failed calls. Do not represent the local MP4 as a DevMotion render.

A local fallback was completed using macOS Samantha speech, Pillow diagrams, OpenCV H264 and AVFoundation AAC/MP4 export. The pip FFmpeg download was stopped when a working native route was verified. No model/data/training logic changed.

If DevMotion is restored, first call its design guide and create/open the project using the actual supported API. Use `storyboard.json`, `narration.md`, `subtitles.srt`, and the 18 chapter PNGs and narration/timing in `data/presentations/urop_explainer_20261028/`. Keep the 588.625-second duration, 1920×1080 canvas, exact current metrics and counterfactual-versus-measurement distinctions. Read engine guidance rather than guessing an import format. Do not upload raw dataset examples or private weights.
