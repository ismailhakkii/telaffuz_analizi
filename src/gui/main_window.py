# src/gui/main_window.py

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QLabel, QFileDialog)
from PyQt5.QtCore import Qt
import os


class MainWindow(QMainWindow):
    def __init__(self, audio_recorder, speech_recognizer):
        super().__init__()
        self.audio_recorder = audio_recorder
        self.speech_recognizer = speech_recognizer
        self.is_recording = False
        self.setup_ui()

    def setup_ui(self):
        """Kullanıcı arayüzünü oluşturur"""
        self.setWindowTitle("Türkçe Telaffuz Analizi")
        self.setMinimumSize(400, 300)

        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Kayıt butonu
        self.record_button = QPushButton("Kayıt Başlat")
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)

        # Dosya seçme butonu
        self.file_button = QPushButton("Dosya Seç")
        self.file_button.clicked.connect(self.select_file)
        layout.addWidget(self.file_button)

        # Sonuç etiketi
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

    def toggle_recording(self):
        """Kayıt başlat/durdur"""
        if not self.is_recording:
            self.record_button.setText("Kaydı Durdur")
            self.file_button.setEnabled(False)
            self.result_label.setText("Kayıt yapılıyor...")
            self.audio_recorder.start_recording()
            self.is_recording = True
        else:
            self.record_button.setText("Kayıt Başlat")
            self.file_button.setEnabled(True)
            self.audio_recorder.stop_recording()

            # Kaydı kaydet ve analiz et
            filename = self.audio_recorder.save_recording()
            if filename:
                self.analyze_audio(filename)
            self.is_recording = False

    def select_file(self):
        """Ses dosyası seç"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Ses Dosyası Seç", "", "Ses Dosyaları (*.wav)"
        )
        if filename:
            self.analyze_audio(filename)

    def analyze_audio(self, filename):
        """Ses dosyasını analiz et"""
        self.result_label.setText("Ses analiz ediliyor...")
        try:
            text = self.speech_recognizer.transcribe_audio(filename)
            self.result_label.setText(f"Tanınan Metin:\n{text}")
        except Exception as e:
            self.result_label.setText(f"Hata: {str(e)}")