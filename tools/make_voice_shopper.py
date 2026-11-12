r"""
make_voice_shopper.py - voices the anonymous woman shopping (A2) with Kokoro-82M (offline).

Same method, file format and loudness as Mr. Pickell's and Mr. Rittenhouse's voices
(make_voice_pickell_kokoro.py, make_voice_rittenhouse.py); only the voice, the speed and
the files differ.
Voice: an American female Kokoro voice (af_*) that sounds like a calm woman of about 35,
chosen by measurement (median pitch, 10-90% pitch range in semitones, syllable tempo):
run with --audition to render line 1 in every candidate voice and print the stats, then set
VOICE below. See PLAN.md (People, A2) for the choice made.

Reads   data/dialogue/shopper.json   (only each node's "text"; replies are not voiced)
Writes  assets/audio/voices/shopper/<node-id>.ogg   (mono Vorbis 64 kbps, 22.05 kHz, ~-18 LUFS)
        assets/audio/voices/shopper/timings.json    (node id -> duration + per-word times)

Setup (once, in a throwaway virtual environment - not the system Python):
    python -m venv kv
    kv\Scripts\python -m pip install kokoro==0.9.4 soundfile numpy imageio-ffmpeg
    kv\Scripts\python -m spacy download en_core_web_sm
    The model weights and the voice files (hexgrad/Kokoro-82M, Apache-2.0) download from
    Hugging Face on the first run and are cached in the user's Hugging Face folder.

Usage:
    kv\Scripts\python tools/make_voice_shopper.py  [--ffmpeg path\to\ffmpeg.exe]  [--only start,vote]
    kv\Scripts\python tools/make_voice_shopper.py  --audition   (compare candidate voices; writes nothing)

Kokoro gives the same take every run, so re-running only matters after a text or PRON change.
Word timings: Kokoro's own per-word timestamps, each word's end pulled back to where the
sound goes quiet (see make_voice_pickell_kokoro.py for the details).
To fix a mispronunciation: add the word to PRON below as IPA in misaki notation and re-run.
The on-screen text is never changed.
"""
import argparse
import json
import re
import subprocess
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DIALOGUE = ROOT / "data" / "dialogue" / "shopper.json"
OUT = ROOT / "assets" / "audio" / "voices" / "shopper"

# ---- voice settings ---------------------------------------------------------------------
REPO = "hexgrad/Kokoro-82M"
VOICE = "af_heart"        # calm, clear woman: mid pitch ~203 Hz, 7.7 st range, unhurried (see PLAN.md A2)
SPEED = 0.92              # <1 = slower; calm, unhurried small talk
KOKORO_SR = 24000         # Kokoro's own output rate
OUT_SR = 22050            # clips are stored at the same rate as before
SENTENCE_PAUSE = 0.38     # silence between chunks, if Kokoro has to split a long line
EDGE_PAD = 0.10           # silence kept at the start and end of each clip
TARGET_LUFS = -18.0
PEAK_DBFS = -1.0
BITRATE = "64k"

# ---- pronunciation fixes (TTS input only) -------------------------------------------------
# key = word as written (without surrounding punctuation), value = IPA in misaki notation.
# Kokoro already says Mr., the years and most words right; these are the ones to pin down.
PRON = {
    "Nevius's": "nˈiviəsɪz",       # NEE-vee-us-iz (the store's name, possessive)
}
DASHES = {"—", "–", "-", "--"}


def tts_token(tok):
    """On-screen token -> TTS text (PRON words as [word](/IPA/)), keeping its punctuation."""
    m = re.match(r"^([\"“‘(]*)(.*?)([\"”’)\.,;:!?]*)$", tok)
    lead, core, trail = m.groups()
    if core in PRON:
        return lead + f"[{core}](/{PRON[core]}/)" + trail
    return tok


def is_spoken(tok):
    return tok not in DASHES and any(c.isalnum() for c in tok)


