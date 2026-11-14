# YouTube Find Thumbnail Scene (yfts)

Finds the point in a YouTube video that matches the video's thumbnail image.

## How it works

Given a YouTube URL, the app downloads the video and its thumbnail, extracts one frame per second with ffmpeg, and computes the [perceptual hash](https://en.wikipedia.org/wiki/Perceptual_hashing) distance between each frame and the thumbnail. The closest frame is shown together with a link to that time in the video. Progress is streamed to the browser over a WebSocket.

Uploaders can set a thumbnail that does not appear in the video at all (for example an image edited in external software), so this tool is only useful in a fairly narrow set of cases.

Converting a video to images is slow, so running the project locally is strongly recommended for anything beyond a quick try.

## Requirements

- Python 3.6+ and pip
- ffmpeg
- Linux (it probably does not work on native Windows; it has been tested on WSL)

## Installation and usage

```bash
git clone https://github.com/book000/yfts.git
cd yfts
pip3 install -r requirements.txt
python3 main.py
```

Then open http://localhost:5000/ and submit a YouTube URL. The `PORT` environment variable overrides the listening port.

The working directory for downloaded thumbnails, videos and extracted frames is the `dirpath` variable in `main.py` (default `/tmp/yfts`). Change it there if necessary.

## Disclaimer

**The author is not responsible for any problems caused by the user using this project.**

## License

This project is licensed under the [MIT License](LICENSE).
