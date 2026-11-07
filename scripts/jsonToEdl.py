import json

def secsToTimestamp(secs, frameRate):
    hours = secs // 3600
    mins = (secs-(hours*60)) // 60
    secsRem = (secs - hours*3600 - mins*60) // 1
    frames = round((secs % 1)*frameRate)
    return(f"{str(int(hours)).zfill(2)}:{str(int(mins)).zfill(2)}:{str(int(secsRem)).zfill(2)}:{str(int(frames)).zfill(2)}")


path = "json/silencesToCut.json"
outputPath = "edl/silencesToCut.edl"

with open(path, "r") as f:
    data = json.load(f)

edlText = f"TITLE: {data["title"]}\nFCM: NON-DROP FRAME\n"
markers = data["timestamps"]

for i, marker in enumerate(markers):
    edlEntry = f"\n{str(i+1).zfill(3)}  001      V     C        {secsToTimestamp(marker["start"], data["frameRate"])} {secsToTimestamp(marker["end"], data["frameRate"])} {secsToTimestamp(marker["start"], data["frameRate"])} {secsToTimestamp(marker["end"], data["frameRate"])}\n |C:ResolveColor{data["colour"]} |M:{marker["note"]} |D:{round((marker["end"]-marker["start"])*data["frameRate"])}"
    edlText += edlEntry

with open(outputPath, "w") as f:
    f.write(edlText)
    f.close()