import os
import os.path as path
import requests
import youtube_dl
import imagehash
from PIL import Image
import ffmpeg
from youtube_dl.utils import DownloadError
import responder
import json
import asyncio
import base64
import threading
import time

dirpath = "/tmp"

if not path.exists(dirpath + "/images/"):
    os.mkdir(dirpath + "/images/")

if not path.exists(dirpath + "/thumbnails/"):
    os.mkdir(dirpath + "/thumbnails/")

if not path.exists(dirpath + "/videos/"):
    os.mkdir(dirpath + "/videos/")


def downloadThumbnail(vid):
    url = "https://img.youtube.com/vi/{vid}/maxresdefault.jpg".format(vid=vid)
    response = requests.get(url)

    print("Status code: {}".format(response.status_code))

    if "image" not in response.headers["content-type"]:
        print("Content type not supported: {}".format(
            response.headers["content-type"]))
        return False

    with open(dirpath + "/thumbnails/" + vid + ".jpg", "wb") as f:
        f.write(response.content)

    return True


def downloadVideo(vid):
    ydl = youtube_dl.YoutubeDL(
        {"outtmpl": dirpath + "/videos/%(id)s.%(ext)s", "format": "webm"})
    try:
        with ydl:
            ydl.extract_info(
                "https://youtu.be/{}".format(vid),
                download=True
            )
    except Exception as e:
        return e


def convertVideoToImage(vid):
    if not path.exists(dirpath + "/images/{}/".format(vid)):
        os.mkdir(dirpath + "/images/{}/".format(vid))

    try:
        stream = ffmpeg.input(
            dirpath + "/videos/" + vid + ".webm"
        )
        stream = ffmpeg.output(
            stream,
            dirpath +
            '/images/{}/%05d.jpg'.format(vid),
            r=1
        )
        ffmpeg.run(stream)
        return True
    except Exception as e:
        return e


