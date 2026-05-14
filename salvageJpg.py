from PIL import Image
import io
import argparse
import pathlib

SOI = b'\xFF\xD8'
EOI = b'\xFF\xD9'


def _file_size(f: io.FileIO):
    cur = f.tell()
    f.seek(0, io.SEEK_END)
    size = f.tell()
    f.seek(cur, io.SEEK_SET)
    return size


def _find_next_marker(f: io.FileIO, marker: bytes, start: int, end: int, chunk_size: int = 1024 * 1024):
    f.seek(start, io.SEEK_SET)
    pos = start
    prev = b''
    overlap = len(marker) - 1
    while pos < end:
        n = min(chunk_size, end - pos)
        buf = f.read(n)
        if not buf:
            break
        data = prev + buf
        idx = data.find(marker)
        if idx != -1:
            return pos - len(prev) + idx
        prev = data[-overlap:] if overlap > 0 else b''
        pos += len(buf)
    return None


def _find_prev_marker(f: io.FileIO, marker: bytes, start: int, end: int, chunk_size: int = 1024 * 1024):
    overlap = len(marker) - 1
    pos = end
    while pos > start:
        read_start = max(start, pos - chunk_size)
        f.seek(read_start, io.SEEK_SET)
        buf = f.read(pos - read_start)
        idx = buf.rfind(marker)
        if idx != -1:
            return read_start + idx
        if read_start == start:
            break
        pos = read_start + overlap
    return None


def _read_range(f: io.FileIO, start: int, end: int):
    f.seek(start, io.SEEK_SET)
    return f.read(end - start)




def search_jpg(f: io.FileIO, max_bytes=None):
    found_data = []
    size = _file_size(f)
    start_idx = 0
    while True:
        pos_sb = _find_next_marker(f, SOI, start_idx, size)
        if pos_sb is None:
            break
        end_idx_eb = size if max_bytes is None else min(size, pos_sb + max_bytes)
        pos_eb = _find_next_marker(f, EOI, pos_sb + 2, end_idx_eb)
        if pos_eb is None:
            break
        end = pos_eb + 2
        jpg_bytes = _read_range(f, pos_sb, end)
        found_data.append((jpg_bytes, pos_sb, end - pos_sb))
        start_idx = end
    return found_data


def search_jpg_eager(f: io.FileIO, outdir: pathlib.Path, filt_by_size=None, max_bytes=None):
    size = _file_size(f)
    start_idx = 0
    pos_sb_arr = []
    while True:
        pos_sb = _find_next_marker(f, SOI, start_idx, size)
        if pos_sb is None:
            break
        pos_sb_arr.append(pos_sb)
        start_idx = pos_sb + 2

    for i, pos_sb in enumerate(pos_sb_arr):
        print(f"{pos_sb:016x} - {i} of {len(pos_sb_arr)}")
        end_idx_eb = size if max_bytes is None else min(size, pos_sb + max_bytes)
        while True:
            # 後方からエンドバイトを探す。見つからない場合、そのスタートバイト位置を諦めて次へ
            pos_eb = _find_prev_marker(f, EOI, pos_sb, end_idx_eb)
            if pos_eb is None:
                break

            # 見つかったエンドバイトまででJPEGデコードを試みる。
            # デコードに成功した場合、スタートバイト位置を見つかったエンドバイト以後にして探索に戻る
            # デコードに成功しない場合は、現在のエンドバイト位置以前にエンドバイトを探しに戻る
            try:
                end = pos_eb + 2
                candidate = _read_range(f, pos_sb, end)
                with io.BytesIO(candidate) as rf:
                    jpg = Image.open(rf)
                    print(f"Found: {pos_sb:016x}, {jpg.size}")

                    if filt_by_size is None or max(jpg.size) >= filt_by_size:
                        outdir.mkdir(exist_ok=True, parents=True)
                        outpath = outdir / f'{pos_sb:016x}.jpg'
                        # jpg.save(outpath.open("wb"), exif=exif)
                        jpg.verify()
                        with outpath.open("wb") as wf:
                            wf.write(candidate)
                break
            except:
                end_idx_eb = pos_eb


