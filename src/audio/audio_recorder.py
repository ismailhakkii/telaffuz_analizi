# src/audio/audio_recorder.py

import sounddevice as sd
import numpy as np
import wave
import threading
from datetime import datetime


class AudioRecorder:
    def __init__(self):
        self.sample_rate = 44100  # Örnekleme hızı
        self.channels = 1  # Mono ses kaydı
        self.recording = False  # Kayıt durumu
        self.frames = []  # Ses verilerini tutacak liste

    def start_recording(self):
        """Ses kaydını başlatır"""
        if not self.recording:
            self.recording = True
            self.frames = []
            self.audio_thread = threading.Thread(target=self._record)
            self.audio_thread.start()

    def stop_recording(self):
        """Ses kaydını durdurur"""
        self.recording = False
        if hasattr(self, 'audio_thread'):
            self.audio_thread.join()

    def _record(self):
        """Ses kaydı yapan iç fonksiyon"""

        def callback(indata, frames, time, status):
            if self.recording:
                self.frames.append(indata.copy())

        with sd.InputStream(samplerate=self.sample_rate,
                            channels=self.channels,
                            callback=callback):
            while self.recording:
                sd.sleep(100)

    def save_recording(self, filename=None):
        """Kaydedilen sesi WAV dosyası olarak kaydeder"""
        if not self.frames:
            return None

        if filename is None:
            filename = f"kayit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"

        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(np.concatenate(self.frames))

        return filename