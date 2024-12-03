# main.py

import sys
from PyQt5.QtWidgets import QApplication
from src.audio.audio_recorder import AudioRecorder
from src.audio.speech_recognizer import SpeechRecognizer
from src.gui.main_window import MainWindow


def main():
    # Uygulama oluştur
    app = QApplication(sys.argv)

    # Ses kaydedici ve tanıyıcı oluştur
    audio_recorder = AudioRecorder()
    speech_recognizer = SpeechRecognizer()

    # Ana pencereyi oluştur ve göster
    window = MainWindow(audio_recorder, speech_recognizer)
    window.show()

    # Uygulamayı çalıştır
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()