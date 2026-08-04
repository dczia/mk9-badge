#!/usr/bin/env python3
"""
Watches for RP2040s in UF2 bootloader mode (RPI-RP2 drives) and
automatically copies a given .uf2 file onto each one as soon as it appears.

Multiple boards can be plugged in at the same time (or staggered): every
drive that shows up gets flashed concurrently on its own thread, so you're
not stuck plugging boards in one at a time and waiting for each to reboot
before the next is noticed.

Usage:
    python auto_flash.py path\\to\\firmware.uf2
    python auto_flash.py path\\to\\firmware.uf2 --once
"""
import argparse
import os
import platform
import sys
import threading
import time

MARKER_FILE = "INFO_UF2.TXT"  # present at the root of every RP2040 bootloader drive

print_lock = threading.Lock()


def candidate_mounts():
    """Yield plausible mount points to check, per platform."""
    system = platform.system()
    if system == "Windows":
        import string
        from ctypes import windll

        bitmask = windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate(string.ascii_uppercase):
            if bitmask & (1 << i):
                yield f"{letter}:\\"
    elif system == "Darwin":
        base = "/Volumes"
        if os.path.isdir(base):
            for name in os.listdir(base):
                yield os.path.join(base, name)
    else:  # Linux and other POSIX
        for base in (
            f"/media/{os.environ.get('USER', '')}",
            "/run/media",
            "/mnt",
            "/media",
        ):
            if os.path.isdir(base):
                for name in os.listdir(base):
                    yield os.path.join(base, name)


def find_rp2040_bootloaders():
    """Return the mount paths of every RP2040 bootloader drive currently present."""
    found = []
    for mount in candidate_mounts():
        try:
            if os.path.isfile(os.path.join(mount, MARKER_FILE)):
                found.append(mount)
        except OSError:
            continue
    return found


def log(mount, msg):
    """Thread-safe print, prefixed with the drive so concurrent flashes stay readable."""
    label = mount.rstrip("\\/") or mount
    with print_lock:
        print(f"[{label}] {msg}")


def flash(uf2_path, mount, retries=5, delay=0.5, chunk_size=64 * 1024):
    dest = os.path.join(mount, os.path.basename(uf2_path))
    total = os.path.getsize(uf2_path)
    for attempt in range(1, retries + 1):
        try:
            copied = 0
            start = time.monotonic()
            last_pct = -1
            with open(uf2_path, "rb") as src, open(dest, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied += len(chunk)
                    pct = int(copied / total * 100) if total else 100
                    # Discrete milestone lines (not a \r progress bar) -- multiple
                    # threads writing to the same terminal would otherwise garble
                    # each other's carriage-return updates.
                    if pct >= last_pct + 10:
                        elapsed = time.monotonic() - start
                        speed_kb = (copied / 1024 / elapsed) if elapsed > 0 else 0.0
                        log(mount, f"{pct:3d}%  {copied / 1024:.0f}/{total / 1024:.0f} KB  {speed_kb:.0f} KB/s")
                        last_pct = pct
            return True
        except OSError as e:
            if attempt == retries:
                log(mount, f"copy failed: {e}")
                return False
            time.sleep(delay)
    return False


def flash_worker(uf2_path, mount, state, state_lock):
    log(mount, "found board -- flashing...")
    ok = flash(uf2_path, mount)
    with state_lock:
        state["in_progress"].discard(mount)
        state["done_waiting_removal"].add(mount)
        if ok:
            state["flashed_count"] += 1
            count = state["flashed_count"]
    if ok:
        log(mount, f"done ({count} flashed so far) -- unplug or wait for reboot")
    else:
        log(mount, "flash failed -- unplug and retry")


def main():
    parser = argparse.ArgumentParser(
        description="Auto-flash a UF2 file to any RP2040(s) that appear in bootloader mode."
    )
    parser.add_argument("uf2", help="Path to the .uf2 file to flash")
    parser.add_argument(
        "--interval", type=float, default=0.5, help="Poll interval in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Flash whichever board(s) are currently connected, then exit once they've "
        "all finished, instead of looping forever",
    )
    args = parser.parse_args()

    uf2_path = os.path.abspath(args.uf2)
    if not os.path.isfile(uf2_path):
        sys.exit(f"UF2 file not found: {uf2_path}")

    print(f"Watching for RP2040 bootloader devices... (uf2: {uf2_path})")
    print("Plug in one or more boards in bootloader mode -- each is flashed as soon as it's detected.")
    print("Press Ctrl+C to stop.")

    state = {"in_progress": set(), "done_waiting_removal": set(), "flashed_count": 0}
    state_lock = threading.Lock()
    threads = []

    try:
        while True:
            current = set(find_rp2040_bootloaders())

            with state_lock:
                # Forget drives that have gone away, so if the same drive letter
                # is reused by a freshly-plugged board later, it's flashed again
                # instead of being treated as "already done".
                state["done_waiting_removal"] &= current
                new_mounts = current - state["in_progress"] - state["done_waiting_removal"]
                state["in_progress"] |= new_mounts

            for mount in new_mounts:
                t = threading.Thread(
                    target=flash_worker, args=(uf2_path, mount, state, state_lock), daemon=True
                )
                t.start()
                threads.append(t)

            with state_lock:
                idle = not state["in_progress"]
                have_flashed = state["flashed_count"] > 0

            if args.once and have_flashed and idle:
                break

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopping... waiting for in-flight flashes to finish.")

    for t in threads:
        t.join()
    print(f"Total flashed: {state['flashed_count']}")


if __name__ == "__main__":
    main()
