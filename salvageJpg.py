from PIL import Image
import io
import argparse
import pathlib




def search_jpg(f):
    data_bytes = f.read()
    found_data = []
    start_idx = 0
    while True:
        try:
            pos_sb = data_bytes.index(b'\xFF\xD8', start_idx)
            pos_eb = data_bytes.index(b'\xFF\xD9', pos_sb) + 2
            found_data.append((data_bytes[pos_sb:pos_eb], pos_sb, pos_eb - pos_sb))
            start_idx = pos_eb
        except ValueError:
            break
    return found_data


def search_jpg_eager(f: io.FileIO, outdir: pathlib.Path, filt_by_size=None):
    data_bytes = f.read()

    start_idx = 0
    pos_sb_arr = []
    while True:
        try:
            # スタートバイト位置を決める
            pos_sb = data_bytes.index(b'\xFF\xD8', start_idx)
            pos_sb_arr.append(pos_sb)
            start_idx = pos_sb + 2
        except ValueError:
            break

    for i, pos_sb in enumerate(pos_sb_arr):
        print(f"{pos_sb:016x} - {i} of {len(pos_sb_arr)}")
        end_idx_eb = len(data_bytes)
        while True:
            # 後方からエンドバイトを探す。見つからない場合、そのスタートバイト位置を諦めて次へ
            try:
                pos_eb = data_bytes.rindex(b'\xFF\xD9', pos_sb, end_idx_eb)
            except ValueError:
                break

            # 見つかったエンドバイトまででJPEGデコードを試みる。
            # デコードに成功した場合、スタートバイト位置を見つかったエンドバイト以後にして探索に戻る
            # デコードに成功しない場合は、現在のエンドバイト位置以前にエンドバイトを探しに戻る
            try:
                with io.BytesIO(data_bytes[pos_sb:pos_eb]) as rf:
                    jpg = Image.open(rf)
                    exif = jpg.getexif()
                    print(f"Found: {pos_sb:016x}, {jpg.size}")

                    if filt_by_size is None or max(jpg.size) >= filt_by_size:
                        outdir.mkdir(exist_ok=True, parents=True)
                        outpath = outdir / f'{pos_sb:016x}.jpg'
                        # jpg.save(outpath.open("wb"), exif=exif)
                        with open("/dev/null", "wb") as wn:
                            jpg.rotate(0).save(wn)
                        with outpath.open("wb") as wf:
                            wf.write(data_bytes[pos_sb:pos_eb])
                break
            except:
                end_idx_eb = pos_eb - 2


def search_jpg_eager2(f: io.FileIO, outdir: pathlib.Path, filt_by_size=None):
    data_bytes = f.read()
    # found_data = []

    start_idx = 0
    pos_sb_arr = []
    while True:
        try:
            # スタートバイト位置を決める
            pos_sb = data_bytes.index(b'\xFF\xD8', start_idx)
            pos_sb_arr.append(pos_sb)
            start_idx = pos_sb + 2
        except ValueError:
            break

    for i, pos_sb in enumerate(pos_sb_arr):
        print(f"{pos_sb:016x} - {i} of {len(pos_sb_arr)}")
        start_idx_eb = len(data_bytes)
        while True:
            # 前方からエンドバイトを探す。見つからない場合、そのスタートバイト位置を諦めて次へ
            try:
                pos_eb = data_bytes.index(b'\xFF\xD9', start_idx_eb) + 2
            except ValueError:
                break

            # 見つかったエンドバイトまででJPEGデコードを試みる。
            # デコードに成功しない場合は、現在のエンドバイト位置以降にエンドバイトを探しに戻る
            try:
                with io.BytesIO(data_bytes[pos_sb:pos_eb]) as rf:
                    jpg = Image.open(rf)
                    exif = jpg.getexif()
                    print(f"Found: {pos_sb:016x}, {jpg.size}")

                    if filt_by_size is None or max(jpg.size) >= filt_by_size:
                        outdir.mkdir(exist_ok=True, parents=True)
                        outpath = outdir / f'{pos_sb:016x}.jpg'
                        with outpath.open("wb") as wf:
                            wf.write(data_bytes[pos_sb:pos_eb])
                        # jpg.save(outpath.open("wb"), exif=exif)
                break
            except:
                start_idx_eb = pos_eb
    # return found_data


def main():
    parser = argparse.ArgumentParser(description="Finds and salvages JPEG data from byte stream")
    parser.add_argument("input", type=pathlib.Path, help="File of binary stream")
    parser.add_argument("--outdir", "-o", default=None, type=pathlib.Path, help="Output directory. Default: same as input file name")
    parser.add_argument("--filter-by-size", "-s", default=None, type=int, help="Save only if the length of image exceeds this")
    parser.add_argument("--eager", "-e", nargs='?', default=None, const="1")
    args = parser.parse_args()

    if args.eager == "1":
        with args.input.open("rb") as f:
            outdir = args.outdir
            if outdir is None:
                outdir = args.input.with_suffix("")
            found_jpgs = search_jpg_eager(f, outdir, filt_by_size=args.filter_by_size)
    elif args.eager == "2":
        with args.input.open("rb") as f:
            outdir = args.outdir
            if outdir is None:
                outdir = args.input.with_suffix("")
            found_jpgs = search_jpg_eager2(f, outdir, filt_by_size=args.filter_by_size)
    else:
        with args.input.open("rb") as f:
            outdir = args.outdir
            if outdir is None:
                outdir = args.input.with_suffix("")
            found_jpgs = search_jpg(f)
        for jpg, addr, size in found_jpgs:
            print(f"{addr:016x}: {size:9d}")
            outdir.mkdir(exist_ok=True, parents=True)
            outpath = outdir / f'{addr:016x}.jpg'
            with outpath.open("wb") as wf:
                wf.write(jpg)
            # Image.open(io.BytesIO(jpg)).save(outpath)


if __name__ == "__main__":
    main()



