import os
import json
import subprocess


# Probes video/audio for specific properties, defined in lists
# Writes these properties as clean json to a file to be used by other functions
def getProperties(PATH):
    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", PATH]
    result = subprocess.run(cmd, capture_output=True, text=True).stdout
    result = json.loads(result)

    generalData = ["codec_name", "codec_long_name", "duration", "bit_rate"]
    videoData = ["width", "height", "has_b_frames", "r_frame_rate"]
    audioData = ["sample_rate", "bits_per_sample", "channels"]
    metrics = {}

    for stream in result["streams"]:
        metrics[stream["codec_type"]] = {}
        for data in generalData:
            metrics[stream["codec_type"]][data] = stream[data]
        if stream["codec_type"] == "video":
            for data in videoData:
                metrics[stream["codec_type"]][data] = stream[data]
        if stream["codec_type"] == "audio":
            for data in audioData:
                metrics[stream["codec_type"]][data] = stream[data]

    json_metrics = json.dumps(metrics, indent=4)
    with open("videoMetrics.json", "w") as f:
        f.write(json_metrics)
        f.close()



mediaFolder = "media/"

files = os.listdir(mediaFolder)
for file in files:
    print(file)

videoPath = mediaFolder + files[1]
getProperties(videoPath)