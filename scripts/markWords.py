import re
import json

# swears = ["fuck", "cunt", "shit"]
# keywords = ["video", "project"]
# inputFilePath = "srt/transcription.srt"
# outputFilePath = "edl/swearsAndKeywords.edl"
# fps = 60



def tcToTime(tc):
    hours = int(tc[0:2])
    mins = int(tc[3:5])
    secs = int(tc[6:8])
    millisecs = float(int(tc[9:12])/1000)
    time = hours*3600 + mins*60 + secs + millisecs
    return time

def getDuration(tIn, tOut, fps):
    tIn = tcToTime(tIn)
    tOut = tcToTime(tOut)
    frames = (tOut-tIn)*fps
    return round(frames)

def contains(list, content):
    for word in content.split(" "):
        for item in list:
            if item.lower() in word.lower():
                return True, re.sub(r"[.!?: ;,]", "", word.lower())
    return False, None

def tcToTs(timecode, fps):
    timestamp = timecode[:8]
    timestamp += f":{str(round(int(timecode[9:12])/1000*fps)).zfill(len(str(fps)))}"
    return timestamp

def MarkWords(inputFilePath, outputFilePath, swears, keywords, fps):
    markingColours = {"swear": "Red", "keyword": "Yellow"}
    markedSwears = []
    markers = []
    swearCount = 0
    keywordCount = 0
    with open(inputFilePath) as f:
        file = f.read()
        captions = (file.split("\n\n"))
        captions = [x for x in captions if x != '']

    for caption in captions:
        parts = caption.split("\n")
        content = parts[2]
        containsSwear, swearInfo = contains(swears, content)
        containsKeyword, keywordInfo = contains(keywords, content)
        marking = None
        if containsSwear:
            timecodes = (parts[1].split(" --> "))
            start = tcToTime(timecodes[0])
            end = tcToTime(timecodes[1])
            markedSwears.append({"start": start, "end": end})
            swearCount += 1
            marking = f"swear {swearCount} - {swearInfo}"
            colour = markingColours.get("swear")
        elif containsKeyword:
            keywordCount += 1
            marking = f"keyword {keywordCount} - {keywordInfo}"
            colour = markingColours.get("keyword")
        if marking != None:
            time = parts[1]
            timeParts = time.split(" ")
            timeIn = timeParts[0]
            timeOut = timeParts[2]
            marker = {"timeIn": timeIn, "timeOut": timeOut, "marking": marking, "content": content, "colour": colour}
            markers.append(marker)

    edlHeader = f"TITLE: Swears and keywords\nFCM: NON-DROP FRAME\n\n"
    edlTxt = edlHeader

    i = 0
    for m in markers:
        i += 1
        edlTxt += f"{str(i).zfill(3)}  001      V     C        {tcToTs(m["timeIn"], fps)} {tcToTs(m["timeOut"], fps)} {tcToTs(m["timeIn"], fps)} {tcToTs(m["timeOut"], fps)}\n"
        edlTxt += f" |C:ResolveColor{m["colour"]} |M:{m["marking"]} |D:{getDuration(m["timeIn"], m["timeOut"], fps)}\n\n"

    with open("json/swears.json", "w") as f:
        f.write(json.dumps(markedSwears, indent=4))
        f.close()

    with open(outputFilePath, "w") as f:
        f.write(edlTxt)
        f.close()