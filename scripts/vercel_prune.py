"""Build hook Vercel: pangkas site-packages sebelum fungsi di-bundle.

Dijalankan lewat buildCommand (vercel.json) setelah dependensi terpasang.
Membuang folder tests/ dan __pycache__/ menekan ukuran bundle tanpa
mengubah perilaku runtime (folder tests tidak pernah diimpor library).
"""
from __future__ import annotations

import argparse
import shutil
import sysconfig
from pathlib import Path

TARGET_DIRS = {"tests", "__pycache__"}


def _site_package_roots() -> set[Path]:
    paths = sysconfig.get_paths()
    roots = {Path(paths["purelib"]), Path(paths["platlib"])}
    roots.update(p for p in Path.cwd().rglob("site-packages") if p.is_dir())
    return {r for r in roots if r.is_dir()}


def prune(dry_run: bool) -> int:
    victims: set[Path] = set()
    for root in _site_package_roots():
        victims.update(
            d for d in root.rglob("*") if d.is_dir() and d.name in TARGET_DIRS
        )

    freed = 0
    # Terdalam dulu agar induk yang ikut terhapus tidak dihitung dua kali.
    for directory in sorted(victims, key=lambda p: len(p.parts), reverse=True):
        if not directory.exists():
            continue
        size = sum(f.stat().st_size for f in directory.rglob("*") if f.is_file())
        freed += size
        prefix = "[dry-run] " if dry_run else ""
        print(f"{prefix}hapus {directory} ({size / 1048576:.1f} MB)")
        if not dry_run:
            shutil.rmtree(directory)

    print(f"total dipangkas: {freed / 1048576:.1f} MB")
    return freed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    prune(dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
