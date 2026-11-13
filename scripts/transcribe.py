import whisperx

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
    return result["segments"]

def splitSegment(words):
    biggestGap = {}
    for i in range(len(words)-1):
        gap = words[i+1]['start'] - words[i]['end']
        if biggestGap == {} or gap > biggestGap['gap']:
            biggestGap = {"index": i, "gap": gap}
    splitSegments = [words[0:biggestGap["index"]+1], words[biggestGap["index"]+1:]]
    return splitSegments

def transcriptToCaptions(segments, characterLimit=30, wordLimit=4, maxTime=2):
    captions = []
    for segment in segments:
        words = segment["words"]
        wordCount = len(words)
        characterCount = len(" ".join(w["word"] for w in words))
        timeCount = words[-1]["end"]-words[0]["start"]
        processedWords = []
        processedWordCount = 0
        if (wordCount <= wordLimit and characterCount <= characterLimit and timeCount <= maxTime) or wordCount == 1:
            captions.append(segment)
        else:
            subsegments = [words]
            while processedWordCount != wordCount:
                splitSegments = splitSegment(subsegments.pop(0))
                for segment in splitSegments:
                    wordCount = len(segment)
                    characterCount = len(" ".join(w["word"] for w in segment))
                    timeCount = segment[-1]["end"]-segment[0]["start"]
                    if (wordCount <= wordLimit and characterCount <= characterLimit and timeCount <= maxTime) or wordCount == 1:
                        processedWords.append(segment)
                        processedWordCount += len(segment)
                    else:
                        subsegments.insert(0, segment)
            captions += processedWords
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
def transcriptionToSrt(transcription):
    srtText = ""
    for i, segment in enumerate(transcription):
        srtText += f"{i+1}\n"
        srtText += f"{secondsToTimecode(segment["start"])} --> {secondsToTimecode(segment["end"])}\n"
        srtText += f"{segment["text"]}\n\n"
    with open("srt/transcription.srt", "w") as f:
        f.write(srtText)
        f.close()

t = transcribe("media/testVideo.mp4")
t2 = transcriptToCaptions(t)
transcriptionToSrt(t2)