def getImageBase64(vid, sec):
    print("getImageBase64({}, {})".format(vid, sec))
    with open(dirpath + "/images/{}/{}.jpg".format(vid, str(sec).zfill(5)), "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode("utf-8")


def findThumbnail(vid):
    thumbnails_hash = imagehash.phash(
        Image.open(dirpath + "/thumbnails/" + vid + ".jpg")
    )

    files = [f for f in os.listdir(
        dirpath + "/images/{}/".format(vid)) if path.isfile(path.join(dirpath + "/images/{}/".format(vid), f))]
    files_similar = {}
    for file in files:
        file_hash = imagehash.phash(Image.open(
            path.join(dirpath + "/images/{}/".format(vid), file)))
        files_similar[int(file[:-4])] = file_hash-thumbnails_hash

    return sorted(files_similar.items(), key=lambda x: x[1])


def getInfomation(url):
    try:
        with youtube_dl.YoutubeDL({}) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        return e


def main(url):
    info = getInfomation(url)
    title = info.get("title", None)
    uploader = info.get("uploader", None)
    vid = info.get("id", None)

    if vid is None:
        print("Could not find video ID")
        return

    print(title + " - " + uploader)

    if not path.exists(dirpath + "/images/"):
        os.mkdir(dirpath + "/images/")

    if not path.exists(dirpath + "/thumbnails/"):
        os.mkdir(dirpath + "/thumbnails/")

    if not path.exists(dirpath + "/videos/"):
        os.mkdir(dirpath + "/videos/")

    print(downloadThumbnail(vid))
    print(downloadVideo(vid))
    print(convertVideoToImage(vid))
    print(findThumbnail(vid))


api = responder.API()
clients = {}


@api.route("/")
def indexPage(req, response):
    response.headers = {"Content-Type": "text/html; charset=utf-8"}
    with open(path.dirname(path.abspath(__file__)) + "/index.html") as f:
        response.text = f.read()


@api.route("/api", websocket=True)
async def youtubeThumb(ws):
    await ws.accept()
    key = ws.headers.get("sec-websocket-key")
    clients[key] = ws
    try:
        while True:
            print("- Process started.")

            # Process 0 : Waiting url
            print("[0] Waiting URL...")
            await ws.send_json({
                "status": True,
                "process_code": 0,
                "message": "Waiting URL...",
                "message_ja": "URLを待っています..."
            })
            url = await ws.receive_text()

            # Process 1: Received url, Get video infomation
            print("[1] Getting Video Infomation...")
            await ws.send_json({
                "status": True,
                "process_code": 1,
                "message": "Getting Video Infomation...",
                "message_ja": "動画情報を取得しています..."
            })
            await asyncio.sleep(1)
            info = getInfomation(url)

            # Process 2 : Whether got information
            if isinstance(info, Exception):
                if "not a valid URL" in str(info):
                    info = "Invalid URL"
                print("[2] Get Video Infomation failed.")
                await ws.send_json({
                    "status": False,
                    "process_code": 2,
                    "message": "Get Video Infomation failed. <code>{}</code>".format(str(info)),
                    "message_ja": "動画情報の取得に失敗しました"
                })
                await asyncio.sleep(1)
                await ws.close()
                del clients[key]
                return

            print("[2] Get Video Infomation completed.")
            await ws.send_json({
                "status": True,
                "process_code": 2,
                "message": "Get Video Infomation completed.",
                "message_ja": "動画情報の取得に成功しました。",
                "info": {
                    "vid": info.get("id"),
                    "title": info.get("title"),
                    "uploader": info.get("uploader")
                }
            })
            vid = info.get("id")
            await asyncio.sleep(1)

            # Process 3 : Download thumbnail image
            print("[3] Downloading thumbnail image...")
            await ws.send_json({
                "status": True,
                "process_code": 3,
                "message": "Downloading thumbnail image...",
                "message_ja": "サムネイル画像をダウンロードしています..."
            })
            await asyncio.sleep(1)

            # Process 4 : Whether download thumbnail image
            if not downloadThumbnail(vid):
                print("[4] Download thumbnail image failed.")
                await ws.send_json({
                    "status": False,
                    "process_code": 4,
                    "message": "Download thumbnail image failed.",
                    "message_ja": "サムネイル画像のダウンロードに失敗しました。"
                })
                await asyncio.sleep(1)
                await ws.close()
                del clients[key]
                return

            print("[4] Download thumbnail image completed.")
            await ws.send_json({
                "status": True,
                "process_code": 4,
                "message": "Download thumbnail image completed.",
                "message_ja": "サムネイル画像のダウンロードに成功しました。"
            })
            await asyncio.sleep(1)

            # Process 5 : Download video
            print("[5] Downloading video...")
            await ws.send_json({
                "status": True,
                "process_code": 5,
                "message": "Downloading video...",
                "message_ja": "動画をダウンロードしています..."
            })
            await asyncio.sleep(1)

            # Process 6 : Whether download video
            dlResult = downloadVideo(vid)
            if isinstance(dlResult, Exception):
                print("[6] Download video failed.")
                await ws.send_json({
                    "status": False,
                    "process_code": 6,
                    "message": "Download video failed. <code>{}</code>".format(str(dlResult)),
                    "message_ja": "動画のダウンロードに失敗しました。"
                })
                await asyncio.sleep(1)
                await ws.close()
                del clients[key]
                return

            print("[6] Download video completed.")
            await ws.send_json({
                "status": True,
                "process_code": 6,
                "message": "Download video completed.",
                "message_ja": "動画のダウンロードに成功しました。"
            })
            await asyncio.sleep(1)

            # Process 7 : Convert video to image
            print("[7] Converting video to image...")
            await ws.send_json({
                "status": True,
                "process_code": 7,
                "message": "Converting video to image...",
                "message_ja": "動画から画像に変換しています..."
            })
            await asyncio.sleep(1)

            # Process 8 : Whether download video
            convResult = convertVideoToImage(vid)
            if isinstance(convResult, Exception):
                print("[8] Convert video to image failed.")
                await ws.send_json({
                    "status": False,
                    "process_code": 8,
                    "message": "Convert video to image failed. <code>{}</code>".format(str(convResult)),
                    "message_ja": "動画から画像への変換に失敗しました。"
                })
                await asyncio.sleep(1)
                await ws.close()
                del clients[key]
                return

            print("[8] Convert video to image completed.")
            await ws.send_json({
                "status": True,
                "process_code": 8,
                "message": "Convert video to image completed.",
                "message_ja": "動画から画像への変換に成功しました。"
            })
            await asyncio.sleep(1)

            # Process 9 : Finding a scene that looks like a thumbnail
            print("[9] Finding a scene that looks like a thumbnail...")
            await ws.send_json({
                "status": True,
                "process_code": 9,
                "message": "Finding a scene that looks like a thumbnail...",
                "message_ja": "サムネイル画像に合うシーンを探しています..."
            })
            await asyncio.sleep(1)

            # Process 10 : Whether find a scene that looks like a thumbnail
            similars = findThumbnail(vid)
            if similars.count == 0:
                print("[10] Not found a scene that looks like a thumbnail.")
                await ws.send_json({
                    "status": False,
                    "process_code": 10,
                    "message": "Not found a scene that looks like a thumbnail.",
                    "message_ja": "サムネイル画像に合うシーンが見つかりませんでした。"
                })
                await asyncio.sleep(1)
                await ws.close()
                del clients[key]
                return

            print("[10] All Completed. ")

            best_image = getImageBase64(vid, next(iter(similars))[0])

            print("[10] Base64 converted. ")

            await ws.send_json({
                "status": True,
                "process_code": 10,
                "message": "All Completed.",
                "message_ja": "全ての処理が完了しました。",
                "vid": vid,
                "data": {
                    "best": next(iter(similars)),
                    "similars": similars
                },
                "best_image": best_image
            })
            await asyncio.sleep(1)

            print("- Process finished.")
    except:
        await ws.close()
        del clients[key]


def awake():
    while True:
        try:
            print("Start Awaking")
            requests.get("https://yfts.herokuapp.com/")
            print("End")
        except:
            print("error")
        time.sleep(300)


t = threading.Thread(target=awake)
t.start()

api.run(address="0.0.0.0", port=int(os.environ.get("PORT", 5000)), workers=1)
