# StreamClipper implementation specification (Windows / RTX 2050 4 GB)

## Accepted scope

- Primary platform: Windows desktop.
- Content profile: gaming only. No real-world accident/fight classification in this iteration.
- Manual clipping: both VOD timestamp selection and live capture from the existing live process.
- Event recognition: local, balanced precision/recall, GPU-memory-aware.
- Clipping: automatic event-to-clip generation. Human approval/review queue is explicitly deferred.
- Streamer Split: vertical layout (streamer panel above gameplay). Improve identification/crop stability without a separate broad refactor phase.
- Editing: optional; manual clips initially use a clean trim/export path, with existing style/render options to be integrated later.

## Architecture decisions

### Manual VOD
Use the existing upload endpoint and support URL sources. A dashboard request creates a normal persisted job and queues a CLI child process. URL ranges are downloaded with the existing yt-dlp slice downloader; local uploaded videos are trimmed with FFmpeg. Output is written under the job's `out` directory and served through the existing safe file endpoint.

### Manual live
Do not create a second recorder. The dashboard writes a bounded capture request into the active live job's output directory. The existing `LiveRun` loop services it against its existing `Ring` buffer, exports the selected segment window, trims it to the requested interval, and writes a status/result document. The dashboard polls that result and links the completed file. Capture is limited to buffered pre-roll; post-roll can be added later.

### Gaming event recognition
Add a local gaming-event candidate layer that emits timestamped, typed candidates. Keep it independent of transcript LLM story analysis. The first model integration should be optional and lazily loaded; use low-resolution sparse frame sampling, batch size 1, FP16 where supported, and serialized GPU work. Do not load multiple GPU models concurrently on a 4 GB card. Event labels: combat/fight, vehicle collision, explosion, fall, funny/unexpected, streamer reaction. Audio/transcript/chat are supporting context, not proof of a visual event. Candidate fusion should balance false positives and missed events, and the existing clip scoring/rendering remains the final decision layer.

A pretrained detector alone cannot reliably distinguish a real in-game fight/crash/fall from visually similar gameplay. Before claiming quality, evaluate against labelled gaming samples. This code iteration should not add a large mandatory PyTorch dependency or download multi-GB weights automatically.

### Streamer Split precision
The target is vertical 9:16 output with the streamer in the upper panel and gameplay in the lower panel. Improve webcam-panel detection by combining face detections across sampled frames, panel/corner geometry, temporal consistency and scene-cut handling. Prefer the existing MediaPipe face detector (bundled BlazeFace full-range) and tracking utilities; avoid adding a large GPU model. If confidence is low, use the existing safe crop/fallback rather than jumping between faces. Manual crop override remains available in the editor.

## Delivery order

1. Manual VOD trim/export and Manual Clip dashboard page.
2. Live capture request bridge using the existing ring buffer.
3. Gaming-only local event candidate API and lightweight inference adapter.
4. Streamer Split vertical panel detection improvements and validation.
5. Integrate event candidates into existing scoring and automatic clip rendering.

## Explicitly deferred

- Approval/review queue.
- Real-world fight/accident recognition.
- Large video-language models and continuous frame-by-frame LLM inference.
- A broad CI/regression-hardening phase as a standalone feature.
- A separate live recorder.
