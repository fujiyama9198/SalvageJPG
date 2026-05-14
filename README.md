# JPEGSalvage

破損したバイナリストリームから JPEG 画像データを復元するツールです。

## 概要

JPEGSalvage は、ディスク復旧やファイルシステムの破損時に、バイナリ領域から JPEG マーカー（SOI/EOI）を探索して、失われた JPEG 画像を復元します。

***警告!***  
物理的に損傷したディスクは不用意に読み出し操作をすると事態を悪化させる危険があります。  
この意味がわからない場合は、素直に諦めて、専門業者を頼ることを **強く強く** 推奨します。

## 機能

- **JPEG マーカー検索**: SOI（Start of Image: `0xFFD8`）と EOI（End of Image: `0xFFD9`）マーカーを検出
- **複数の検索戦略**:
  - 標準検索: SOI から前方に EOI を探索
  - イーガー検索モード1: SOI から後方に EOI を探索（より多くのデータを保持）
  - ***推奨***: イーガー検索モード2: SOI から前方に EOI を探索（効率的）
- **フィルタリング**: 画像サイズによる検出結果の絞り込み

## セットアップ

### venvによる方法

```bash
git clone https://github.com/fujiyama9198/SalvageJPG
cd SalvageJPG
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### uvによる方法

```bash
git clone https://github.com/fujiyama9198/SalvageJPG
cd SalvageJPG
uv sync
```


## 使用方法

まず何はともあれディスクをイメージに書き出す必要があります。ディスクの物理損傷が疑われる場合はddrescueもおすすめですが、不用意にディスクを触るよりも専門業者に頼むほうが適切です。

```bash
sudo dd if=/dev/ディスク番号 of=disk.img conv=noerror,sync
```

次に本ツールを実行します。

```bash
python salvageJpg.py <入力ファイル> [オプション]
```

### オプション

| オプション | 説明 |
|-----------|------|
| `-o, --outdir` | 出力ディレクトリ（デフォルト: 入力ファイル名と同じ） |
| `-s, --filter-by-size` | 指定サイズ以上の画像のみを保存（ピクセル長辺） |
| `-e, --eager` | イーガー検索を使用（`-e1` or `-e2`） |
| `-m, --max-bytes` | 各 JPEG から読み込む最大バイト数（デフォルト: 16MB） |

### 例

```bash
# 推奨: イーガー検索モード2、100x100以上の画像のみ。最大バイト数を8MBに制限（高速探索）
python salvageJpg.py disk.img -e2 -s 100 -m $((16*1024*1024)) -o ./recovered_images/
```

## 出力

復元されたファイルは、見つかったアドレス位置をファイル名として保存されます。

例: `0000000000123abc.jpg`

## 依存パッケージ

- Pillow >= 12.2.0
- NumPy >= 2.4.4

## ライセンス

MIT

---

# JPEGSalvage (English)

A tool to recover JPEG image data from corrupted binary streams.

## Overview

JPEGSalvage recovers lost JPEG images by searching for JPEG markers (SOI/EOI) in binary regions, which is useful during disk recovery or when file systems are corrupted.

***Warning!***  
Reading from a physically damaged disk without proper care can make the situation worse.  
If you do not fully understand what this means, stop and seek help from a professional data recovery service.

## Features

- **JPEG Marker Detection**: Detects SOI (Start of Image: `0xFFD8`) and EOI (End of Image: `0xFFD9`) markers
- **Multiple Search Strategies**:
  - Standard search: Search forward from SOI for EOI
  - Eager search mode 1: Search backward from SOI for EOI (retains more data)
  - **Recommended**: Eager search mode 2: Search forward from SOI for EOI (efficient)
- **Filtering**: Filter detection results by image size
- **Memory Efficient**: Chunk-based processing supports large files

## Setup

### Using venv

```bash
git clone https://github.com/fujiyama9198/SalvageJPG
cd SalvageJPG
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Using uv

```bash
git clone https://github.com/fujiyama9198/SalvageJPG
cd SalvageJPG
uv sync
```

## Usage

First, you need to create a disk image from the disk. If the disk may be physically damaged, `ddrescue` is also worth considering, but in many cases a professional recovery service is the safer choice than handling the disk casually.

```bash
sudo dd if=/dev/disk_number of=disk.img conv=noerror,sync
```

Then run this tool:

```bash
python salvageJpg.py <input_file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --outdir` | Output directory (default: same name as input file) |
| `-s, --filter-by-size` | Save only images with longest edge exceeding this value (pixels) |
| `-e, --eager` | Use eager search (`-e1` or `-e2`) |
| `-m, --max-bytes` | Maximum bytes to read from each JPEG (default: 16MB) |

### Examples

```bash
# Recommended: Eager search mode 2, save only images 100x100 or larger, under the size of 16MB
python salvageJpg.py disk.img -e2 -s 100 -m $((16*1024*1024)) -o ./recovered_images/

```

## Output

Recovered files are saved with the found address position as the filename.

Example: `0000000000123abc.jpg`

## Dependencies

- Pillow >= 12.2.0
- NumPy >= 2.4.4

## License

MIT
