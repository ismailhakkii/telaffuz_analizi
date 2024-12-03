# src/analysis/pronunciation_analyzer.py

import librosa
import numpy as np
from difflib import SequenceMatcher
import re


class PronunciationAnalyzer:
    def __init__(self):
        # Türkçe fonemlerin ideal frekans aralıkları
        self.turkish_phonemes = {
            'a': {'frequency_range': (700, 1100), 'common_errors': ['e', 'ı']},
            'e': {'frequency_range': (500, 700), 'common_errors': ['i', 'a']},
            'i': {'frequency_range': (300, 500), 'common_errors': ['ı', 'e']},
            'o': {'frequency_range': (500, 900), 'common_errors': ['u', 'ö']},
            'u': {'frequency_range': (300, 500), 'common_errors': ['ü', 'o']},
            'ü': {'frequency_range': (200, 400), 'common_errors': ['u', 'i']},
            'ö': {'frequency_range': (400, 600), 'common_errors': ['o', 'u']},
            'ı': {'frequency_range': (300, 500), 'common_errors': ['i', 'e']}
        }

    def analyze_pronunciation(self, audio_path, target_text, recognized_text):
        """
        Hedef metin ile tanınan metni karşılaştırarak telaffuz analizi yapar
        """
        try:
            # Ses dosyasından özellikleri çıkar
            y, sr = librosa.load(audio_path, sr=None)

            # Metinleri kelimelere ayır
            target_words = self._clean_and_split_text(target_text)
            recognized_words = self._clean_and_split_text(recognized_text)

            # Kelime bazlı analiz
            word_analysis = self._analyze_words(target_words, recognized_words, y, sr)

            # Genel skor hesapla
            total_score = np.mean([w['score'] for w in word_analysis])

            # Geri bildirim oluştur
            feedback = self._generate_detailed_feedback(word_analysis)

            return {
                'total_score': total_score,
                'word_analysis': word_analysis,
                'feedback': feedback
            }

        except Exception as e:
            print(f"Telaffuz analizi hatası: {str(e)}")
            return None

    def _clean_and_split_text(self, text):
        """Metni temizler ve kelimelere ayırır"""
        # Noktalama işaretlerini kaldır ve küçük harfe çevir
        cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
        return cleaned_text.split()

    def _analyze_words(self, target_words, recognized_words, audio_data, sample_rate):
        """Her kelime için detaylı analiz yapar"""
        word_analysis = []

        # Ses dosyasını segmentlere ayır
        segments = self._segment_audio(audio_data, sample_rate, len(recognized_words))

        for i, (target, segment) in enumerate(zip(target_words, segments)):
            recognized = recognized_words[i] if i < len(recognized_words) else ""

            # Kelime bazlı karşılaştırma yap
            similarity = SequenceMatcher(None, target, recognized).ratio()

            # Ses özelliklerini analiz et
            phonetic_score = self._analyze_phonemes_in_word(target, segment, sample_rate)

            # Kelime için toplam skor hesapla
            word_score = (similarity + phonetic_score) / 2

            word_analysis.append({
                'target_word': target,
                'recognized_word': recognized,
                'score': word_score,
                'is_correct': similarity > 0.8,
                'error_type': self._determine_error_type(target, recognized) if similarity < 0.8 else None
            })

        return word_analysis

    def _segment_audio(self, audio_data, sample_rate, num_words):
        """Ses dosyasını kelime sayısına göre segmentlere ayırır"""
        # Basit olarak eşit parçalara böl
        segment_length = len(audio_data) // num_words
        return [audio_data[i:i + segment_length] for i in range(0, len(audio_data), segment_length)][:num_words]

    def _analyze_phonemes_in_word(self, word, audio_segment, sample_rate):
        """Kelime içindeki fonemleri analiz eder"""
        scores = []
        for char in word:
            if char in self.turkish_phonemes:
                freq_range = self.turkish_phonemes[char]['frequency_range']
                score = self._check_frequency_range(audio_segment, sample_rate, freq_range)
                scores.append(score)

        return np.mean(scores) if scores else 0.5

    def _check_frequency_range(self, audio_data, sr, freq_range):
        """Belirli bir frekans aralığındaki enerjiyi kontrol eder"""
        spectrogram = np.abs(librosa.stft(audio_data))
        freq_bins = librosa.fft_frequencies(sr=sr)

        lower_bin = np.searchsorted(freq_bins, freq_range[0])
        upper_bin = np.searchsorted(freq_bins, freq_range[1])

        energy = np.mean(spectrogram[lower_bin:upper_bin])
        total_energy = np.mean(spectrogram)

        return min(1.0, energy / total_energy)

    def _determine_error_type(self, target, recognized):
        """Telaffuz hatasının türünü belirler"""
        if not recognized:
            return "eksik_telaffuz"

        if len(target) != len(recognized):
            return "uzunluk_hatası"

        errors = []
        for t_char, r_char in zip(target, recognized):
            if t_char != r_char:
                if t_char in self.turkish_phonemes and r_char in self.turkish_phonemes[t_char]['common_errors']:
                    errors.append(f"{t_char}-{r_char}_karışımı")

        return errors if errors else "belirsiz_hata"

    def _generate_detailed_feedback(self, word_analysis):
        """Detaylı geri bildirim oluşturur"""
        feedback = []

        # Genel durum değerlendirmesi
        correct_words = sum(1 for w in word_analysis if w['is_correct'])
        total_words = len(word_analysis)

        feedback.append(f"Toplam {total_words} kelimeden {correct_words} tanesi doğru telaffuz edildi.")

        # Hatalı kelimeler için özel geri bildirimler
        for word in word_analysis:
            if not word['is_correct']:
                target = word['target_word']
                recognized = word['recognized_word']
                error_type = word['error_type']

                if error_type == "eksik_telaffuz":
                    feedback.append(f"'{target}' kelimesi eksik veya anlaşılamadı.")
                elif error_type == "uzunluk_hatası":
                    feedback.append(f"'{target}' kelimesinin uzunluğu yanlış telaffuz edildi.")
                elif isinstance(error_type, list):
                    for error in error_type:
                        t_char, r_char = error.split('-')[0], error.split('-')[1].split('_')[0]
                        feedback.append(f"'{target}' kelimesinde '{t_char}' sesi '{r_char}' olarak telaffuz edildi.")

                # Telaffuz önerisi
                feedback.append(f"Öneri: '{target}' kelimesini daha net ve vurgulu telaffuz etmeyi deneyin.")

        return feedback