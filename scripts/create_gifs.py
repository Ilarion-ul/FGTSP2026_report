#!/usr/bin/env python3
"""Create GIF animations for the presentation from simulation PNG frames.

Outputs by default go to: generated_gifs/
- plate_neutron_heatmap_W-Ta.gif
- plate_neutron_heatmap_U-Mo.gif
- beam_visualization_W-Ta.gif
- beam_visualization_U-Mo.gif
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable


TARGET_RUNS = {
    "W-Ta": Path("Data/20260211_172835_W-Ta"),
    "U-Mo": Path("Data/20260212_072836_U-Mo"),
}


def load_image(path: Path):
    try:
        from PIL import Image
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Pillow is required. Install with: pip install pillow"
        ) from exc
    return Image.open(path).convert("RGB")


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
    frames: list[Path] = []
    for name in preferred:
        p = run_dir / name
        if p.exists():
            frames.append(p)
    return frames


def write_gif(frame_paths: Iterable[Path], out_path: Path, duration_ms: int) -> None:
    frame_paths = list(frame_paths)
    if not frame_paths:
        raise ValueError(f"No frames provided for GIF: {out_path}")

    images = [load_image(p) for p in frame_paths]
    first, rest = images[0], images[1:]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    first.save(
        out_path,
        save_all=True,
        append_images=rest,
        duration=duration_ms,
        loop=0,
        optimize=False,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GIFs used in presentation slides")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("generated_gifs"),
        help="Output directory for generated GIF files",
    )
    parser.add_argument(
        "--duration-ms",
        type=int,
        default=700,
        help="Frame duration in milliseconds",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List discovered frame sets and planned outputs without creating GIFs",
    )
    args = parser.parse_args()

    created: list[Path] = []

    for target, run_dir in TARGET_RUNS.items():
        if not run_dir.exists():
            print(f"[skip] Missing run directory: {run_dir}")
            continue

        heatmap_frames = collect_heatmap_frames(run_dir)
        if heatmap_frames:
            out = args.output_dir / f"plate_neutron_heatmap_{target}.gif"
            if args.list:
                print(f"[plan] {out} <- {len(heatmap_frames)} frames")
            else:
                write_gif(heatmap_frames, out, args.duration_ms)
                created.append(out)
        else:
            print(f"[skip] No heatmap frames in {run_dir}")

        beam_frames = collect_beam_frames(run_dir)
        if beam_frames:
            out = args.output_dir / f"beam_visualization_{target}.gif"
            if args.list:
                print(f"[plan] {out} <- {len(beam_frames)} frames")
            else:
                write_gif(beam_frames, out, args.duration_ms)
                created.append(out)
        else:
            print(f"[skip] No beam visualization frames in {run_dir}")

    if args.list:
        return

    if created:
        print("Created GIF files:")
        for path in created:
            print(f" - {path}")
    else:
        print("No GIF files were created.")


if __name__ == "__main__":
    main()
