"""Simplified hotkey service for VoxVibe.

Supports:
- Win+Alt (hold-to-talk)
"""
import threading
import time
from enum import Enum
from typing import Callable, Optional

import pynput
from pynput import keyboard


class RecordingMode(Enum):
    IDLE = "idle"
    HOLD_TO_TALK = "hold_to_talk" 
    HANDS_FREE = "hands_free"


class HotkeyService:
    def __init__(self):
        self.mode = RecordingMode.IDLE
        self.listener = None
        self.pressed_keys = set()
        
        # Callbacks
        self.on_start_recording: Optional[Callable] = None
        self.on_stop_recording: Optional[Callable] = None
        self.on_mode_change: Optional[Callable[[RecordingMode], None]] = None
        
        # Key mappings - simplified to just Win+Alt
        self.win_alt_combo = {keyboard.Key.cmd, keyboard.Key.alt_l}  # Win+Alt
        
        self._recording = False
        self._lock = threading.Lock()
        
        # Debouncing to prevent spurious key events
        self._key_release_times = {}
        self._debounce_delay = 0.1  # 100ms debounce delay
        
        # Grace period for hold-to-talk combo interruptions
        self._combo_grace_period = 0.2  # 200ms grace period
        self._pending_stop_timer = None
        
    def start(self):
        """Start the hotkey listener service"""
        if self.listener:
            return
            
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
        print("🎯 Hotkey service started")
        
    def stop(self):
        """Stop the hotkey listener service"""
        if self.listener:
            self.listener.stop()
            self.listener = None
        print("🛑 Hotkey service stopped")
        
    def _on_key_press(self, key):
        """Handle key press events"""
        with self._lock:
            # Normalize key representation
            normalized_key = self._normalize_key(key)
            if normalized_key:
                self.pressed_keys.add(normalized_key)
                # Debug: print(f"🔑 Key pressed: {key} -> {normalized_key}, all keys: {self.pressed_keys}")
            
            # Check for hotkey combinations
            self._check_hotkey_combinations()
            
            # Cancel pending stop if combo is restored
            if self._pending_stop_timer and self.mode == RecordingMode.HOLD_TO_TALK:
                win_alt_restored = self.win_alt_combo.issubset(self.pressed_keys)
                if win_alt_restored:
                    print(f"🔑 Combo restored, canceling pending stop")
                    self._pending_stop_timer.cancel()
                    self._pending_stop_timer = None
    
    def _on_key_release(self, key):
        """Handle key release events"""
        with self._lock:
            normalized_key = self._normalize_key(key)
            if normalized_key:
                self.pressed_keys.discard(normalized_key)
                # Debug: print(f"🔑 Key released: {key} -> {normalized_key}, remaining keys: {self.pressed_keys}")
            
            # Handle mode-specific release logic
            self._handle_key_release(normalized_key)
    
    def _normalize_key(self, key):
        """Normalize key representation for consistent comparison"""
        # Handle special keys
        if hasattr(key, 'name') or not hasattr(key, 'char'):
            # Special keys like Alt, Ctrl, Space, Win, etc.
            if key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                return keyboard.Key.cmd
            elif (key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r or
                  key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r):
                # Treat both Alt and Ctrl as the same for compatibility
                return keyboard.Key.alt_l
            elif key == keyboard.Key.space:
                return keyboard.Key.space
            else:
                return key
        
        # Handle character keys
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
        except AttributeError:
            pass
            
        return key
    
    def _check_hotkey_combinations(self):
        """Check if any hotkey combinations are currently pressed"""
        current_keys = self.pressed_keys.copy()
        
        # Win+Alt (hold-to-talk) - simple and reliable
        if self.win_alt_combo.issubset(current_keys):
            if self.mode == RecordingMode.IDLE:
                self._start_hold_to_talk()
    
    def _handle_key_release(self, key):
        """Handle key release logic based on current mode with debouncing"""
        if self.mode == RecordingMode.HOLD_TO_TALK:
            # Debounce key releases to prevent spurious events
            current_time = time.time()
            # Debug: print(f"🔑 Processing key release for {key} at {current_time:.3f}")
            
            if key in self._key_release_times:
                time_since_last_release = current_time - self._key_release_times[key]
                # Debug: print(f"🔑 Time since last release of {key}: {time_since_last_release:.3f}s")
                if time_since_last_release < self._debounce_delay:
                    # Debug: print(f"🔑 DEBOUNCING key release for {key} (too soon: {time_since_last_release:.3f}s < {self._debounce_delay}s)")
                    return
            # else:
                # Debug: print(f"🔑 First release of {key}")
            
            self._key_release_times[key] = current_time
            
            # Check if Win+Alt is still pressed
            win_alt_still_pressed = self.win_alt_combo.issubset(self.pressed_keys)
            
            # Stop if Win+Alt is no longer held (with grace period)
            if not win_alt_still_pressed:
                # Debug: print(f"🔑 Key combo broken, starting grace period. Remaining keys: {self.pressed_keys}")
                self._schedule_stop_with_grace_period()
                
        elif self.mode == RecordingMode.HANDS_FREE:
            # Single Space key releases hands-free mode (when no other keys are pressed)
            if key == keyboard.Key.space and keyboard.Key.space not in self.pressed_keys:
                print("🔑 Space released, exiting hands-free mode")
                self._exit_hands_free_mode()
    
    def _start_hold_to_talk(self):
        """Start hold-to-talk recording"""
        if self._recording:
            return
        
        # Clear any pending timer from previous recording
        if self._pending_stop_timer:
            print(f"🔧 Canceling leftover timer from previous recording")
            self._pending_stop_timer.cancel()
            self._pending_stop_timer = None
            
        self.mode = RecordingMode.HOLD_TO_TALK
        self._recording = True
        
        print(f"🎤 Hold-to-talk started. Current keys: {self.pressed_keys}")
        if self.on_start_recording:
            threading.Thread(target=self.on_start_recording, daemon=True).start()
        if self.on_mode_change:
            threading.Thread(target=lambda: self.on_mode_change(self.mode), daemon=True).start()
    
    def _stop_hold_to_talk(self):
        """Stop hold-to-talk recording"""
        if not self._recording or self.mode != RecordingMode.HOLD_TO_TALK:
            return
            
        self.mode = RecordingMode.IDLE
        self._recording = False
        
        print(f"🛑 Hold-to-talk stopped. Current keys: {self.pressed_keys}")
        if self.on_stop_recording:
            threading.Thread(target=self.on_stop_recording, daemon=True).start()
        if self.on_mode_change:
            threading.Thread(target=lambda: self.on_mode_change(self.mode), daemon=True).start()
    
    def _enter_hands_free_mode(self):
        """Enter hands-free recording mode"""
        self.mode = RecordingMode.HANDS_FREE
        self._recording = True
        
        print("🔒 Hands-free mode activated")
        if self.on_start_recording:
            threading.Thread(target=self.on_start_recording, daemon=True).start()
        if self.on_mode_change:
            threading.Thread(target=lambda: self.on_mode_change(self.mode), daemon=True).start()
    
    def _exit_hands_free_mode(self):
        """Exit hands-free recording mode"""
        if self.mode != RecordingMode.HANDS_FREE:
            return
            
        self.mode = RecordingMode.IDLE
        self._recording = False
        
        print("🔓 Hands-free mode deactivated")
        if self.on_stop_recording:
            threading.Thread(target=self.on_stop_recording, daemon=True).start()
        if self.on_mode_change:
            threading.Thread(target=lambda: self.on_mode_change(self.mode), daemon=True).start()
    
    def _schedule_stop_with_grace_period(self):
        """Schedule a stop with grace period to allow for brief key releases"""
        # Cancel any existing pending stop
        if self._pending_stop_timer:
            print(f"🔧 Canceling existing pending timer")
            self._pending_stop_timer.cancel()
        
        # Schedule stop after grace period
        self._pending_stop_timer = threading.Timer(
            self._combo_grace_period, 
            self._check_delayed_stop
        )
        self._pending_stop_timer.start()
        # Debug: print(f"🔑 Scheduled stop check in {self._combo_grace_period}s (timer: {id(self._pending_stop_timer)})")
    
    def _check_delayed_stop(self):
        """Check if we should still stop after the grace period"""
        print(f"🔧 Grace period timer fired (timer: {id(self._pending_stop_timer)})")
        
        # Check if combo is still broken
        win_alt_still_pressed = self.win_alt_combo.issubset(self.pressed_keys)
        
        if not win_alt_still_pressed:
            print(f"🔑 Grace period expired, stopping hold-to-talk. Keys: {self.pressed_keys}")
            self._stop_hold_to_talk()
        else:
            print(f"🔑 Combo restored during grace period, continuing. Keys: {self.pressed_keys}")
        
        self._pending_stop_timer = None
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording"""
        return self._recording
    
    @property
    def current_mode(self) -> RecordingMode:
        """Get current recording mode"""
        return self.mode 