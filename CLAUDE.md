# CLAUDE.md

## Overview

YouTube Find Thumbnail Scene (yfts): given a YouTube URL, finds the point in
the video that most closely matches the video's thumbnail image. It downloads
the video and thumbnail, extracts one frame per second with ffmpeg, and ranks
frames by [perceptual hash](https://en.wikipedia.org/wiki/Perceptual_hashing)
distance to the thumbnail. Progress and results are streamed to the browser
over a WebSocket.

## Architecture

- `main.py` — the entire backend. It is a [responder](https://github.com/kennethreitz/responder)
  ASGI app that:
  - serves `index.html` at `GET /`;
  - exposes a WebSocket endpoint at `/api` (`youtubeThumb`) that drives the
    pipeline step by step, sending a JSON message per step with
    `status`, `process_code` (0-10), `message`, and `message_ja`;
  - runs a background daemon thread (`awake`) that periodically pings the
    deployed URL to keep a hosted instance alive.
  - Pipeline functions: `downloadThumbnail` (via `requests`), `downloadVideo`
    (via `youtube_dl`, webm), `convertVideoToImage` (via `ffmpeg`, `r=1`),
    `findThumbnail` (via `imagehash.phash` + `PIL`), `getImageBase64`.
- `index.html` — the entire frontend: a single page with inline CSS and vanilla
  JS. Opens a WebSocket to `/api`, sends the URL, and renders per-step messages,
  a progress bar, the thumbnail, and the best-matching frame (delivered inline
  as base64).
- `Procfile`, `runtime.txt`, `requirements.txt` — Heroku deployment metadata.
- `dirpath` in `main.py` (currently `/tmp/yfts`) is the working directory where
  `thumbnails/`, `videos/`, and `images/` are created. Change it there, not via
  an environment variable.

## Development commands

Requires Python 3.6+, ffmpeg, and Linux (WSL works; Windows native likely does
not). There is no package manager config beyond `requirements.txt`.

```bash
pip3 install -r requirements.txt
python3 main.py          # serves on http://localhost:5000 (PORT env overrides)
```

## Conventions

- Backend messages are bilingual: every WebSocket JSON payload carries both an
  English `message` and a Japanese `message_ja`. Keep both when adding steps.
- Pipeline helper functions signal failure by returning either `False` or the
  caught `Exception` object (not by raising); the WebSocket handler inspects the
  return value with `isinstance(result, Exception)` / falsy checks. Follow this
  existing pattern rather than letting exceptions propagate to the caller.
- `process_code` values are consumed by the frontend progress bar (`max=10`);
  keep the numbering contiguous and update `index.html` if you add steps.

## Testing

There are no automated tests, linters, or CI. Verify changes manually: run the
server locally, open `http://localhost:5000/`, submit a YouTube URL, and confirm
the pipeline advances through all steps and renders a matching frame. ffmpeg and
network access to YouTube are required for an end-to-end run.

## Security / prohibitions

- Never commit secrets. There are currently no credentials in this repo; keep it
  that way (no API keys, tokens, or internal URLs).
- The `/api` endpoint passes the user-supplied URL directly to `youtube_dl` and
  downloads remote content. Treat all incoming URLs as untrusted; do not extend
  the handler to run shell commands or file operations derived from user input.

## Documentation update rules

- Update `README.md` when the install/run steps, requirements, or supported
  platforms change.
- Update this file when `main.py`'s pipeline steps, the WebSocket message shape,
  or the deployment/runtime setup changes.
