"""
make_voice_pickell.py - voices Mr. John B. Pickell's dialogue lines with Piper TTS (offline).

Reads   data/dialogue/pickell.json   (only each node's "text" = Pickell's speech; the
                                       visitor's "replies" are not voiced)
Writes  assets/audio/voices/pickell/<node-id>.ogg   (mono Vorbis 64 kbps, 22.05 kHz, ~-18 LUFS)
        assets/audio/voices/pickell/timings.json    (node id -> duration + per-word times)

Setup (once, in a throwaway virtual environment - not the system Python):
    python -m venv venv_piper
    venv_piper\\Scripts\\python -m pip install "piper-tts[alignment]==1.8.0" numpy imageio-ffmpeg
    Download the voice from https://huggingface.co/rhasspy/piper-voices (en/en_US/libritts/high):
        en_US-libritts-high.onnx  and  en_US-libritts-high.onnx.json   (same folder)

Usage:
    venv_piper\\Scripts\\python tools/make_voice_pickell.py --model path\\to\\en_US-libritts-high.onnx
        [--ffmpeg path\\to\\ffmpeg.exe]  [--only start,goods]

Each run gives a slightly different take (Piper adds random variation), so re-run with
--only <node> to re-voice one line; a take that pauses > 0.25 s inside a word is redone.

Word timings come from Piper's own phoneme alignments (real durations, not guesses).
In timings.json every whitespace-separated token of the on-screen text appears once,
in order, exactly as displayed (so joining the "w" values with spaces gives the text back).
Tokens that are not spoken (a lone dash) get start = end = the previous word's end.

To fix a mispronunciation: add the word to PRON below (respelling or [[ IPA ]] phonemes in
espeak en-us notation) and re-run. The on-screen text is never changed.
"""
import argparse
import difflib
import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DIALOGUE = ROOT / "data" / "dialogue" / "pickell.json"
OUT = ROOT / "assets" / "audio" / "voices" / "pickell"

# ---- voice settings ---------------------------------------------------------------------
SPEAKER_ID = 595          # = LibriTTS reader 7241: calm, low (~90 Hz), clean pauses
LENGTH_SCALE = 1.15       # >1 = slower; Pickell is a calm, unhurried clerk
NOISE_SCALE = 0.667       # Piper defaults (natural variation)
NOISE_W_SCALE = 0.8
SENTENCE_PAUSE = 0.38     # seconds of silence between sentences
EDGE_PAD = 0.10           # silence kept at the start and end of each clip
TARGET_LUFS = -18.0
PEAK_DBFS = -1.0
BITRATE = "64k"
MAX_GAP_IN_WORD = 0.25    # a longer silence inside one word = a stumble -> retake the line
MAX_TAKES = 6

# ---- pronunciation fixes (TTS input only) -------------------------------------------------
# key = word as written (without surrounding punctuation), value = what Piper is given.
PRON = {
    "Mr.": "Mister",
    "Pickell": "Pickle",                    # PICK-ul
    "gingham": "[[ ɡˈɪŋəm ]]",              # GING-um (espeak says "jing-am")
    "percale": "[[ pɚkˈeɪl ]]",             # per-KALE
    "hosiery": "[[ hˈoʊʒɚɹi ]]",            # HOE-zhuh-ree
    "jurymen": "[[ dʒˈʊɹimən ]]",           # JOOR-ee-mun
    "automobile": "[[ ˈɔːɾəmoʊbˌiːl ]]",   # AW-tuh-moh-beel (espeak says "-bee-ul")
    "1828": "eighteen twenty-eight",
    "1856": "eighteen fifty-six",
    "1878": "eighteen seventy-eight",
    "1880": "eighteen eighty",
    "1895": "eighteen ninety-five",
    "1896": "eighteen ninety-six",
}
DASHES = {"—", "–", "-", "--"}


def tts_token(tok):
    """On-screen token -> TTS text (respelled), keeping its punctuation."""
    if tok in DASHES:
        return ","
    if tok in PRON:
        return PRON[tok]
    m = re.match(r"^([\"“‘(]*)(.*?)([\"”’)\.,;:!?]*)$", tok)
    lead, core, trail = m.groups()
    if core in PRON:
        rep = PRON[core]
        if rep.startswith("[["):
            # punctuation after a raw block is dropped by Piper: put it inside the block
            inner = rep[2:-2].strip()
            return lead + "[[ " + inner + "".join(c for c in trail if c in ".,;:!?") + " ]]"
        return lead + rep + trail
    if re.fullmatch(r"1[89]\d\d", core):
        raise SystemExit(f"Year {core} has no spoken form in PRON; add it.")
    return tok


