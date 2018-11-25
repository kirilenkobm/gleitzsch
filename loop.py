#!/usr/bin/env python3
"""Compress and decompress the image 1000 times and make a gif of it."""
import argparse
import os
import sys
import shutil
import subprocess
from tqdm import tqdm
from skimage import io
import imageio


def parse_args():
    """Argumnent parser."""
    app = argparse.ArgumentParser()
    app.add_argument("input_file")
    app.add_argument("frames_folder")
    app.add_argument("output_gif")
    app.add_argument("--frames_num", default=250, type=int)
    app.add_argument("--remove_frames", action="store_true", dest="remove_frames")
    args = app.parse_args()
    return args


def main():
    """Entry point"""
    args = parse_args()
    os.mkdir(args.frames_folder) if not os.path.isdir(args.frames_folder) else None
    cmd_template = "./gleitzsch.py {0} {1} --size 500"
    # initial round
    init_file = os.path.join(args.frames_folder, "0.jpg")
    files = [init_file]
    init_cmd = cmd_template.format(args.input_file, init_file)
    rc = subprocess.call(init_cmd, shell=True)
    if rc != 0:
        sys.stderr.write("Error! Gleitzsch died!\n")
        sys.exit(1)

    for i in tqdm(range(args.frames_num)):
        prev_file = os.path.join(args.frames_folder, "{}.jpg".format(i))
        new_file = os.path.join(args.frames_folder, "{}.jpg".format(i + 1))
        iter_cmd = cmd_template.format(prev_file, new_file)
        subprocess.call(iter_cmd, shell=True, stderr=subprocess.DEVNULL)
        files.append(new_file) if i % 2 == 0 else None
        # sys.stderr.write("{}/{}\n".format(i, args.frames_num))

    # frame_files = [os.path.join(args.frames_folder, x) for x in files]
    frames = [io.imread(x) for x in files]
    imageio.mimsave(args.output_gif, frames)
    shutil.rmtree(args.frames_folder) if os.path.isdir(args.frames_folder) and args.remove_frames else None


if __name__ == "__main__":
    main()
