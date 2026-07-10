# Copilot Code Review Instructions

Guidance for reviewing pull requests in this repository (YouTube Find Thumbnail
Scene). Focus on the priorities below; do not raise the listed non-issues.

## Project shape

- Small Python web app. Backend is a single `main.py` built on the
  [responder](https://github.com/kennethreitz/responder) ASGI framework;
  frontend is a single `index.html` with inline CSS and vanilla JS.
- The `/api` WebSocket endpoint runs the pipeline (download thumbnail, download
  video, extract frames with ffmpeg at 1 fps, rank by perceptual hash) and sends
  one JSON status message per step.
- No test suite, no linter/formatter config, and no CI. Deployment metadata:
  `Procfile`, `runtime.txt`, `requirements.txt`.

## Review priorities

- **Untrusted input.** The user-supplied URL flows into `youtube_dl` and triggers
  network downloads. Flag any change that passes user input into shell commands,
  `os`/file-path operations, `eval`, or string-formatted paths without validation.
- **WebSocket protocol consistency.** Each step sends a JSON object with
  `status`, `process_code`, `message`, and `message_ja`. Flag new/changed steps
  that omit any of these, drop the Japanese `message_ja`, or break the
  contiguous `process_code` numbering that the frontend progress bar
  (`max=10` in `index.html`) depends on.
- **Error handling pattern.** Pipeline helpers signal failure by returning
  `False` or the caught `Exception` (not by raising), and the handler checks with
  `isinstance(..., Exception)` / falsy checks. Flag new code that mixes these two
  styles inconsistently or lets exceptions escape the handler and kill the
  WebSocket loop.
- **Client cleanup.** The handler tracks connections in the `clients` dict and
  deletes the entry on every early return / close. Flag new early-exit paths that
  leave a stale `clients[key]` entry.
- **Blocking work.** Downloads and ffmpeg run synchronously inside the async
  handler. Flag additions that add further long, unbounded blocking work without
  acknowledging the impact, but see non-issues below before flagging the existing
  calls.

## Known non-issues (do not flag)

- The existing synchronous `requests`/`youtube_dl`/`ffmpeg` calls inside the
  async WebSocket handler are a known, accepted design for this single-purpose
  tool. Do not raise them unless a PR is specifically reworking that area.
- Hardcoded `dirpath = "/tmp/yfts"` is intentional; it is documented as the
  edit point rather than an environment variable.
- The bare `except:` at the end of the WebSocket handler is intentional
  connection-teardown cleanup.
- Inline CSS/JS in `index.html` and the absence of a frontend build step are
  intentional for this small project; do not suggest introducing a framework or
  bundler.
- Absence of automated tests is known. Do not request added test coverage as a
  blocking review comment.

## Style

- Match the existing style: 4-space indentation, `.format()`-style string
  formatting, and the existing naming (camelCase function names such as
  `downloadThumbnail`). Do not ask to reformat unrelated existing code or convert
  the whole file to f-strings/snake_case in an unrelated PR.
