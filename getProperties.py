import os
import json
import subprocess

mediaFolder = "media/"

files = os.listdir(mediaFolder)
for file in files:
    print(file)

videoPath = mediaFolder + files[0]
print(videoPath)

cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", videoPath]
result = subprocess.run(cmd, capture_output=True, text=True).stdout
print(result)

with open("videoMetrics.json", "w") as f:
    f.write(result)
    f.close()