def quiet_frames(x, sr):
    """10 ms frames that are 40 dB below the loud parts of the clip."""
    hop = int(0.01 * sr)
    fr = x[: len(x) // hop * hop].reshape(-1, hop)
    db = 20 * np.log10(np.sqrt((fr ** 2).mean(1)) + 1e-9)
    return db < np.percentile(db, 95) - 40


def tighten_ends(words, quiet):
    """Pull a word's end back to the start of a pause (>= 80 ms) that begins inside it."""
    for w in words:
        if not is_spoken(w["w"]):
            continue
        a, b = int(w["start"] * 100) + 5, int(w["end"] * 100)
        for i in range(a, b):
            if quiet[i: i + 8].all() and len(quiet[i: i + 8]) == 8:
                w["end"] = round(max(w["start"] + 0.05, i / 100 + 0.03), 3)
                break


def word_gap(quiet, words):
    """Longest silent stretch (s) inside any single spoken word: a sign of a stumble."""
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


CANDIDATES = ["af_heart", "af_bella", "af_sarah", "af_nicole", "af_jessica", "af_river",
              "af_kore", "af_aoede", "af_alloy", "af_nova", "af_sky"]


def pitch_track(x, sr, fmin=110.0, fmax=420.0):
    """Rough f0 (Hz) of the voiced 40 ms frames, by normalised autocorrelation."""
    n, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / fmax), int(sr / fmin)
    rms_all = np.sqrt((x ** 2).mean())
    f0 = []
    for i in range(0, len(x) - n, hop):
        f = x[i:i + n] - x[i:i + n].mean()
        if np.sqrt((f ** 2).mean()) < 0.3 * rms_all:
            continue
        ac = np.correlate(f, f, "full")[n - 1:]
        ac = ac / (ac[0] + 1e-9)
        k = lo + int(np.argmax(ac[lo:hi]))
        if ac[k] > 0.5:
            f0.append(sr / k)
    return np.array(f0)


