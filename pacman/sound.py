"""Synthesised recreations of the arcade sound effects and music.

No audio files are needed: every effect is generated at start-up from simple
waveforms, in the spirit of the arcade's wavetable sound chip.
"""

import array
import math

import pygame

RATE = 22050
_NOTE_INDEX = {"C": 0, "CS": 1, "D": 2, "DS": 3, "E": 4, "F": 5, "FS": 6,
               "G": 7, "GS": 8, "A": 9, "AS": 10, "B": 11}


def note(name):
    midi = 12 * (int(name[-1]) + 1) + _NOTE_INDEX[name[:-1]]
    return 440.0 * 2 ** ((midi - 69) / 12)


def tri(ph):
    return 4.0 * abs(ph - 0.5) - 1.0


def square(ph):
    return 0.6 if ph < 0.5 else -0.6


def sweep(dur, fn, wave=tri, vol=0.3, fade=True):
    """A tone whose frequency follows fn(u) for u in [0, 1)."""
    n = int(RATE * dur)
    out = [0.0] * n
    ph = 0.0
    for i in range(n):
        u = i / n
        ph = (ph + fn(u) / RATE) % 1.0
        env = (1.0 - u) / 0.15 if fade and u > 0.85 else 1.0
        out[i] = wave(ph) * vol * env
    return out


def loop(period, fn, wave=tri, vol=0.3):
    """A seamless loop: frequencies are nudged to fit whole wave cycles."""
    n = int(RATE * period)
    freqs = [fn(i / n) for i in range(n)]
    cycles = sum(freqs) / RATE
    k = max(1, round(cycles)) / cycles
    out = []
    ph = 0.0
    for f in freqs:
        ph = (ph + f * k / RATE) % 1.0
        out.append(wave(ph) * vol)
    return out


def silence(dur):
    return [0.0] * int(RATE * dur)


def melody(notes, whole, wave=tri, vol=0.3):
    out = []
    for name, d in notes:
        dur = whole / abs(d) * (1.5 if d < 0 else 1.0)
        n = int(RATE * dur)
        f = note(name) if name else 0.0
        ph = 0.0
        for i in range(n):
            u = i / n
            env = (1.0 if u < 0.75 else (1.0 - u) / 0.25) * (1.0 - 0.35 * u)
            if f:
                ph = (ph + f / RATE) % 1.0
                out.append(wave(ph) * vol * env)
            else:
                out.append(0.0)
    return out


def mix(*tracks):
    n = max(len(t) for t in tracks)
    out = [0.0] * n
    for t in tracks:
        for i, v in enumerate(t):
            out[i] += v
    return out


def _intro():
    whole = 2.18
    tune = [("B4", 16), ("B5", 16), ("FS5", 16), ("DS5", 16), ("B5", 32), ("FS5", -16), ("DS5", 8),
            ("C5", 16), ("C6", 16), ("G5", 16), ("E5", 16), ("C6", 32), ("G5", -16), ("E5", 8),
            ("B4", 16), ("B5", 16), ("FS5", 16), ("DS5", 16), ("B5", 32), ("FS5", -16), ("DS5", 8),
            ("DS5", 32), ("E5", 32), ("F5", 32), ("F5", 32), ("FS5", 32), ("G5", 32), ("G5", 32),
            ("GS5", 32), ("A5", 16), ("B5", 8)]
    bass = [("B2", 8), ("B3", 8), ("B2", 8), ("B3", 8),
            ("C3", 8), ("C4", 8), ("C3", 8), ("C4", 8),
            ("B2", 8), ("B3", 8), ("B2", 8), ("B3", 8),
            ("FS3", 8), ("GS3", 8), ("AS3", 8), ("B3", 8)]
    return mix(melody(tune, whole, square, 0.18), melody(bass, whole, tri, 0.35))


def _intermission():
    whole = 1.9
    tune = [("F5", 8), ("C5", 16), ("F5", 16), ("C5", 8), ("F5", 16), ("C5", 16),
            ("F5", 8), ("C5", 16), ("F5", 16), ("A5", 8), ("G5", 8),
            ("F5", 8), ("C5", 16), ("F5", 16), ("C5", 8), ("F5", 16), ("C5", 16),
            ("F5", 8), ("A5", 16), ("G5", 16), ("F5", 4),
            ("AS5", 8), ("F5", 16), ("AS5", 16), ("F5", 8), ("AS5", 16), ("F5", 16),
            ("A5", 8), ("F5", 16), ("A5", 16), ("C6", 8), ("A5", 8),
            ("G5", 8), ("E5", 16), ("G5", 16), ("C6", 8), ("AS5", 8),
            ("A5", 8), ("G5", 8), ("F5", 4)]
    bass = [("F2", 8), ("F3", 8)] * 8 + [("AS2", 8), ("AS3", 8)] * 2 + \
           [("F2", 8), ("F3", 8)] * 2 + [("C3", 8), ("C4", 8)] * 2 + [("F2", 8), ("F3", 8)] * 2
    return mix(melody(tune, whole, square, 0.18), melody(bass, whole, tri, 0.35))


