# src/audio/speech_recognizer.py
"""
Bu modül ses tanıma işlemlerini gerçekleştirir. Temel görevi ses dosyasını metne çevirmektir.
Ses kalitesini artırmak için ön işleme adımları da içerir.
"""

from vosk import Model, KaldiRecognizer
import wave
import json
import os
import logging
import soundfile as sf
import librosa
import numpy as np

logging.getLogger('vosk').setLevel(logging.ERROR)


class SpeechRecognizer:
    def __init__(self, model_path="models/vosk-model-small-tr-0.3"):
        # Model yolunun geçerliliğini kontrol et
        if not os.path.exists(model_path):
            raise Exception(f"Model klasörü '{model_path}' bulunamadı.")

        self.model = Model(model_path)
        self.target_sr = 16000  # Ses tanıma için ideal örnekleme hızı

    def preprocess_audio(self, audio_file_path):
        """
        Ses dosyasını tanıma için optimize eder.
        - Örnekleme hızını ayarlar
        - Ses seviyesini normalleştirir
        - Basit gürültü azaltma uygular
        """
        try:
            # Ses dosyasını oku
            y, sr = librosa.load(audio_file_path, sr=None)

            # Örnekleme hızını dönüştür
            if sr != self.target_sr:
                y = librosa.resample(y, orig_sr=sr, target_sr=self.target_sr)

            # Ses seviyesini normalize et
            y = librosa.util.normalize(y)

            # Gürültü azaltma
            y = self._reduce_noise(y)

            # İşlenmiş sesi geçici dosyaya kaydet
            temp_path = "temp_processed.wav"
            sf.write(temp_path, y, self.target_sr)

            return temp_path

        except Exception as e:
            print(f"Ses işleme hatası: {str(e)}")
            return audio_file_path

    def _reduce_noise(self, audio_data):
        """
        Basit gürültü azaltma işlemi uygular.
        Sessiz bölgelerdeki gürültü profilini kullanarak sesi temizler.
        """
        non_silent = librosa.effects.split(audio_data,
                                           top_db=20,
                                           frame_length=2048,
                                           hop_length=512)

        noise_sample = []
        for interval in non_silent:
            if interval[1] - interval[0] > 2048:
                noise_sample.extend(audio_data[interval[0]:interval[1]])

        if noise_sample:
            noise_profile = np.mean(noise_sample)
            audio_data = np.where(np.abs(audio_data) > noise_profile * 1.2,
                                  audio_data,
                                  audio_data * 0.1)

        return audio_data

    def transcribe_audio(self, audio_file_path):
        """
        Ses dosyasını metne çevirir.
        Önce sesi ön işlemeden geçirir, sonra Vosk ile metne çevirir.
        """
        try:
            processed_file = self.preprocess_audio(audio_file_path)

            with wave.open(processed_file, "rb") as wf:
                recognizer = KaldiRecognizer(self.model, wf.getframerate())

                text = ""
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if recognizer.AcceptWaveform(data):
                        result = json.loads(recognizer.Result())
                        text += result.get("text", "") + " "

                result = json.loads(recognizer.FinalResult())
                text += result.get("text", "")

            # Geçici dosyayı temizle
            if processed_file != audio_file_path:
                try:
                    os.remove(processed_file)
                except:
                    pass

            return text.strip()

        except Exception as e:
            print(f"Ses tanıma hatası: {str(e)}")
            return None