def audition(pipe, nodes):
    """Render every line in each candidate voice; print pitch and tempo stats (writes nothing)."""
    text = " ".join(n["text"] for n in nodes.values())
    nwords = len(text.split())
    print(f"{'voice':11s} {'median Hz':>9s} {'10-90% Hz':>11s} {'range st':>8s} {'words/s':>7s}")
    for v in CANDIDATES:
        try:
            chunks = [r.audio.numpy().astype(np.float64)
                      for r in pipe(text, voice=v, speed=SPEED, split_pattern=None)]
        except Exception as e:  # voice not available
            print(f"{v:11s} failed: {e}")
            continue
        x = np.concatenate(chunks)
        f0 = pitch_track(x, KOKORO_SR)
        p10, p50, p90 = np.percentile(f0, [10, 50, 90])
        print(f"{v:11s} {p50:9.0f} {p10:5.0f}-{p90:<5.0f} {12 * np.log2(p90 / p10):8.1f} "
              f"{nwords / (len(x) / KOKORO_SR):7.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ffmpeg", default=None)
    ap.add_argument("--only", default="")
    ap.add_argument("--audition", action="store_true")
    args = ap.parse_args()
    ff = args.ffmpeg
    if not ff:
        import imageio_ffmpeg
        ff = imageio_ffmpeg.get_ffmpeg_exe()

    from kokoro import KPipeline
    pipe = KPipeline(lang_code="a", repo_id=REPO)
    sr = KOKORO_SR

    nodes = json.loads(DIALOGUE.read_text(encoding="utf-8"))["nodes"]
    if args.audition:
        audition(pipe, nodes)
        return
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
        # TTS string, plus where each on-screen token sits in it (to map Kokoro's tokens back)
        tts_parts = [tts_token(t) for t in tokens]
        tts, spans_c = "", []
        for p in tts_parts:
            if tts:
                tts += " "
            spans_c.append((len(tts), len(tts) + len(p)))
            tts += p

        # synthesize; Kokoro splits very long lines into chunks: trim each, join with a pause
        audio, ktoks, off = [], [], 0.0
        pause = np.zeros(int(SENTENCE_PAUSE * sr))
        for r in pipe(tts, voice=VOICE, speed=SPEED, split_pattern=None):
            a = r.audio.numpy().astype(np.float64)
            env = np.convolve(np.abs(a), np.ones(220) / 220, "same")
            loud = np.where(env > np.max(env) * 10 ** (-45 / 20))[0]
            a0, a1 = (loud[0], loud[-1]) if len(loud) else (0, len(a))
            a = a[a0:a1]
            if audio:
                audio.append(pause); off += SENTENCE_PAUSE
            for tk in r.tokens or []:
                if tk.start_ts is None or not any(c.isalnum() for c in tk.text):
                    continue
                s = off + tk.start_ts - a0 / sr
                e = off + (tk.end_ts if tk.end_ts is not None else tk.start_ts) - a0 / sr
                ktoks.append((tk.text, s, e))
            audio.append(a); off += len(a) / sr
        x = np.concatenate(audio)
        lead = np.zeros(int(EDGE_PAD * sr))
        x = np.concatenate([lead, x, lead])
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.5   # headroom; loudness is set below
        x[: int(0.01 * sr)] *= np.linspace(0, 1, int(0.01 * sr))
        x[-int(0.02 * sr):] *= np.linspace(1, 0, int(0.02 * sr))
        dur = len(x) / sr

        # map Kokoro's word tokens onto the on-screen tokens (by position in the TTS string)
        spans = [None] * len(tokens)
        cursor = 0
        for ktext, s, e in ktoks:
            pos = tts.find(ktext, cursor)
            if pos < 0 or pos > cursor + 40:
                continue
            k = next(i for i, (c0, c1) in enumerate(spans_c) if c1 > pos)
            cursor = pos + len(ktext)
            if "](/" in tts_parts[k]:
                cursor = max(cursor, spans_c[k][1])   # skip past the IPA markup
            s = min(max(0.0, s + EDGE_PAD), dur); e = min(max(0.0, e + EDGE_PAD), dur)
            spans[k] = (s, e) if spans[k] is None else (min(spans[k][0], s), max(spans[k][1], e))

        # tokens with no Kokoro word (or silent ones like a dash) sit between their neighbours
        words, last = [], 0.0
        for k, t in enumerate(tokens):
            sp = spans[k]
            if sp is None:
                nxt = next((q[0] for q in spans[k + 1:] if q), dur)
                sp = (last, last) if not is_spoken(t) else (max(last, nxt - 0.15), max(last, nxt))
            sp = (max(sp[0], last if not words else words[-1]["start"]), sp[1])
            words.append({"w": t, "start": round(sp[0], 3), "end": round(max(sp), 3)})
            last = max(last, sp[1])
        quiet = quiet_frames(x, sr)
        tighten_ends(words, quiet)
        # keep the order rule: a silent token after a tightened word starts at that word's end
        prev_end = 0.0
        for w in words:
            if not is_spoken(w["w"]):
                w["start"] = w["end"] = round(prev_end, 3)
            prev_end = max(prev_end, w["end"]) if is_spoken(w["w"]) else prev_end
        missing = [t for t, sp in zip(tokens, spans) if sp is None and is_spoken(t)]
        how = f"{len(ktoks)} Kokoro words" + (f"; interpolated: {missing}" if missing else "")
        how += f"; longest pause inside a word {word_gap(quiet, words):.2f} s"

        # loudness: measure, gain, then limit peaks; Kokoro's consonants are peakier than
        # Piper's and Vorbis raises peaks a little, so check the finished file and, if its
        # true peak is still above -1 dBFS, limit harder and encode again
        raw = tmp / f"{nid}_raw.wav"; save_wav(raw, x, sr)
        i, tp = lufs(ff, raw)
        g = TARGET_LUFS - i
        ogg = OUT / f"{nid}.ogg"
        limit_db = PEAK_DBFS - 1.5
        for _ in range(6):
            af = f"aresample={OUT_SR},volume={g:.2f}dB"
            if tp + g > limit_db:
                af += f",alimiter=limit={10 ** (limit_db / 20):.3f}:attack=1:release=50:level=disabled"
            subprocess.run([ff, "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw), "-af", af,
                            "-c:a", "libvorbis", "-b:a", BITRATE, "-ac", "1", "-ar", str(OUT_SR),
                            "-map_metadata", "-1", str(ogg)], check=True)
            i2, tp2 = lufs(ff, ogg)
            if tp2 <= PEAK_DBFS:
                break
            limit_db -= (tp2 - PEAK_DBFS) + 0.5

        timings[nid] = {"duration_s": round(dur, 3), "words": words}
        print(f"{nid:9s} {dur:5.2f}s  {ogg.stat().st_size/1024:5.1f} KB  {i2:6.1f} LUFS  peak {tp2:5.1f}  {how}")
        raw.unlink()

    tmp.rmdir()
    timings["_meta"] = {"model": REPO, "voice": VOICE, "speed": SPEED, "sample_rate": OUT_SR,
                        "note": "words = on-screen tokens in order; times in seconds from clip start"}
    ordered = {k: timings[k] for k in list(nodes) if k in timings}
    ordered["_meta"] = timings["_meta"]
    tpath.write_text(json.dumps(ordered, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