def _death():
    out = silence(0.05)
    for i in range(11):
        top = 900 - i * 60
        out += sweep(0.1, lambda u, top=top: top * (1.0 - 0.45 * math.sin(math.pi * u)), tri, 0.3, False)
    out += silence(0.1)
    for _ in range(2):
        out += sweep(0.09, lambda u: 150 + 1400 * u, square, 0.25)
        out += silence(0.05)
    return out


def _extra_life():
    out = []
    for _ in range(8):
        out += sweep(0.07, lambda u: 1560, square, 0.2) + silence(0.06)
    return out


def build_sounds():
    s = {
        "start": _intro(),
        "intermission": _intermission(),
        "death": _death(),
        "extra_life": _extra_life(),
        "chomp_a": sweep(0.11, lambda u: 620 - 380 * u, tri, 0.35),
        "chomp_b": sweep(0.11, lambda u: 240 + 380 * u, tri, 0.35),
        "eat_ghost": sweep(0.55, lambda u: 110 * 13 ** u, tri, 0.3),
        "eat_fruit": sweep(0.18, lambda u: 1300 - 900 * u, tri, 0.3, False)
                     + sweep(0.18, lambda u: 400 + 900 * u, tri, 0.3),
        "credit": sweep(0.14, lambda u: 700 + 1200 * u, square, 0.25),
        "fright": loop(0.135, lambda u: 170 + 480 * u, tri, 0.28),
        "eyes": loop(0.095, lambda u: 1750 - 1050 * u, tri, 0.22),
    }
    for i in range(5):
        lo, hi = 340 + i * 45, 640 + i * 85
        s["siren%d" % i] = loop(0.40 - i * 0.03, lambda u, lo=lo, hi=hi: lo + (hi - lo) * (1 - abs(2 * u - 1)),
                                tri, 0.22)
    return s


class SoundManager:
    def __init__(self, muted=False):
        self.enabled = False
        self.muted = muted
        self.sounds = {}
        self.current_loop = None
        self._chomp_toggle = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(RATE, -16, 1, 512)
            info = pygame.mixer.get_init()
        except pygame.error:
            return
        if not info:
            return
        _, _, self.channels = info
        pygame.mixer.set_num_channels(8)
        pygame.mixer.set_reserved(2)
        self.loop_channel = pygame.mixer.Channel(0)
        self.chomp_channel = pygame.mixer.Channel(1)
        for name, samples in build_sounds().items():
            self.sounds[name] = self._make(samples)
        self.enabled = True

    def _make(self, samples):
        pcm = array.array("h", (int(max(-1.0, min(1.0, v)) * 32000) for v in samples))
        if self.channels == 2:
            stereo = array.array("h", bytes(len(pcm) * 4))
            stereo[0::2] = pcm
            stereo[1::2] = pcm
            pcm = stereo
        return pygame.mixer.Sound(buffer=pcm.tobytes())

    @property
    def active(self):
        return self.enabled and not self.muted

    def play(self, name):
        if self.active:
            self.sounds[name].play()

    def chomp(self):
        if self.active:
            self._chomp_toggle = not self._chomp_toggle
            self.chomp_channel.play(self.sounds["chomp_a" if self._chomp_toggle else "chomp_b"])

    def loop(self, name):
        if not self.active or self.current_loop == name:
            return
        self.current_loop = name
        self.loop_channel.play(self.sounds[name], loops=-1)

    def stop_loop(self):
        if self.enabled:
            self.loop_channel.stop()
        self.current_loop = None

    def stop_all(self):
        if self.enabled:
            pygame.mixer.stop()
        self.current_loop = None

    def toggle_mute(self):
        self.muted = not self.muted
        if self.muted:
            self.stop_all()


class SilentSound:
    """Drop-in replacement used by the attract-mode demo, which is silent."""

    active = False

    def play(self, name):
        pass

    def chomp(self):
        pass

    def loop(self, name):
        pass

    def stop_loop(self):
        pass

    def stop_all(self):
        pass
