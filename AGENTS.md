# AGENTS.md

Guidance for AI coding agents and contributors. `CLAUDE.md` imports this file, and `.github/copilot-instructions.md` adds the review checklist.

## Language

- All deliverables are written in **English**: commit messages, PR/Issue titles and bodies, review comments, code comments and docstrings, and documentation (`README.md`, `AGENTS.md`, etc.).
- Exceptions (keep as is): localized UI strings (the Japanese `message_ja` WebSocket field and the Japanese text in `index.html`), quotations, technical identifiers, generated files, and external source text.
- Runtime messages (logs, errors) are English.
- Do not rewrite Git history to change the language of past commits.

## Overview

yfts (YouTube Find Thumbnail Scene) takes a YouTube URL, downloads the video and its thumbnail, extracts one frame per second with ffmpeg, and ranks the frames by [perceptual hash](https://en.wikipedia.org/wiki/Perceptual_hashing) distance to the thumbnail. Progress and results are streamed to the browser over a WebSocket.

## Commands

```bash
pip3 install -r requirements.txt
python3 main.py          # serves on http://localhost:5000 (the PORT env var overrides the port)
```

Requires Python 3.6+, ffmpeg and Linux (WSL works). There is no test suite, linter, formatter or CI. Verify changes manually: run the server, open the page, submit a YouTube URL, and confirm the pipeline reaches the final step and shows a matching frame (needs ffmpeg and network access to YouTube).

## Structure

- `main.py`: the whole backend, a [responder](https://github.com/kennethreitz/responder) ASGI app.
  - `GET /` serves `index.html`.
  - WebSocket `/api` (`youtubeThumb`) runs the pipeline step by step and sends one JSON message per step with `status`, `process_code` (0-10), `message` and `message_ja`.
  - Pipeline helpers: `getInfomation` (youtube_dl metadata), `downloadThumbnail` (requests, `maxresdefault.jpg`), `downloadVideo` (youtube_dl, webm), `convertVideoToImage` (ffmpeg, 1 fps), `findThumbnail` (`imagehash.phash`), `getImageBase64`.
- `index.html`: the whole frontend (inline CSS and vanilla JS). Opens a WebSocket to `/api`, sends the URL, and renders per-step messages, a progress bar, the thumbnail and the best-matching frame (inline base64).
- `Procfile`, `runtime.txt`, `requirements.txt`: Heroku deployment metadata.
- `dirpath` in `main.py` (`/tmp/yfts`) is the working directory holding `thumbnails/`, `videos/` and `images/`. Change it in the code, not through an environment variable.

## Conventions

- Match the existing style: 4-space indentation, `.format()` string formatting, camelCase function names. Do not reformat unrelated code.
- Every WebSocket payload carries both an English `message` and a Japanese `message_ja`. Keep both when adding steps.
- Pipeline helpers signal failure by returning `False` or the caught `Exception` rather than raising, and the handler checks with `isinstance(result, Exception)` or a falsy check. Follow that pattern.
- `process_code` values drive the frontend progress bar (`max="10"` in `index.html`). Keep the numbering contiguous and update `index.html` when adding steps.
- The handler tracks connections in `clients` and deletes the entry on every early return. New exit paths must do the same.
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/); branches follow [Conventional Branch](https://conventional-branch.github.io) short form (`feat/...`, `fix/...`).

## Safety

- Never commit secrets. There are no credentials in this repository.
- The user-supplied URL goes straight to `youtube_dl` and triggers remote downloads. Treat it as untrusted and do not derive shell commands or file paths from it.

## Documentation

- Update `README.md` when install/run steps, requirements or supported platforms change.
- Update this file when the pipeline steps, the WebSocket message shape or the deployment setup change.