def is_spoken(tok):
    return tok not in DASHES and any(c.isalnum() for c in tok)


SKIP = set(" ^$_" + ",.;:!?—…\"'()-")


def phone_times(chunk, sr):
    """Piper's alignments -> [(phoneme, start_s, end_s)] for the sounding phonemes of a sentence."""
    out, t = [], 0.0
    for a in chunk.phoneme_alignments:
        d = int(a.num_samples) / sr
        if a.phoneme not in SKIP:
            out.append((a.phoneme, t, t + d))
        t += d
    return out


def align_words(token_phones, phones):
    """Match each on-screen token's own phonemes to the timed phonemes of the whole line.

    espeak merges small words in context ("of the" -> one word) and reduces vowels, so the
    words are found by a sequence alignment (difflib) rather than by counting word breaks.
    Returns [(start, end) or None] per token, plus the share of phonemes matched."""
    flat, owner = [], []
    for k, ph in enumerate(token_phones):
        flat += ph; owner += [k] * len(ph)
    sm = difflib.SequenceMatcher(None, flat, [p for p, _, _ in phones], autojunk=False)
    hit = {}
    for blk in sm.get_matching_blocks():
        for j in range(blk.size):
            hit[blk.a + j] = blk.b + j
    spans = [None] * len(token_phones)
    for i, j in hit.items():
        k = owner[i]; s, e = phones[j][1], phones[j][2]
        spans[k] = (s, e) if spans[k] is None else (min(spans[k][0], s), max(spans[k][1], e))
    return spans, len(hit) / max(1, len(flat))


def word_gap(x, sr, words):
    """Longest silent stretch (s) inside any single spoken word: a sign of a stumble."""
    hop = int(0.01 * sr)
    fr = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    quiet = db < np.percentile(db, 95) - 40
    worst = 0.0
    for w in words:
        if not is_spoken(w["w"]):
            continue
        run = 0
        for q in quiet[int(w["start"] * 100) + 3: int(w["end"] * 100) - 3]:
            run = run + 1 if q else 0
            worst = max(worst, run / 100)
    return worst