def search_jpg_eager2(f: io.FileIO, outdir: pathlib.Path, filt_by_size=None, max_bytes=None):
    size = _file_size(f)
    start_idx = 0
    pos_sb_arr = []
    while True:
        pos_sb = _find_next_marker(f, SOI, start_idx, size)
        if pos_sb is None:
            break
        pos_sb_arr.append(pos_sb)
        start_idx = pos_sb + 2

    for i, pos_sb in enumerate(pos_sb_arr):
        print(f"{pos_sb:016x} - {i} of {len(pos_sb_arr)}")
        start_idx_eb = pos_sb + 2
        while True:
            # 前方からエンドバイトを探す。見つからない場合、そのスタートバイト位置を諦めて次へ
            end_idx_eb = size if max_bytes is None else min(size, pos_sb + max_bytes)
            pos_eb = _find_next_marker(f, EOI, start_idx_eb, end_idx_eb)
            # print(pos_eb)
            if pos_eb is None or (max_bytes is not None and pos_eb > pos_sb + max_bytes):
                break
            pos_eb += 2

            # 見つかったエンドバイトまででJPEGデコードを試みる。
            # デコードに成功しない場合は、現在のエンドバイト位置以降にエンドバイトを探しに戻る
            try:
                end = pos_eb + 2
                candidate = _read_range(f, pos_sb, end)
                with io.BytesIO(candidate) as rf:
                    jpg = Image.open(rf)
                    print(f"Found: {pos_sb:016x}, {jpg.size}")

                    if filt_by_size is None or max(jpg.size) >= filt_by_size:
                        outdir.mkdir(exist_ok=True, parents=True)
                        outpath = outdir / f'{pos_sb:016x}.jpg'
                        with outpath.open("wb") as wf:
                            wf.write(candidate)
                        # jpg.save(outpath.open("wb"), exif=exif)
                break
            except:
                start_idx_eb = pos_eb
    # return found_data


def main():
    parser = argparse.ArgumentParser(description="Finds and salvages JPEG data from byte stream")
    parser.add_argument("input", type=pathlib.Path, help="File of binary stream")
    parser.add_argument("--outdir", "-o", default=None, type=pathlib.Path, help="Output directory. Default: same as input file name")
    parser.add_argument("--filter-by-size", "-s", default=None, type=int, help="Save only if the dimensionof image exceeds this")
    parser.add_argument("--eager", "-e", nargs='?', default=None, const="1", help="Eagerly search for JPEGs. 1: Search backward for EOI, 2: Search forward for EOI")
    parser.add_argument("--max-bytes", "-m", default=16*1024*1024, type=int, help="Maximum number of bytes to read from each JPEG (default: 16MB)")
    args = parser.parse_args()

    if args.eager == "1":
        with args.input.open("rb") as f:
            outdir = args.outdir
            if outdir is None:
                outdir = args.input.with_suffix("")
            found_jpgs = search_jpg_eager(f, outdir, filt_by_size=args.filter_by_size, max_bytes=args.max_bytes)
    elif args.eager == "2":
        with args.input.open("rb") as f:
            outdir = args.outdir
            if outdir is None:
                outdir = args.input.with_suffix("")
            found_jpgs = search_jpg_eager2(f, outdir, filt_by_size=args.filter_by_size, max_bytes=args.max_bytes)
    else:
        with args.input.open("rb") as f:
            outdir = args.outdir
            if outdir is None:
                outdir = args.input.with_suffix("")
            found_jpgs = search_jpg(f, max_bytes=args.max_bytes)
        for jpg, addr, size in found_jpgs:
            print(f"{addr:016x}: {size:9d}")
            outdir.mkdir(exist_ok=True, parents=True)
            outpath = outdir / f'{addr:016x}.jpg'
            with outpath.open("wb") as wf:
                wf.write(jpg)
            # Image.open(io.BytesIO(jpg)).save(outpath)


if __name__ == "__main__":
    main()



