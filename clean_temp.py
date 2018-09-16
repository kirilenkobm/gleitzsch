#!/usr/bin/env python3
"""Check temp dir every day and remove too old files."""
import subprocess
from time import sleep

TEMP = "temp"
cmd = "find {0} -mtime +1 -type f -delete".format(TEMP)

if __name__ == "__main__":
    while True:  # remove and sleep
        subprocess.call(cmd, shell=True)
        sleep(86400)
