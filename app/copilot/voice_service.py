"""
Voice Services for AI Copilot
Handles Speech-to-Text and Text-to-Speech
"""
import os
from typing import BinaryIO, Optional, Dict
import io

import httpx
from dotenv import load_dotenv

load_dotenv()

# Optional providers
try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from gtts import gTTS
except ImportError:
    gTTS = None

try:
    import edge_tts
except ImportError:
    edge_tts = None


class VoiceService:
    """
    Voice interaction service for AI Copilot
    
    Features:
    - Speech-to-Text using Groq Whisper
    - Text-to-Speech using gTTS
    - Multiple language support
    - Audio file handling
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize provider-aware voice services."""
        self.groq_api_key = api_key or os.getenv("GROQ_API_KEY")
        self.stt_provider = os.getenv("STT_PROVIDER", "gnani").strip().lower()
        self.tts_provider = os.getenv("TTS_PROVIDER", "gnani").strip().lower()
        self.gnani_api_key = os.getenv("GNANI_API_KEY")
        self.gnani_base_url = os.getenv("GNANI_BASE_URL", "https://api.vachana.ai").rstrip("/")
        self.gnani_stt_url = os.getenv("GNANI_STT_URL")
        self.gnani_tts_url = os.getenv("GNANI_TTS_URL")

        self.client = Groq(api_key=self.groq_api_key) if Groq and self.groq_api_key else None
        self.whisper_model = "whisper-large-v3"

        self.supported_languages = {
            "en": {
                "name": "English",
                "voices": {
                    "en-IN-NeerjaNeural": "Neerja (Female)",
                    "en-IN-PrabhatNeural": "Prabhat (Male)"
                },
                "default_voice": "en-IN-NeerjaNeural"
            },
            "ta": {
                "name": "Tamil",
                "voices": {
                    "ta-IN-PallaviNeural": "Pallavi (Female)",
                    "ta-IN-ValluvarNeural": "Valluvar (Male)"
                },
                "default_voice": "ta-IN-PallaviNeural"
            },
            "te": {
                "name": "Telugu",
                "voices": {
                    "te-IN-ShrutiNeural": "Shruti (Female)",
                    "te-IN-MohanNeural": "Mohan (Male)"
                },
                "default_voice": "te-IN-ShrutiNeural"
            },
            "hi": {
                "name": "Hindi",
                "voices": {
                    "hi-IN-SwaraNeural": "Swara (Female)",
                    "hi-IN-MadhurNeural": "Madhur (Male)"
                },
                "default_voice": "hi-IN-SwaraNeural"
            }
        }
    
    def transcribe_audio(
        self,
        audio_file,
        language: str = "en"
    ) -> Dict[str, str]:
        """
        Convert speech to text using Groq Whisper
        
        Args:
            audio_file: Audio file (WAV, MP3, etc.)
            language: Language code (en, es, fr, etc.)
            
        Returns:
            Dictionary with transcription and metadata
        """
        try:
            gnani_result = None
            language = self.normalize_language(language)

            if hasattr(audio_file, "read"):
                file_bytes = audio_file.read()
                filename = getattr(audio_file, "name", "audio.wav")
            else:
                with open(audio_file, "rb") as source:
                    file_bytes = source.read()
                filename = os.path.basename(str(audio_file))

            if self.stt_provider == "gnani" and self.gnani_api_key:
                gnani_result = self._transcribe_with_gnani(file_bytes, filename, language)
                if gnani_result.get("success"):
                    return gnani_result

            if self.client:
                try:
                    transcription = self.client.audio.transcriptions.create(
                        file=(filename, file_bytes),
                        model=self.whisper_model,
                        language=language,
                        response_format="json"
                    )
                    return {"text": transcription.text, "language": language, "success": True}
                except Exception as groq_error:
                    if self.stt_provider == "gnani" and self.gnani_api_key:
                        gnani_error = gnani_result.get("error")
                        return {"text": "", "language": language, "error": f"GNANI STT failed: {gnani_error}; Groq fallback failed: {groq_error}", "success": False}
                    return {"text": "", "language": language, "error": str(groq_error), "success": False}

            return {"text": "", "language": language, "error": "No STT provider is configured", "success": False}
        except Exception as e:
            return {"text": "", "language": language, "error": str(e), "success": False}
    
    def text_to_speech(
        self,
        text: str,
        language: str = "en",
        slow: bool = False,
        voice: str = None
    ) -> bytes:
        """
        Convert text to speech using gTTS
        
        Args:
            text: Text to convert
            language: Language code
            slow: Speak slowly
            
        Returns:
            MP3 audio bytes
        """
        language = self.normalize_language(language)
        if voice is None:
            voice = self.supported_languages[language]["default_voice"]
        if voice not in self.supported_languages[language]["voices"]:
            raise ValueError("Unsupported voice for the selected language")

        if self.tts_provider == "gnani" and self.gnani_api_key:
            try:
                return self._synthesize_with_gnani(text, language, slow, voice)
            except Exception as e:
                print(f"GNANI TTS Error: {e}")

        if edge_tts:
            try:
                return self._synthesize_with_edge(text, voice, slow)
            except Exception as e:
                print(f"Edge neural TTS Error: {e}")

        if gTTS:
            try:
                tts = gTTS(text=text, lang=language, slow=slow)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                return audio_buffer.getvalue()
            except Exception as e:
                print(f"TTS Error: {e}")

        return b""
    
    def normalize_language(self, language: str) -> str:
        normalized = (language or "en").strip().lower()
        aliases = {"english": "en", "tamil": "ta", "telugu": "te", "hindi": "hi"}
        normalized = aliases.get(normalized, normalized)
        if normalized not in self.supported_languages:
            raise ValueError("Unsupported language. Choose en, ta, te, or hi.")
        return normalized

    def _synthesize_with_edge(self, text: str, voice: str, slow: bool) -> bytes:
        import subprocess
        import sys
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp:
            output_path = temp.name

        try:
            command = [
                sys.executable,
                "-m",
                "edge_tts",
                "--voice",
                voice,
                "--text",
                text,
                "--rate",
                "-15%" if slow else "+0%",
                "--write-media",
                output_path
            ]
            result = subprocess.run(command, capture_output=True, timeout=90)
            if result.returncode != 0:
                error = result.stderr.decode("utf-8", errors="replace")[:500]
                raise RuntimeError(error or "Edge neural TTS failed")

            with open(output_path, "rb") as audio_file:
                audio = audio_file.read()
            if not audio:
                raise RuntimeError("Edge neural TTS returned empty audio")
            return audio
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def _gnani_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.gnani_api_key}",
            "X-API-Key": self.gnani_api_key,
            "Accept": "application/json, audio/mpeg, audio/wav, */*"
        }

    def _transcribe_with_gnani(self, file_bytes: bytes, filename: str, language: str) -> Dict[str, str]:
        endpoints = tuple(url for url in (
            self.gnani_stt_url,
            f"{self.gnani_base_url}/v1/audio/transcriptions",
            f"{self.gnani_base_url}/audio/transcriptions"
        ) if url)
        mime = "audio/wav" if filename.lower().endswith(".wav") else "application/octet-stream"
        last_error = "GNANI STT request failed"

        for endpoint in endpoints:
            try:
                response = httpx.post(
                    endpoint,
                    headers=self._gnani_headers(),
                    files={"file": (filename, file_bytes, mime)},
                    data={"language": language},
                    timeout=60.0
                )
                if response.status_code >= 400:
                    last_error = f"GNANI STT {response.status_code}: {response.text[:500]}"
                    continue

                payload = response.json()
                text = payload.get("text") or payload.get("transcript") or payload.get("data", {}).get("text", "")
                return {"text": str(text), "language": str(payload.get("language", language)), "success": True}
            except Exception as e:
                last_error = str(e)

        return {"text": "", "language": language, "error": last_error, "success": False}

    def _synthesize_with_gnani(self, text: str, language: str, slow: bool, voice: str = None) -> bytes:
        endpoints = tuple(url for url in (
            self.gnani_tts_url,
            f"{self.gnani_base_url}/v1/audio/speech",
            f"{self.gnani_base_url}/tts",
            f"{self.gnani_base_url}/text-to-speech"
        ) if url)
        payload = {"text": text, "language": language, "slow": slow, "voice": voice}
        last_error = "GNANI TTS request failed"

        for endpoint in endpoints:
            try:
                response = httpx.post(endpoint, headers=self._gnani_headers(), json=payload, timeout=60.0)
                content_type = response.headers.get("content-type", "")
                if response.status_code >= 400:
                    last_error = f"GNANI TTS {response.status_code}: {response.text[:500]}"
                    continue
                if "audio" in content_type or response.content.startswith((b"ID3", b"RIFF", b"\xff\xfb", b"OggS")):
                    return response.content

                payload_response = response.json()
                audio = payload_response.get("audio") or payload_response.get("audio_base64") or payload_response.get("data", {}).get("audio")
                if isinstance(audio, str):
                    import base64
                    return base64.b64decode(audio)
            except Exception as e:
                last_error = str(e)

        raise RuntimeError(last_error)

    def text_to_speech_file(
        self,
        text: str,
        output_path: str,
        language: str = "en",
        slow: bool = False,
        voice: str = None
    ) -> bool:
        """
        Convert text to speech and save to file
        
        Args:
            text: Text to convert
            output_path: Path to save MP3 file
            language: Language code
            slow: Speak slowly
            
        Returns:
            Success status
        """
        try:
            language = self.normalize_language(language)
            if voice is None:
                voice = self.supported_languages[language]["default_voice"]

            if self.tts_provider == "gnani" and self.gnani_api_key:
                audio = self._synthesize_with_gnani(text, language, slow, voice)
            elif edge_tts:
                audio = self._synthesize_with_edge(text, voice, slow)
            elif gTTS:
                tts = gTTS(text=text, lang=language, slow=slow)
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                audio = audio_buffer.getvalue()
            else:
                return False

            with open(output_path, "wb") as output:
                output.write(audio)
            return True
        except Exception as e:
            print(f"TTS File Error: {e}")
            return False
    
    def get_supported_languages(self) -> Dict:
        """Get the four supported languages and their human neural voices."""
        return {
            code: {
                "name": details["name"],
                "default_voice": details["default_voice"],
                "voices": details["voices"]
            }
            for code, details in self.supported_languages.items()
        }


# Singleton instance
_voice_service_instance = None

def get_voice_service() -> VoiceService:
    """Get or create voice service instance"""
    global _voice_service_instance
    
    if _voice_service_instance is None:
        _voice_service_instance = VoiceService()
    
    return _voice_service_instance
