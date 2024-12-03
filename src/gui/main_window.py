# src/gui/main_window.py

from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QProgressBar,
                             QTextEdit, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
import os


class MainWindow(QMainWindow):
    def __init__(self, audio_recorder, speech_recognizer, pronunciation_analyzer):
        super().__init__()
        self.audio_recorder = audio_recorder
        self.speech_recognizer = speech_recognizer
        self.pronunciation_analyzer = pronunciation_analyzer

        # Durum değişkenleri
        self.is_recording = False
        self.recording_duration = 0
        self.target_text = ""

        self.setup_ui()

    def setup_ui(self):
        """Gelişmiş kullanıcı arayüzünü oluşturur"""
        self.setWindowTitle("Türkçe Telaffuz Analizi")
        self.setMinimumSize(800, 600)

        # Ana widget ve layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Başlık
        title = QLabel("Türkçe Telaffuz Analizi")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # Hedef metin girişi
        text_input_label = QLabel("Telaffuz edilecek metni girin:")
        text_input_label.setStyleSheet("font-size: 14px; margin-top: 10px;")
        main_layout.addWidget(text_input_label)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Örnek: Merhaba, benim adım İsmail ve ben bir öğrenciyim.")
        self.text_input.setMaximumHeight(100)
        self.text_input.textChanged.connect(self.update_target_text)
        main_layout.addWidget(self.text_input)

        # Butonlar için yatay düzen
        button_layout = QHBoxLayout()

        # Kayıt butonu
        self.record_button = QPushButton("Kayıt Başlat")
        self.record_button.setEnabled(False)  # Metin girilene kadar devre dışı
        self.record_button.clicked.connect(self.toggle_recording)
        self.record_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.record_button)

        # Dosya seçme butonu
        self.file_button = QPushButton("Ses Dosyası Seç")
        self.file_button.setEnabled(False)  # Metin girilene kadar devre dışı
        self.file_button.clicked.connect(self.select_file)
        self.file_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_layout.addWidget(self.file_button)

        main_layout.addLayout(button_layout)

        # Kayıt süresi göstergesi
        self.duration_label = QLabel("Kayıt Süresi: 0:00")
        self.duration_label.setAlignment(Qt.AlignCenter)
        self.duration_label.hide()
        main_layout.addWidget(self.duration_label)

        # İlerleme çubuğu
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # Sonuçlar için kaydırılabilir alan
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
        """)

        # Sonuç widget'ı
        self.result_widget = QWidget()
        self.result_layout = QVBoxLayout(self.result_widget)

        # Tanınan metin etiketi
        self.recognized_text_label = QLabel()
        self.recognized_text_label.setWordWrap(True)
        self.recognized_text_label.setStyleSheet("padding: 10px;")
        self.result_layout.addWidget(self.recognized_text_label)

        # Kelime analizi etiketi
        self.word_analysis_label = QLabel()
        self.word_analysis_label.setWordWrap(True)
        self.word_analysis_label.setStyleSheet("padding: 10px;")
        self.result_layout.addWidget(self.word_analysis_label)

        # Geri bildirim etiketi
        self.feedback_label = QLabel()
        self.feedback_label.setWordWrap(True)
        self.feedback_label.setStyleSheet("padding: 10px;")
        self.result_layout.addWidget(self.feedback_label)

        scroll_area.setWidget(self.result_widget)
        main_layout.addWidget(scroll_area)

        # Zamanlayıcı
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_duration)

    def update_target_text(self):
        """Hedef metin değiştiğinde butonları günceller"""
        text = self.text_input.toPlainText().strip()
        self.target_text = text

        # Butonları metin varsa aktif et
        has_text = bool(text)
        self.record_button.setEnabled(has_text)
        self.file_button.setEnabled(has_text)

    def toggle_recording(self):
        """Kayıt başlatma/durdurma işlemini yönetir"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        """Kayıt işlemini başlatır"""
        self.record_button.setText("Kaydı Durdur")
        self.record_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.file_button.setEnabled(False)
        self.text_input.setEnabled(False)
        self.recording_duration = 0
        self.duration_label.show()
        self.clear_results()

        self.audio_recorder.start_recording()
        self.timer.start(1000)
        self.is_recording = True

    def stop_recording(self):
        """Kayıt işlemini durdurur ve analizi başlatır"""
        self.record_button.setText("Kayıt Başlat")
        self.record_button.setStyleSheet("""
            QPushButton {
                padding: 10px;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        self.file_button.setEnabled(True)
        self.text_input.setEnabled(True)
        self.timer.stop()
        self.audio_recorder.stop_recording()

        filename = self.audio_recorder.save_recording()
        if filename:
            self.analyze_audio(filename)

        self.is_recording = False
        self.duration_label.hide()

    def select_file(self):
        """Ses dosyası seçme penceresini açar"""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Ses Dosyası Seç",
            "",
            "Ses Dosyaları (*.wav)"
        )
        if filename:
            self.clear_results()
            self.analyze_audio(filename)

    def update_duration(self):
        """Kayıt süresini günceller"""
        self.recording_duration += 1
        minutes = self.recording_duration // 60
        seconds = self.recording_duration % 60
        self.duration_label.setText(f"Kayıt Süresi: {minutes}:{seconds:02d}")

    def clear_results(self):
        """Sonuç alanlarını temizler"""
        self.recognized_text_label.setText("")
        self.word_analysis_label.setText("")
        self.feedback_label.setText("")

    def analyze_audio(self, filename):
        """Ses dosyasını analiz eder ve sonuçları gösterir"""
        self.progress_bar.show()
        self.progress_bar.setRange(0, 0)

        try:
            # Metne çevir
            recognized_text = self.speech_recognizer.transcribe_audio(filename)

            if recognized_text:
                # Telaffuz analizi yap
                results = self.pronunciation_analyzer.analyze_pronunciation(
                    filename,
                    self.target_text,
                    recognized_text
                )

                if results:
                    self.show_results(recognized_text, results)
                else:
                    self.show_error("Telaffuz analizi yapılamadı.")
            else:
                self.show_error("Ses tanıma başarısız oldu!")

        except Exception as e:
            self.show_error(f"Hata: {str(e)}")

        finally:
            self.progress_bar.hide()

    def show_results(self, recognized_text, results):
        """Analiz sonuçlarını gösterir"""
        # Tanınan metin
        self.recognized_text_label.setText(
            f"<h3>Hedef Metin:</h3>"
            f"<p>{self.target_text}</p>"
            f"<h3>Tanınan Metin:</h3>"
            f"<p>{recognized_text}</p>"
        )

        # Kelime analizi
        word_analysis_text = "<h3>Kelime Analizi:</h3><p>"
        for word in results['word_analysis']:
            color = "#27ae60" if word['is_correct'] else "#e74c3c"
            score = word['score'] * 100
            word_analysis_text += (
                f"<span style='color: {color};'>"
                f"{word['target_word']}: {score:.1f}%"
                f"</span> | "
            )
        word_analysis_text += "</p>"

        self.word_analysis_label.setText(word_analysis_text)

        # Geri bildirimler
        feedback_text = "<h3>Öneriler:</h3><ul>"
        for feedback in results['feedback']:
            feedback_text += f"<li>{feedback}</li>"
        feedback_text += "</ul>"

        self.feedback_label.setText(feedback_text)

    def show_error(self, message):
        """Hata mesajını gösterir"""
        self.clear_results()
        self.feedback_label.setText(
            f"<p style='color: #e74c3c;'>{message}</p>"
        )