import shutil
import urllib.request
from pathlib import Path

USER_AGENT = "bdf-movielens-project"


def download_file(url: str, dest_dir: Path, chunk_size: int = 1024 * 1024) -> Path:
    """Stream `url` into `dest_dir`, skipping files that already exist."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / url.rsplit("/", 1)[-1]
    if dest.exists():
        print(f"skip   {dest.name} (already downloaded)")
        return dest

    tmp = dest.with_suffix(dest.suffix + ".part")  # avoid leaving partial files
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    print(f"get    {url}")
    try:
        with urllib.request.urlopen(request) as response, open(tmp, "wb") as out:
            shutil.copyfileobj(response, out, chunk_size)
        tmp.replace(dest)
    finally:
        tmp.unlink(missing_ok=True)
    print(f"saved  {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest
