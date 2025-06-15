# Linux Dictation App

A voice dictation application for Linux that captures audio via hotkey and pastes transcribed text into the previously focused application.

## Project Structure

```
dictation-app/
├── README.md
├── requirements.txt
├── setup.py
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── audio/
│   │   ├── __init__.py
│   │   └── recorder.py
│   ├── transcription/
│   │   ├── __init__.py
│   │   └── whisper_transcriber.py
│   ├── system/
│   │   ├── __init__.py
│   │   ├── window_manager.py
│   │   └── clipboard_manager.py
│   ├── ui/
│   │   ├── __init__.py
│   │   └── tray_icon.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── resources/
│   └── icons/
│       └── microphone.svg
└── tests/
    ├── __init__.py
    └── test_audio.py
```

## File Contents

### requirements.txt
```
PyQt6==6.6.1
openai-whisper==20231117
pyaudio==0.2.13
pynput==1.7.6
pyperclip==1.8.2
python-xlib==0.33
dbus-python==1.3.2
numpy==1.24.3
```

### setup.py
```python
from setuptools import setup, find_packages

setup(
    name="linux-dictation-app",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "PyQt6>=6.6.1",
        "openai-whisper",
        "pyaudio>=0.2.13",
        "pynput>=1.7.6",
        "pyperclip>=1.8.2",
        "python-xlib>=0.33",
        "dbus-python>=1.3.2",
        "numpy>=1.24.3",
    ],
    entry_points={
        "console_scripts": [
            "dictation-app=main:main",
        ],
    },
    python_requires=">=3.8",
)
```

### src/main.py
```python
#!/usr/bin/env python3
import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from pynput import keyboard
from audio.recorder import AudioRecorder
from transcription.whisper_transcriber import WhisperTranscriber
from system.window_manager import WindowManager
from system.clipboard_manager import ClipboardManager
from ui.tray_icon import TrayIcon
from config.settings import Settings


class DictationApp:
    def __init__(self):
        self.settings = Settings()
        self.recorder = AudioRecorder()
        self.transcriber = WhisperTranscriber(model_size=self.settings.whisper_model)
        self.window_manager = WindowManager()
        self.clipboard_manager = ClipboardManager()
        self.is_recording = False
        self.last_window_id = None
        
        # Setup hotkey listener
        self.hotkey = keyboard.GlobalHotKeys({
            self.settings.record_hotkey: self.toggle_recording
        })
        self.hotkey.start()
        
        # Setup UI
        self.app = QApplication(sys.argv)
        self.tray = TrayIcon(self)
        
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        print("Starting recording...")
        self.last_window_id = self.window_manager.get_active_window()
        self.is_recording = True
        self.tray.set_recording_state(True)
        self.recorder.start_recording()
    
    def stop_recording(self):
        print("Stopping recording...")
        self.is_recording = False
        self.tray.set_recording_state(False)
        
        audio_data = self.recorder.stop_recording()
        if audio_data:
            self.tray.show_message("Transcribing", "Processing audio...")
            text = self.transcriber.transcribe(audio_data)
            
            if text:
                print(f"Transcribed: {text}")
                self.paste_text(text)
                self.tray.show_message("Success", f"Transcribed: {text[:50]}...")
            else:
                self.tray.show_message("Error", "No speech detected")
    
    def paste_text(self, text):
        if self.last_window_id:
            # Store in clipboard
            self.clipboard_manager.set_text(text)
            
            # Switch to last window and paste
            self.window_manager.focus_window(self.last_window_id)
            # Small delay to ensure window is focused
            QTimer.singleShot(100, lambda: self.window_manager.paste())
    
    def run(self):
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        sys.exit(self.app.exec())
    
    def quit(self):
        self.hotkey.stop()
        self.app.quit()


def main():
    app = DictationApp()
    app.run()


if __name__ == "__main__":
    main()
```

### src/audio/recorder.py
```python
import pyaudio
import numpy as np
import threading
import queue
from typing import Optional


class AudioRecorder:
    def __init__(self, sample_rate=16000, chunk_size=1024):
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        
    def start_recording(self):
        self.is_recording = True
        self.audio_queue = queue.Queue()
        
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )
        
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()
    
    def _record(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                self.audio_queue.put(data)
            except Exception as e:
                print(f"Recording error: {e}")
                break
    
    def stop_recording(self) -> Optional[np.ndarray]:
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join()
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        
        # Combine all audio chunks
        audio_chunks = []
        while not self.audio_queue.empty():
            audio_chunks.append(self.audio_queue.get())
        
        if audio_chunks:
            audio_data = b''.join(audio_chunks)
            # Convert to numpy array
            return np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        return None
    
    def __del__(self):
        if hasattr(self, 'audio'):
            self.audio.terminate()
```

### src/transcription/whisper_transcriber.py
```python
import whisper
import numpy as np
from typing import Optional


class WhisperTranscriber:
    def __init__(self, model_size="base"):
        print(f"Loading Whisper model: {model_size}")
        self.model = whisper.load_model(model_size)
        
    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        try:
            # Whisper expects float32 audio
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Transcribe
            result = self.model.transcribe(
                audio_data,
                language="en",  # Change this for other languages
                fp16=False
            )
            
            text = result["text"].strip()
            return text if text else None
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return None
```

### src/system/window_manager.py
```python
import subprocess
import os
from typing import Optional


class WindowManager:
    def __init__(self):
        self.display_server = self._detect_display_server()
        
    def _detect_display_server(self) -> str:
        """Detect if running on X11 or Wayland"""
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        return 'wayland' if wayland_display else 'x11'
    
    def get_active_window(self) -> Optional[str]:
        """Get the ID of the currently active window"""
        try:
            if self.display_server == 'x11':
                result = subprocess.run(
                    ['xdotool', 'getactivewindow'],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip() if result.returncode == 0 else None
            else:
                # Wayland doesn't allow window introspection easily
                # Store the current focused app using other methods
                return None
        except Exception as e:
            print(f"Error getting active window: {e}")
            return None
    
    def focus_window(self, window_id: str):
        """Focus a window by its ID"""
        try:
            if self.display_server == 'x11' and window_id:
                subprocess.run(['xdotool', 'windowfocus', window_id])
        except Exception as e:
            print(f"Error focusing window: {e}")
    
    def paste(self):
        """Simulate Ctrl+V paste"""
        try:
            if self.display_server == 'x11':
                subprocess.run(['xdotool', 'key', 'ctrl+v'])
            else:
                # For Wayland, use ydotool (needs to be installed separately)
                subprocess.run(['ydotool', 'key', 'ctrl+v'])
        except Exception as e:
            print(f"Error pasting: {e}")
```

### src/system/clipboard_manager.py
```python
import pyperclip
import subprocess
import os


class ClipboardManager:
    def __init__(self):
        self.display_server = os.environ.get('WAYLAND_DISPLAY')
        
    def set_text(self, text: str):
        """Set text to clipboard"""
        try:
            if self.display_server:
                # Use wl-copy for Wayland
                process = subprocess.Popen(
                    ['wl-copy'],
                    stdin=subprocess.PIPE
                )
                process.communicate(text.encode())
            else:
                # Use pyperclip for X11
                pyperclip.copy(text)
        except Exception as e:
            print(f"Clipboard error: {e}")
            # Fallback to pyperclip
            try:
                pyperclip.copy(text)
            except:
                pass
```

### src/ui/tray_icon.py
```python
from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import QTimer


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setup_ui()
        
    def setup_ui(self):
        # Create icon (you'll need to add an actual icon file)
        self.setIcon(QIcon.fromTheme("audio-input-microphone"))
        self.setVisible(True)
        
        # Create menu
        menu = QMenu()
        
        self.status_action = menu.addAction("Ready")
        self.status_action.setEnabled(False)
        
        menu.addSeparator()
        
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.show_settings)
        
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(self.app.quit)
        
        self.setContextMenu(menu)
        
        # Show initial message
        self.show_message("Dictation App", "Press hotkey to start recording")
    
    def set_recording_state(self, is_recording: bool):
        if is_recording:
            self.status_action.setText("Recording...")
            self.setIcon(QIcon.fromTheme("media-record"))
        else:
            self.status_action.setText("Ready")
            self.setIcon(QIcon.fromTheme("audio-input-microphone"))
    
    def show_settings(self):
        # TODO: Implement settings dialog
        self.show_message("Settings", "Settings dialog not implemented yet")
    
    def show_message(self, title: str, message: str):
        self.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 2000)
```

### src/config/settings.py
```python
import json
import os
from pathlib import Path


class Settings:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "dictation-app"
        self.config_file = self.config_dir / "settings.json"
        self.load_settings()
    
    def load_settings(self):
        # Default settings
        self.defaults = {
            "record_hotkey": "<ctrl>+<alt>+r",
            "whisper_model": "base",
            "language": "en",
            "auto_punctuation": True
        }
        
        # Load from file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.defaults.update(saved_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
        
        # Apply settings
        for key, value in self.defaults.items():
            setattr(self, key, value)
    
    def save_settings(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.defaults, f, indent=4)
```

## Installation Instructions

1. **Clone/Create the project structure**
```bash
mkdir dictation-app
cd dictation-app
# Create all directories and files as shown above
```

2. **Set up virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install system dependencies**
```bash
# For Ubuntu/Debian:
sudo apt-get install python3-pyaudio portaudio19-dev
sudo apt-get install xdotool  # For X11
sudo apt-get install wl-clipboard  # For Wayland

# For Wayland input simulation (optional):
# ydotool requires manual installation from github
```

5. **Run the application**
```bash
python src/main.py
```

## Usage

1. The app will appear in your system tray
2. Press `Ctrl+Alt+R` (default hotkey) to start recording
3. Speak your text
4. Press the hotkey again to stop recording
5. The app will transcribe and paste the text into your last focused application

## Configuration

Edit `~/.config/dictation-app/settings.json` to customize:
- Hotkey combination
- Whisper model size (tiny, base, small, medium, large)
- Language
- Other preferences

## Notes

- First run will download the Whisper model (may take a few minutes)
- Wayland support is limited due to security restrictions
- Consider running with `--no-sandbox` flag if you encounter permission issues

## Future Improvements

- [ ] GUI settings dialog
- [ ] Multiple language support
- [ ] Custom wake words
- [ ] Voice activity detection
- [ ] Real-time transcription display
- [ ] Support for multiple clipboard formats
- [ ] Better Wayland integration using desktop portals