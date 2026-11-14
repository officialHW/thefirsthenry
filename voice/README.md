# Your buddy in your own voice (optional, free)

Out of the box your buddy uses the computer's built-in voice. To make him speak in **your**
voice, use Pocket TTS (free, by Kyutai). It runs on your own computer, so your voice never
leaves it. Skip any of this and he simply keeps the computer voice.

## What you need

- A free Hugging Face account, and on https://huggingface.co/kyutai/pocket-tts click
  **Agree and access** (the voice-copying model asks you to accept its terms).
- A Hugging Face access key: https://huggingface.co/settings/tokens, **Create new token**,
  type **Read**. It starts with `hf_`.
- A clear recording of your voice, 6 to 15 seconds, one person, no music. Phone voice memos
  are fine.

## Steps

1. Download Pocket TTS for your computer from https://github.com/kyutai-labs/pocket-tts/releases
   (Mac Intel: `x86_64-apple-darwin`, Mac M-chip: `aarch64-apple-darwin`,
   Windows: `x86_64-pc-windows-msvc`). Unzip it and put the `pocket-tts` program
   (`pocket-tts.exe` on Windows) in this folder's `bin/` folder.
   Mac: if it won't open, run `xattr -d com.apple.quarantine voice/bin/pocket-tts` once.
2. Save your Hugging Face key (typing stays hidden, it is never printed):

       hermes/tools/python-*/bin/python3 -I tools/set_hf_token.py

3. Turn your recording into a 24 kHz WAV file. On a Mac:

       afconvert -f WAVE -d LEI16@24000 -c 1 my-recording.m4a voice/my-voice.wav

   (Any audio editor can do the same: export as WAV, mono, 24000 Hz.)
4. Make your voice file (the first run downloads the model, a few hundred MB):

       HF_HOME=voice/hf-cache voice/bin/pocket-tts export-voice --language english_2m_2026-10 voice/my-voice.wav voice/my-voice.safetensors

5. Start your buddy. You should see "Henry is speaking in your voice." in the terminal.

## Faster or better

In `app/settings.json`, `"voice_model"` picks the size. Make a voice file for each one you try,
with the same `--language` as in step 4.

| `voice_model` | Speed | Sound |
| --- | --- | --- |
| `english_2m_2026-10` | fastest (good for older computers) | good |
| `english_7m_2026-10` | medium | better |
| `english_18m_2026-10` | slow | best |

`"my_voice": false` switches back to the computer voice.

## Please be fair

Only copy **your own** voice, or a voice whose owner has said yes in writing. The voice model
is licensed CC-BY-4.0 (credit Kyutai, see NOTICE.md).
