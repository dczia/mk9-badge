#!/usr/bin/env python3
"""
Watches for an RP2040 in UF2 bootloader mode (RPI-RP2 drive) and
automatically copies a given .uf2 file onto it as soon as it appears.

Loops forever by default so you can batch-flash boards one after another:
plug one in, it flashes and the board reboots (unmounting the drive),
unplug it, plug in the next one.

Usage:
    python auto_flash.py path\to\firmware.uf2
    python auto_flash.py path\to\firmware.uf2 --once
"""
import argparse
import os
import platform
import sys
import time

MARKER_FILE = "INFO_UF2.TXT"  # present at the root of every RP2040 bootloader drive


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


def find_rp2040_bootloader():
    """Return the mount path of an RP2040 bootloader drive, or None."""
    for mount in candidate_mounts():
        try:
            if os.path.isfile(os.path.join(mount, MARKER_FILE)):
                return mount
        except OSError:
            continue
    return None


def print_progress(copied, total, start_time):
    pct = (copied / total * 100) if total else 100.0
    elapsed = time.monotonic() - start_time
    speed_kb = (copied / 1024 / elapsed) if elapsed > 0 else 0.0
    bar_width = 30
    filled = int(bar_width * copied / total) if total else bar_width
    bar = "#" * filled + "-" * (bar_width - filled)
    print(
        f"\r  [{bar}] {pct:5.1f}%  {copied / 1024:.0f}/{total / 1024:.0f} KB  {speed_kb:.0f} KB/s",
        end="",
        flush=True,
    )


def flash(uf2_path, mount, retries=5, delay=0.5, chunk_size=64 * 1024):
    dest = os.path.join(mount, os.path.basename(uf2_path))
    total = os.path.getsize(uf2_path)
    for attempt in range(1, retries + 1):
        try:
            copied = 0
            start = time.monotonic()
            with open(uf2_path, "rb") as src, open(dest, "wb") as dst:
                while True:
                    chunk = src.read(chunk_size)
                    if not chunk:
                        break
                    dst.write(chunk)
                    copied += len(chunk)
                    print_progress(copied, total, start)
            print()  # move past the progress line
            return True
        except OSError as e:
            print()
            if attempt == retries:
                print(f"  copy failed: {e}")
                return False
            time.sleep(delay)
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Auto-flash a UF2 file to any RP2040 that appears in bootloader mode."
    )
    parser.add_argument("uf2", help="Path to the .uf2 file to flash")
    parser.add_argument(
        "--interval", type=float, default=0.5, help="Poll interval in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--once", action="store_true", help="Flash a single board then exit, instead of looping forever"
    )
    args = parser.parse_args()

    uf2_path = os.path.abspath(args.uf2)
    if not os.path.isfile(uf2_path):
        sys.exit(f"UF2 file not found: {uf2_path}")

    print(f"Watching for RP2040 bootloader devices... (uf2: {uf2_path})")
    print("Press Ctrl+C to stop.")

    flashed_count = 0
    try:
        while True:
            mount = find_rp2040_bootloader()
            if mount:
                print(f"Found RPI-RP2 at {mount} -- flashing...")
                if flash(uf2_path, mount):
                    flashed_count += 1
                    print(f"  done ({flashed_count} flashed so far)")
                    if args.once:
                        break
                # Wait for this drive to go away before watching again, so we
                # don't try to flash the same board twice while it reboots.
                print("Waiting for board to reboot...")
                while find_rp2040_bootloader() == mount:
                    time.sleep(args.interval)
                print("Waiting for next board...")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
