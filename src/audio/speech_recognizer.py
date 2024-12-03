# src/audio/speech_recognizer.py

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
        if not os.path.exists(model_path):
            raise Exception(f"Model klasörü '{model_path}' bulunamadı.")
        self.model = Model(model_path)
        self.target_sr = 16000  # Hedef örnekleme hızı

    def preprocess_audio(self, audio_file_path):
        """Ses dosyasını ön işleme ve format dönüşümü"""
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

            # Geçici WAV dosyası oluştur
            temp_path = "temp_processed.wav"
            sf.write(temp_path, y, self.target_sr)

            return temp_path

        except Exception as e:
            print(f"Ses işleme hatası: {str(e)}")
            return audio_file_path

    def _reduce_noise(self, audio_data):
        """Basit gürültü azaltma"""
        # Sessiz bölgeleri bul
        non_silent = librosa.effects.split(audio_data,
                                           top_db=20,
                                           frame_length=2048,
                                           hop_length=512)

        # Sessiz bölgelerin ortalamasını al
        noise_sample = []
        for interval in non_silent:
            if interval[1] - interval[0] > 2048:  # Minimum uzunluk kontrolü
                noise_sample.extend(audio_data[interval[0]:interval[1]])

        if noise_sample:
            noise_profile = np.mean(noise_sample)
            # Gürültü eşiği üzerindeki sesleri koru
            audio_data = np.where(np.abs(audio_data) > noise_profile * 1.2,
                                  audio_data,
                                  audio_data * 0.1)

        return audio_data

    def transcribe_audio(self, audio_file_path):
        """Ses dosyasını metne çevir"""
        try:
            # Ses dosyasını ön işle
            processed_file = self.preprocess_audio(audio_file_path)

            wf = wave.open(processed_file, "rb")
            recognizer = KaldiRecognizer(self.model, wf.getframerate())

            text = ""
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text += result.get("text", "") + " "

            # Son kısmı da işle
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