def lufs(ff, path):
    r = subprocess.run([ff, "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    i = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    tp = float(re.findall(r"Peak:\s+(-?[\d.inf]+) dBFS", r)[-1])
    return i, tp


def save_wav(path, x, sr):
    y = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(y.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--ffmpeg", default=None)
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    ff = args.ffmpeg
    if not ff:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()

    from piper import PiperVoice, SynthesisConfig
    voice = PiperVoice.load(args.model, include_alignments=True)
    sr = voice.config.sample_rate
    # espeak sometimes emits marks the model has no id for (e.g. the syllabic mark in
    # "buttons"); Piper skips them but then cannot align the sentence, so drop them first.
    known = voice.config.phoneme_id_map
    _phonemize = voice.phonemize
    voice.phonemize = lambda t: [[p for p in sent if p in known] for sent in _phonemize(t)]
    # normalize_audio off: Piper would scale every sentence to full peak separately
    cfg = SynthesisConfig(speaker_id=SPEAKER_ID, length_scale=LENGTH_SCALE,
                          noise_scale=NOISE_SCALE, noise_w_scale=NOISE_W_SCALE,
                          normalize_audio=False)

    nodes = json.loads(DIALOGUE.read_text(encoding="utf-8"))["nodes"]
    only = [s for s in args.only.split(",") if s]
    OUT.mkdir(parents=True, exist_ok=True)
    tpath = OUT / "timings.json"
    timings = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() and only else {}
    tmp = OUT / "_tmp"
    tmp.mkdir(exist_ok=True)

    for nid, node in nodes.items():
        if only and nid not in only:
            continue
        text = node["text"]
        tokens = text.split()
        tts = " ".join(tts_token(t) for t in tokens)
        # each spoken token's own phonemes, for the word-timing alignment
        token_phones = [[p for sent in voice.phonemize(tts_token(t)) for p in sent if p not in SKIP]
                        if is_spoken(t) else [] for t in tokens]
        def take():
            chunks = list(voice.synthesize(tts, cfg, include_alignments=True))
            audio, phones, off = [], [], 0.0
            pause = np.zeros(int(SENTENCE_PAUSE * sr))
            for k, ch in enumerate(chunks):
                a = ch.audio_float_array.astype(np.float64)
                phones += [(p, s + off, e + off) for p, s, e in phone_times(ch, sr)]
                audio.append(a); off += len(a) / sr
                if k < len(chunks) - 1:
                    audio.append(pause); off += SENTENCE_PAUSE
            x = np.concatenate(audio)
            x = x / (np.max(np.abs(x)) + 1e-9) * 0.5   # headroom; loudness is set below

            # trim to EDGE_PAD of silence at each end
            env = np.convolve(np.abs(x), np.ones(220) / 220, "same")
            loud = np.where(env > 10 ** (-45 / 20))[0]
            a0 = max(0, loud[0] - int(EDGE_PAD * sr)); a1 = min(len(x), loud[-1] + int(EDGE_PAD * sr))
            x = x[a0:a1]; shift = a0 / sr
            n = len(x)
            x[: int(0.01 * sr)] *= np.linspace(0, 1, int(0.01 * sr))
            x[-int(0.02 * sr):] *= np.linspace(1, 0, int(0.02 * sr))
            dur = n / sr

            # word timings (times relative to the trimmed clip)
            spans, matched = align_words(token_phones, phones)
            spans = [None if sp is None else (max(0.0, sp[0] - shift), min(dur, sp[1] - shift))
                     for sp in spans]
            # tokens with no matched phoneme (or silent ones like a dash) sit between their neighbours
            words, last = [], 0.0
            for k, t in enumerate(tokens):
                sp = spans[k]
                if sp is None:
                    nxt = next((q[0] for q in spans[k + 1:] if q), dur)
                    sp = (last, last) if not is_spoken(t) else (max(last, nxt - 0.15), max(last, nxt))
                sp = (max(sp[0], last if not words else words[-1]["start"]), sp[1])
                words.append({"w": t, "start": round(sp[0], 3), "end": round(max(sp), 3)})
                last = max(last, sp[1])
            missing = [t for t, sp in zip(tokens, spans) if sp is None and is_spoken(t)]
            how = f"aligned {matched:.0%} of phonemes" + (f"; interpolated: {missing}" if missing else "")
            return x, dur, words, how, word_gap(x, sr, words)

        # Piper's output varies from run to run; retake a line if it hesitates inside a word
        best = None
        for attempt in range(MAX_TAKES):
            t_ = take()
            if best is None or t_[4] < best[4]:
                best = t_
            if best[4] <= MAX_GAP_IN_WORD:
                break
        x, dur, words, how, gap = best
        how += f"; takes {attempt + 1}, longest pause inside a word {gap:.2f} s"

        # loudness: measure, gain, limit only if the peak would pass -1 dBFS
        raw = tmp / f"{nid}_raw.wav"; save_wav(raw, x, sr)
        i, tp = lufs(ff, raw)
        g = TARGET_LUFS - i
        af = f"volume={g:.2f}dB"
        if tp + g > PEAK_DBFS:
            af += ",alimiter=limit=0.84:attack=2:release=50:level=disabled"
        ogg = OUT / f"{nid}.ogg"
        subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), "-af", af,
                        "-c:a", "libvorbis", "-b:a", BITRATE, "-ac", "1", "-ar", str(sr),
                        "-map_metadata", "-1", str(ogg)], check=True)
        i2, tp2 = lufs(ff, ogg)

        timings[nid] = {"duration_s": round(dur, 3), "words": words}
        print(f"{nid:9s} {dur:5.2f}s  {ogg.stat().st_size/1024:5.1f} KB  {i2:6.1f} LUFS  peak {tp2:5.1f}  {how}")
        raw.unlink()

    tmp.rmdir()
    timings["_meta"] = {"model": Path(args.model).name, "speaker_id": SPEAKER_ID,
                        "length_scale": LENGTH_SCALE, "noise_scale": NOISE_SCALE,
                        "noise_w_scale": NOISE_W_SCALE, "sample_rate": sr,
                        "note": "words = on-screen tokens in order; times in seconds from clip start"}
    ordered = {k: timings[k] for k in list(nodes) if k in timings}
    ordered["_meta"] = timings["_meta"]
    tpath.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
