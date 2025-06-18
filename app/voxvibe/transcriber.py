import os
from typing import Optional

import numpy as np
from faster_whisper import WhisperModel


class Transcriber:
    def __init__(self, model_size="base", device="auto", compute_type="auto"):
        """
        Initialize the Whisper transcriber.
        
        Args:
            model_size: Size of the Whisper model ("tiny", "base", "small", "medium", "large-v2", "large-v3")
            device: Device to run on ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "int16", "float16", "float32", "auto")
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.model = None
        
        # Initialize model lazily to avoid long startup times
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        try:
            print(f"Loading Whisper model: {self.model_size}")
            
            # Use CPU for better compatibility
            if self.device == "auto":
                device = "cpu"
            else:
                device = self.device
            
            if self.compute_type == "auto":
                compute_type = "int8" if device == "cpu" else "float16"
            else:
                compute_type = self.compute_type
            
            self.model = WhisperModel(
                self.model_size,
                device=device,
                compute_type=compute_type,
                download_root=os.path.expanduser("~/.cache/whisper")
            )
            print(f"Model loaded successfully on {device} with {compute_type}")
            
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            raise
    
    def transcribe(self, audio_data: np.ndarray, language="en") -> Optional[str]:
        """
        Transcribe audio data to text.
        
        Args:
            audio_data: Numpy array of audio data (float32, mono, 16kHz)
            language: Language code ("en", "es", "fr", etc.) or None for auto-detection
            
        Returns:
            Transcribed text or None if transcription failed
        """
        if self.model is None:
            print("Model not loaded")
            return None
        
        if audio_data is None or len(audio_data) == 0:
            print("No audio data provided")
            return None
        
        try:
            # Ensure audio is in the correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Check minimum length (at least 0.1 seconds)
            min_samples = int(0.1 * 16000)  # 0.1 seconds at 16kHz
            if len(audio_data) < min_samples:
                print("Audio too short for transcription")
                return None
            
            # Transcribe using faster-whisper
            segments, info = self.model.transcribe(
                audio_data,
                language=language if language != "auto" else None,
                beam_size=5,
                best_of=5,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,  # Voice activity detection
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    max_speech_duration_s=30
                )
            )
            
            # Combine all segments into a single text
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())
            
            if not text_parts:
                print("No speech detected in audio")
                return None
            
            full_text = " ".join(text_parts).strip()
            
            if full_text:
                print(f"Transcribed ({info.language}, {info.language_probability:.2f}): {full_text}")
                return full_text
            else:
                print("Empty transcription result")
                return None
                
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
    
    def get_available_models(self):
        """Get list of available Whisper model sizes"""
        return [
            "tiny",      # ~39 MB
            "base",      # ~74 MB  
            "small",     # ~244 MB
            "medium",    # ~769 MB
            "large-v2",  # ~1550 MB
            "large-v3"   # ~1550 MB
        ]
    
    def get_supported_languages(self):
        """Get list of supported language codes"""
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", 
            "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", 
            "el", "ms", "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", 
            "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn", 
            "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne", 
            "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn", 
            "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", 
            "lo", "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", 
            "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]