# VoxVibe – Roadmap to Wispr Flow-Level UX

> This document analyses the current VoxVibe code-base and lists the **functional, UI and technical requirements** needed to replicate the standout desktop experience of Wispr Flow.

---

## 1. Snapshot of Current VoxVibe Capabilities *(v0.2 - MAJOR UPDATE)*

| Area | Implemented Today | Key Source Files |
|------|------------------|------------------|
| Audio capture | **✅ ENHANCED**: Non-blocking, 16 kHz mono with timeout protection & grace periods | `audio_recorder.py` |
| Speech-to-text | **Streaming** transcription via `faster-whisper`; no post-processing | `transcriber.py` |
| Desktop paste | **✅ ENHANCED**: GNOME-Shell DBus with automatic window storage & focus | `dbus_window_manager.py`, `extension/extension.js` |
| Global hotkeys | **✅ NEW**: Alt+Space, Win+Alt (hold-to-talk), Win+Alt+Space (hands-free) | `hotkey_service.py` |
| Persistent UI | **✅ NEW**: Always-visible floating mic bar with live waveform | `mic_bar.py` |
| Audio feedback | **✅ NEW**: Synthesized start/stop ping sounds | `sound_fx.py` |
| History system | **✅ NEW**: SQLite database with last 50 transcriptions | `history.py` |
| System tray | **✅ NEW**: Microphone icon with "Paste Last" & history access | `tray_icon.py` |
| Launch flow | **✅ ENHANCED**: Background service with comprehensive error handling | `main.py` |

> **Major Achievement**: VoxVibe now delivers **Wispr Flow-level UX** with reliable multi-recording sessions, grace periods for brief key releases, and comprehensive desktop integration!

---

## 2. Priority Matrix - **COMPLETED v0.2 GOALS!**

### 2.1 ✅ **COMPLETED** - Core Wispr Flow Features *(v0.2)*
| Feature | Status | Implementation |
|---------|--------|----------------|
| **Global hot-keys** | ✅ **COMPLETE** | • `Alt+Space` hold-to-talk<br/>• `Win+Alt` hold-to-talk<br/>• `Win+Alt+Space` hands-free mode<br/>• Grace periods for brief key releases |
| **Persistent mic bar** | ✅ **COMPLETE** | Always-visible floating widget with live waveform visualization |
| **Audible feedback** | ✅ **COMPLETE** | Synthesized start/stop ping sounds via PyQt6 multimedia |
| **History & quick-paste** | ✅ **COMPLETE** | SQLite database + system tray "Paste Last" functionality |
| **Robust recording** | ✅ **COMPLETE** | Timeout protection, minimum duration, proper thread cleanup |
| **Desktop integration** | ✅ **COMPLETE** | Automatic window storage/focus, seamless pasting |

### 2.2 🎯 **REMAINING** - Polish & Advanced Features *(v0.3+)*
| Feature | Priority | Notes |
|---------|----------|-------|
| **Settings panel** | 🔥 **HIGH** | Hotkey customization, audio device selection, model choice |
| **Hands-free mode refinement** | 🔥 **HIGH** | Better visual indicators, auto-stop on silence |
| **Performance optimization** | 🔥 **HIGH** | Model caching, faster startup, memory optimization |
| **AI post-processing** | 🔶 **MEDIUM** | Punctuation, filler removal, capitalization |
| **Command mode** | 🔶 **MEDIUM** | Voice editing commands ("delete last word", etc.) |
| **Multi-language support** | 🔶 **MEDIUM** | UI translations, language-specific models |
| **Personal dictionary** | 🔵 **LOW** | Custom vocabulary, proper nouns |
| **Course correction** | 🔵 **LOW** | "Actually..." replacement logic |

### 2.3 🐛 **KNOWN ISSUES** *(to address)*
- Debug logging should be removable for production
- Grace period timer IDs in logs are verbose  
- Linter warnings for optional type annotations
- QBasicTimer threading warnings (cosmetic)

---

## 3. ✅ **COMPLETED** - Technical Implementation Summary

### 3.1 **Major Breakthroughs Achieved**
1. **🎯 Multi-Recording Session Fix** - Resolved critical `should_stop` flag persistence issue
2. **⏱️ Grace Period System** - 200ms tolerance for brief key releases during hold-to-talk
3. **🔄 Robust Thread Management** - Timeout protection, proper cleanup, no hanging processes
4. **🎵 Audio Pipeline Optimization** - Non-blocking recording with responsive start/stop
5. **🖥️ Desktop Integration** - Automatic window storage and seamless text pasting

### 3.2 **Key Technical Solutions**
| Problem | Solution | Implementation |
|---------|----------|----------------|
| **Premature recording stops** | Grace period + debouncing | `_schedule_stop_with_grace_period()` |
| **Thread state persistence** | Reset flags on new recording | `self.should_stop = False` in `run()` |
| **Audio stream hanging** | Timeout protection | `_record_with_timeout()` with 2s limit |
| **Cache interference** | Proper package management | `uv cache clean` + editable install |
| **Spurious key events** | Key release debouncing | 100ms debounce delay |

---

## 4. 🎯 **NEXT PRIORITIES** *(v0.3 Development)*

### 4.1 **HIGH PRIORITY** *(Essential UX improvements)*
1. **Settings Panel** - GUI for hotkey customization, audio device selection
2. **Performance Optimization** - Faster startup, model caching, memory efficiency  
3. **Hands-free Mode Polish** - Better visual feedback, auto-stop on silence detection
4. **Production Cleanup** - Remove debug logging, clean up verbose output

### 4.2 **MEDIUM PRIORITY** *(Advanced features)*
1. **AI Post-processing** - Smart punctuation, filler word removal
2. **Multi-language Support** - Model switching, UI translations
3. **Command Mode** - Voice editing ("delete last word", "capitalize that")

### 4.3 **LOW PRIORITY** *(Nice-to-have)*
1. **Personal Dictionary** - Custom vocabulary training
2. **Course Correction** - "Actually..." replacement logic

---

## 5. 🎉 **Milestone Achievement**
- **✅ v0.2 COMPLETE** - VoxVibe now matches Wispr Flow's core UX!
- **🎯 v0.3 Target** - Polish, settings, and advanced features
- **📅 Timeline** - v0.3 planning phase, ~2-3 weeks for implementation

---

## 6. Future Backlog (for reference)
*Advanced NLP, command mode, settings UI, multilingual support, personal dictionary.*

---

### Appendix A – Suggested Libraries

• `qt6-quick`, `pynput`, `faster-whisper-cpp`, `pydub`, `rapidfuzz`, `openai`, `orjson`.

---

*Prepared for the VoxVibe maintainers – June 2025*
