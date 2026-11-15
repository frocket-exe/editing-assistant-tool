import json
import subprocess
import os

# ffmpeg -f lavfi -i "sine=frequency=2000:duration=10" output.mp3
os.makedirs(os.path.dirname("censor/"), exist_ok=True)

with open("json/swears.json", "r") as f:
    data = json.load(f)


def silenceSwears():
    inputVidePath = "media/testVideo04.mp4"
    swears = (data["timestamps"])
    cmd = ["ffmpeg", "-y", "-i", inputVidePath, "-vcodec", "copy", "-af"]
    audioFilter = ""
    for swear in swears:
        audioFilter += (f"volume=enable='between(t,{swear["start"]},{swear["end"]})':volume=0, ")
    audioFilter = audioFilter[:-2]
    cmd.append(audioFilter)
    cmd.append("censor/silencedSwears.mp4")
    subprocess.run(cmd)


def generateBleep():
    duration = data["duration"]
    swears = (data["timestamps"])
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
    print(cmd)
    subprocess.run(cmd)

def combineBleep():
    # ffmpeg -i video.mkv -i audio.m4a -filter_complex "[0:a][1:a]amerge=inputs=2[a]" -map 0:v -map "[a]" -c:v copy -ac 2 -shortest output.mkv
    cmd = ["ffmpeg", "-y", "-i", "censor/silencedSwears.mp4", "-i", "censor/bleepTimed.mp3", "-filter_complex", "[0:a][1:a]amerge=inputs=2[a]", "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-ac", "2", "-shortest", "censor/censoredVideo.mp4"]
    print(cmd)
    subprocess.run(cmd)

# generateBleep()
combineBleep()