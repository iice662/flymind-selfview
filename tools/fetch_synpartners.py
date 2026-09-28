"""Resumable downloader for the MaleCNS v1.0 synaptic-partner table.

Usage:
    python tools/fetch_synpartners.py [--url URL] [--dest PATH] [--check]

Why a purpose-written downloader: the release bucket throttles single connections to
~0.5 MB/s, so the 6.8 GB table needs a resumable fetch that can be interrupted and
restarted without losing ground.  No third-party dependency is used anywhere in this
project, so this is plain urllib.

The table's columns are:
    x_pre, y_pre, z_pre, body_pre, conf_pre,
    x_post, y_post, z_post, body_post, conf_post, primary_post
`primary_post` is the neuropil of the postsynaptic site, so filtering rows by
`body_post == <id>` gives the neuropil distribution of that cell's *input* -- which is
the receptive-field proxy used by tools/receptive_field.py.
"""

import argparse
import hashlib
import os
import sys
import time
import urllib.request

DEFAULT_URL = ("https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/"
               "flat-connectome/syn-partners-male-cns-v1.0-minconf-0.5.feather")
DEFAULT_DEST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "malecns", "syn-partners.feather")
CHUNK = 4 << 20


def remote_size(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def sha256(path, limit=None):
    h = hashlib.sha256()
    read = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            h.update(b)
            read += len(b)
            if limit and read >= limit:
                break
    return h.hexdigest().upper()


def fetch(url, dest):
    total = remote_size(url)
    have = os.path.getsize(dest) if os.path.exists(dest) else 0
    if have > total:
        print(f"local file larger than remote ({have} > {total}); restarting", flush=True)
        os.remove(dest)
        have = 0
    if have == total:
        print(f"already complete: {dest} ({total:,} bytes)", flush=True)
        return total
    mode = "ab" if have else "wb"
    print(f"downloading {url}\n  -> {dest}\n  {have:,} / {total:,} bytes "
          f"({100.0 * have / total:.1f}% already present)", flush=True)
    t0 = time.time()
    done = have
    last = 0.0
    with open(dest, mode) as out:
        while done < total:
            req = urllib.request.Request(url, headers={"Range": f"bytes={done}-"})
            try:
                with urllib.request.urlopen(req, timeout=120) as r:
                    while True:
                        b = r.read(CHUNK)
                        if not b:
                            break
                        out.write(b)
                        done += len(b)
                        now = time.time()
                        if now - last > 15:
                            last = now
                            el = now - t0
                            rate = (done - have) / el / 1e6 if el > 0 else 0
                            eta = (total - done) / (rate * 1e6) / 60 if rate > 0 else float("nan")
                            print(f"  {done:,} / {total:,}  {100.0 * done / total:5.1f}%  "
                                  f"{rate:.2f} MB/s  ETA {eta:.1f} min", flush=True)
                        if done >= total:
                            break
            except Exception as e:  # transient network error: resume from where we are
                print(f"  interrupted at {done:,} ({type(e).__name__}: {e}); resuming in 10 s",
                      flush=True)
                time.sleep(10)
                done = os.path.getsize(dest)
    print(f"complete: {dest} ({os.path.getsize(dest):,} bytes) in "
          f"{(time.time() - t0) / 60:.1f} min", flush=True)
    print(f"SHA256 {sha256(dest)}", flush=True)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--dest", default=DEFAULT_DEST)
    ap.add_argument("--check", action="store_true",
                    help="verify size and print SHA256 without downloading")
    a = ap.parse_args()
    os.makedirs(os.path.dirname(a.dest), exist_ok=True)
    if a.check:
        if not os.path.exists(a.dest):
            print("missing:", a.dest)
            return 1
        total = remote_size(a.url)
        have = os.path.getsize(a.dest)
        print(f"{a.dest}\n  local  {have:,}\n  remote {total:,}\n  "
              f"{'COMPLETE' if have == total else 'INCOMPLETE'}")
        print(f"  SHA256 {sha256(a.dest)}")
        return 0 if have == total else 1
    fetch(a.url, a.dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
