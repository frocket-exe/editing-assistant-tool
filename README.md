# editing-assistant-tool

## The plan is simple...:
### High priority:
- Import a video/audio
- Display the properties of the video
- Detect silence and add to EDL
- Transcribe using whisperX
- Export subtitles as SRT
- Swear word detection (+ EDL)
- Key word detection (+ EDL)
- Export media with choice of output quality

---

### Medium priority:
- Mute swear words
- Beep swear words
- Burn subtitles into video
- Normalise audio
- Estimate file output size
- Detect black frames

---

### Low priority:
- Compress audio
- Detect low-motion/static scenes
- Auto cut silences
- Subtitle translation
- Plot graphs about video properties
- Compare score for video before/after processing

# Dependencies
- requirements.txt
- ffmpeg
- python 3.12

# Dummy don't forget these commands
.venv/Script/activate
pip freeze > requirements.txt
pip install -r requirements.txt