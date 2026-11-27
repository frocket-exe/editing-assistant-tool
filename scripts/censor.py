import json
import subprocess
import os

# cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", inputVideoPath]
# result = subprocess.run(cmd, capture_output=True, text=True).stdout
# duration = float(json.loads(result)["streams"][0]["duration"])


def silenceSwears(inputVideoPath, outputVideoPath):
    with open("json/swears.json", "r") as f:
        swears = json.load(f)
    cmd = ["ffmpeg", "-y", "-i", inputVideoPath, "-vcodec", "copy", "-af"]
    audioFilter = ""
    for swear in swears:
        audioFilter += (f"volume=enable='between(t,{swear["start"]},{swear["end"]})':volume=0, ")
    audioFilter = audioFilter[:-2]
    cmd.append(audioFilter)
    cmd.append(outputVideoPath)
    subprocess.run(cmd)


def generateBleep(duration):
    with open("json/swears.json", "r") as f:
            swears = json.load(f)
    cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", f'sine=frequency=1000:duration={duration}', "censor/bleep.mp3"]
    subprocess.run(cmd)
    cmd = ["ffmpeg", "-y", "-i", "censor/bleep.mp3", "-af"]
    swears.insert(0, {'end': 0})
    swears.append({'start': duration})
    audioFilter = ""
    for i in range(len(swears)-1):
        audioFilter += (f"volume=enable='between(t,{swears[i]["end"]},{swears[i+1]["start"]})':volume=0, ")
    audioFilter = audioFilter[:-2]
    cmd.append(audioFilter)
    cmd.append("censor/bleepTimed.mp3")
    subprocess.run(cmd)

def combineBleep(silencedVideoPath, outputVideoPath):
    cmd = ["ffmpeg", "-y", "-i", silencedVideoPath, "-i", "censor/bleepTimed.mp3", "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-ac", "2", "-shortest", outputVideoPath]
    subprocess.run(cmd)
