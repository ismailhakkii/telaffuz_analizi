# main.py
"""
Uygulamanın ana giriş noktası.
Tüm bileşenleri başlatır ve kullanıcı arayüzünü gösterir.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from src.audio.audio_recorder import AudioRecorder
from src.audio.speech_recognizer import SpeechRecognizer
from src.analysis.pronunciation_analyzer import PronunciationAnalyzer
from src.gui.main_window import MainWindow


def check_requirements():
    """Gerekli klasör ve dosyaların varlığını kontrol eder"""
    required_folders = ['models', 'data/recordings']

    for folder in required_folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"'{folder}' klasörü oluşturuldu.")

    model_path = "models/vosk-model-small-tr-0.3"
    if not os.path.exists(model_path):
        print(f"UYARI: '{model_path}' bulunamadı!")
        print("Lütfen Vosk Türkçe modelini indirip models klasörüne çıkartın.")
        print("İndirme linki: https://alphacephei.com/vosk/models")
        sys.exit(1)


def main():
    """Uygulamayı başlatır"""
    try:
        # Gereksinimleri kontrol et
        check_requirements()

        # Uygulama örneği oluştur
        app = QApplication(sys.argv)

        # Temel bileşenleri oluştur
        audio_recorder = AudioRecorder()
        speech_recognizer = SpeechRecognizer()
        pronunciation_analyzer = PronunciationAnalyzer()

        # Ana pencereyi oluştur ve göster
        window = MainWindow(audio_recorder, speech_recognizer, pronunciation_analyzer)
        window.show()

        # Uygulamayı çalıştır
        sys.exit(app.exec_())

    except Exception as e:
        print(f"Uygulama başlatma hatası: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()