import whisperx
import re

# Transcribes a given video/audio file based on it's path
# using WhisperX, an open source local AI transcription model
def transcribe(filePath):
    print("Transcribing....")
    modelSize = "large-v2"
    device = "cpu"
    compute_type = "int8"
    model = whisperx.load_model(modelSize, device, compute_type=compute_type, vad_method="silero")
    audio = whisperx.load_audio(filePath)
    transcription = model.transcribe(audio, language="en")

    # Align transcripted words
    print("Aligning....")
    align_model, metadata = whisperx.load_align_model(language_code = transcription["language"], device=device)
    result = whisperx.align(transcription["segments"], align_model, metadata, audio, device, return_char_alignments=False)
    print("Finished alignment")
    return result["segments"]

def splitSegment(words):
    biggestGap = {}
    for i in range(len(words)-1):
        gap = words[i+1]['start'] - words[i]['end']
        if biggestGap == {} or gap > biggestGap['gap']:
            biggestGap = {"index": i, "gap": gap}
    splitSegments = [words[0:biggestGap["index"]+1], words[biggestGap["index"]+1:]]
    return splitSegments

def transcriptToCaptions(segments, characterLimit=30, wordLimit=1, maxTime=2, fillGaps=True):
    captions = []
    for segment in segments:
        words = segment["words"]
        wordCount = len(words)
        characterCount = len(" ".join(w["word"] for w in words))
        timeCount = words[-1]["end"]-words[0]["start"]
        processedWords = []
        if (wordCount <= wordLimit and characterCount <= characterLimit and timeCount <= maxTime) or wordCount == 1:
            captions.append(segment["words"])
        else:
            subsegments = [words]
            while subsegments != []:
                splitSegments = splitSegment(subsegments.pop(0))
                for segment in splitSegments:
                    wordCount = len(segment)
                    characterCount = len(" ".join(w["word"] for w in segment))
                    timeCount = segment[-1]["end"]-segment[0]["start"]
                    if (wordCount <= wordLimit and characterCount <= characterLimit and timeCount <= maxTime) or wordCount == 1:
                        processedWords.append(segment)
                    else:
                        subsegments.insert(0, segment)
            captions += processedWords
            if fillGaps:
                for phrase in processedWords:
                    for i in range(len(phrase)-1):
                        gap = phrase[i+1]['start'] - phrase[i]['end'] 
    segmentedCaptions = []
    for caption in captions:
        seg = {'start': float(caption[0]['start']), 'end': float(caption[-1]['end']), 'text': " ".join([cap["word"] for cap in caption])}
        segmentedCaptions.append(seg)
    sortedSegmentedCaptions = sorted(segmentedCaptions, key=lambda d: d['start'])
    return(sortedSegmentedCaptions)


# Converts seconds to the timecode format used in the srt standard
def secondsToTimecode(seconds):
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds * 1000) % 1000)
    return(f"{hours:02}:{mins:02}:{secs:02},{milliseconds:03}")

# Converts a transcription from the model into an srt file to be used for subtitles
def transcriptionToSrt(transcription, savePath):
    srtText = ""
    for i, segment in enumerate(transcription):
        srtText += f"{i+1}\n"
        srtText += f"{secondsToTimecode(segment["start"])} --> {secondsToTimecode(segment["end"])}\n"
        srtText += f"{segment["text"]}\n\n"
    with open(savePath, "w") as f:
        f.write(srtText)
        f.close()

def sanitise(inputPath, outputPath, keepCap=["I", "I'm", "I've", "I'd", "I'll"], puncToRemove=r'[.!",;]', caseConvert="lower", censorWords=[]):
    keepCap = [i.capitalize() for i in keepCap]
    with open(inputPath, "r") as f:
        file = f.read()
        captions = (file.split("\n\n"))
        captions = [x for x in captions if x != '']
    sanitisedCaptions = ""
    for caption in captions:
        content = caption.split("\n")[2]
        content = re.sub(puncToRemove, '', content)
        for swear in censorWords:
            swear = swear.lower()
            if swear in content.lower():
                content = re.sub('(?i)' + re.escape(swear), swear[:1]+("*"*(len(swear)-2))+swear[-1:], content)
        if caseConvert == "upper":
            sanitisedCaption = f"{caption.split("\n")[0]}\n{caption.split("\n")[1]}\n{content.upper()}"
        elif caseConvert == "lower":
            words = []
            for word in content.split(" "):
                if word.capitalize() in keepCap:
                    words.append(word.capitalize())
                else:
                    words.append(word.lower())
            sanitisedCaption = f"{caption.split("\n")[0]}\n{caption.split("\n")[1]}\n{" ".join(words)}"
        else:
            sanitisedCaption = f"{caption.split("\n")[0]}\n{caption.split("\n")[1]}\n{content}"
        sanitisedCaptions += sanitisedCaption + "\n\n"
    with open(outputPath, "w") as f:
        f.write(sanitisedCaptions[:-2])
        f.close()
