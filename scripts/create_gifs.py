#!/usr/bin/env python3
"""Prepare numbered PNG frame sequences for Beamer animategraphics."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def pick_latest_dir(pattern: str, fallback: str) -> Path:
    candidates = sorted(Path("Data").glob(pattern))
    if candidates:
        return candidates[-1]
    return Path(fallback)


TARGET_RUNS = {
    "W-Ta": Path("Data/20260211_172835_W-Ta"),
    "U-Mo": pick_latest_dir("*_U-Mo", "Data/20260212_072836_U-Mo"),
}


def collect_heatmap_frames(run_dir: Path) -> list[Path]:
    return sorted(
        run_dir.glob("plate_neutron_heatmap_*.png"),
        key=lambda p: int(p.stem.split("_")[-1]),
    )


def collect_beam_frames(run_dir: Path) -> list[Path]:
    preferred = [
        "h2_edep_xy_mid.png",
        "edep_3d_xy.png",
        "edep_3d_xz.png",
        "edep_3d_yz.png",
        "h2_neutron_exit_xy_upstream.png",
        "h2_neutron_exit_xy_downstream.png",
        "h2_neutron_exit_xz_side_y.png",
        "h2_neutron_exit_yz_side_x.png",
        "h2_neutron_exit_side_surface.png",
    ]
    return [run_dir / name for name in preferred if (run_dir / name).exists()]


def copy_sequence(frames: list[Path], out_prefix: Path, dry_run: bool) -> list[Path]:
    created: list[Path] = []
    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    for i, src in enumerate(frames):
        dst = out_prefix.parent / f"{out_prefix.name}{i:03d}.png"
        created.append(dst)
        if not dry_run:
            shutil.copy2(src, dst)
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Build PNG frame sequences for Beamer animations")
    parser.add_argument("--output-dir", type=Path, default=Path("generated_gifs"))
    parser.add_argument("--dry-run", action="store_true", help="Show planned outputs only")
    args = parser.parse_args()

    for target, run_dir in TARGET_RUNS.items():
        if not run_dir.exists():
            print(f"[skip] missing run directory: {run_dir}")
            continue

        heatmap = collect_heatmap_frames(run_dir)
        beam = collect_beam_frames(run_dir)

        heatmap_out = args.output_dir / f"plate_neutron_heatmap_{target}_"
        beam_out = args.output_dir / f"beam_visualization_{target}_"

        created_h = copy_sequence(heatmap, heatmap_out, args.dry_run) if heatmap else []
        created_b = copy_sequence(beam, beam_out, args.dry_run) if beam else []

        print(f"[dir] {target}: {run_dir}")
        if heatmap:
            print(f"[ok] {target} heatmap frames: {len(created_h)} -> {heatmap_out}000...{len(created_h)-1:03d}.png")
        else:
            print(f"[skip] no heatmap frames for {target}")

        if beam:
            print(f"[ok] {target} beam frames: {len(created_b)} -> {beam_out}000...{len(created_b)-1:03d}.png")
        else:
            print(f"[skip] no beam frames for {target}")


if __name__ == "__main__":
    main()
