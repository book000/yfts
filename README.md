# YouTube Find Thumbnail Scene (yfts)

YouTube動画内でサムネイル画像に設定されている箇所を探します。  
Find the part set in the thumbnail image in the YouTube video.

## Demo / Release

https://yfts.herokuapp.com/

## Attention

真面目に動作させる場合、プロジェクトをクローンしてローカルで実行することを強くお勧めします。Herokuにお試しで置いてはいますが、動画から画像への変換にとんでもない時間が掛かります。

## Requirements

- Python 3.6+ & pip
- Linux only (Maybe it doesn't work on Windows)
  - Tested to work with WSL
- ffmpeg

## Installation

### 1. Git Clone & Change current directory

```bash
git clone https://github.com/book000/yfts.git
cd yfts
```

## 2. pip install & Run main.py

```bash
pip3 install -r requirements.txt
python3 main.py
```

必要に応じて`dirpath`の位置を変更してください。動画などが保存されるディレクトリになります。  
Change the position of `dirpath` if necessary. This is the directory where videos etc. are saved.

## 3. Access to localhost:5000

http://localhost:5000/

## Disclaimer

**このプロジェクトを使用したことによって引き起こされた問題に関して開発者は一切の責任を負いません。**  
**The author is not responsible for any problems caused by the user using this project.**

## ライセンス / License

このプロジェクトのライセンスは[MIT License](https://github.com/book000/yfts/blob/master/LICENSE)です。  
The license for this project is [MIT License](https://github.com/book000/yfts/blob/master/LICENSE).
