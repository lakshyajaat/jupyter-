#!/usr/bin/env python3
# split_dataset.py  -- safe copy-based splitter for ImageFolder layout

import argparse
from pathlib import Path
import random
import shutil

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', required=True, type=str, help="root data dir containing class subfolders")
    p.add_argument('--ratios', nargs=3, type=float, default=(0.8,0.1,0.1), help="train val test ratios")
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--move', action='store_true', help="move files instead of copying")
    args = p.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        raise SystemExit(f"data dir not found: {data_dir}")

    # Prevent accidental overwrite
    if any((data_dir / s).exists() for s in ('train','val','test')):
        raise SystemExit("train/val/test already exist under data/. Remove them first if you want to recreate.")

    random.seed(args.seed)

    # find class folders (direct children that are directories)
    class_dirs = [p for p in sorted(data_dir.iterdir()) if p.is_dir() and p.name not in ('train','val','test')]
    if not class_dirs:
        raise SystemExit("No class subfolders found in data_dir.")

    print(f"Found classes: {[p.name for p in class_dirs]}")
    for cls in class_dirs:
        imgs = [f for f in cls.iterdir() if f.is_file()]
        random.shuffle(imgs)
        n = len(imgs)
        t = int(args.ratios[0] * n)
        v = int(args.ratios[1] * n)
        splits = {
            'train': imgs[:t],
            'val': imgs[t:t+v],
            'test': imgs[t+v:],
        }
        for split_name, file_list in splits.items():
            outdir = data_dir / split_name / cls.name
            outdir.mkdir(parents=True, exist_ok=True)
            for f in file_list:
                if args.move:
                    shutil.move(str(f), str(outdir / f.name))
                else:
                    shutil.copy2(str(f), str(outdir / f.name))
        print(f"Class {cls.name}: total={n} -> train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")

    print("Done. train/val/test created under", data_dir)

if __name__ == '__main__':
    main()
