# VoxVibe v0.2 Testing Checklist

> **Instructions:** Run `uv run python -m voxvibe.main` in terminal, then work through each test systematically. Mark ✅ for pass, ❌ for fail, ⚠️ for partial.

---

## 🎯 **Phase 1: Basic Hotkey Functionality**

### Test 1: Win+Alt Hold-to-Talk
- [ ] **Setup:** Open a text editor, place cursor in document
- [ ] **Action:** Hold Win+Alt, say "This is a test message", release
- [ ] **Expected:** 
  - Orange mic indicator appears
  - Recording starts immediately
  - Text appears at cursor location
  - Recording stops on key release
- [ ] **Result:** ________________

### Test 2: Alt+Space Hold-to-Talk
- [ ] **Setup:** Move cursor to new location
- [ ] **Action:** Hold Alt+Space, say "Testing Alt Space combo", release  
- [ ] **Expected:**
  - Same behavior as Win+Alt
  - Text appears where cursor is
- [ ] **Result:** ________________

---

## 🔄 **Phase 2: Hands-Free Mode**

### Test 3: Hands-Free Toggle
- [ ] **Setup:** Cursor in text area
- [ ] **Action:** Press Win+Alt+Space (all three), say "Hands-free mode test", press Space
- [ ] **Expected:**
  - Continuous recording (no need to hold keys)
  - Different visual indicator (magenta?)
  - Stops only when Space is pressed
- [ ] **Result:** ________________

### Test 4: Hands-Free Multiple Sentences
- [ ] **Action:** Win+Alt+Space, say "First sentence. Second sentence. Third sentence.", press Space
- [ ] **Expected:**
  - All sentences captured in one transcription
  - Proper punctuation between sentences
- [ ] **Result:** ________________

---

## 🎵 **Phase 3: Audio & Visual Feedback**

### Test 5: Sound Effects
- [ ] **Action:** Trigger any recording mode
- [ ] **Expected:**
  - Distinct "ping" sound when recording starts
  - Different tone when recording stops
  - Sounds are pleasant, not jarring
- [ ] **Result:** ________________

### Test 6: Mic Bar Visual States
- [ ] **Observe:** Mic bar when idle
- [ ] **Expected:** Subtle pulsing animation
- [ ] **Observe:** Mic bar during recording  
- [ ] **Expected:** Live waveform animation
- [ ] **Result:** ________________

---

## 🖥️ **Phase 4: System Integration**

### Test 7: Text Pasting in Different Apps
- [ ] **Test A:** Record in text editor → text appears
- [ ] **Test B:** Record in browser text field → text appears
- [ ] **Test C:** Record in terminal → text appears
- [ ] **Expected:** Automatic pasting works everywhere
- [ ] **Result:** ________________

### Test 8: System Tray Functionality
- [ ] **Action:** Right-click the microphone tray icon
- [ ] **Expected:**
  - Context menu appears
  - "Paste Last" option visible
  - Recent history submenu populated
- [ ] **Result:** ________________

---

## 📚 **Phase 5: History & Recovery**

### Test 9: History Persistence
- [ ] **Action:** Record 3-4 different short messages
- [ ] **Action:** Right-click tray → check "Recent History"
- [ ] **Expected:**
  - All messages stored with timestamps
  - Most recent appears first
  - Can click to paste any previous message
- [ ] **Result:** ________________

### Test 10: Quick Paste Last
- [ ] **Setup:** Cursor in new location
- [ ] **Action:** Double-click tray icon
- [ ] **Expected:**
  - Most recent transcription gets pasted immediately
  - No menu required
- [ ] **Result:** ________________

---

## 🔬 **Phase 6: Edge Cases**

### Test 11: Short Audio
- [ ] **Action:** Win+Alt, say just "Hi", release quickly
- [ ] **Expected:**
  - Still processes and transcribes
  - No errors with brief audio
- [ ] **Result:** ________________

### Test 12: Background Noise Test
- [ ] **Setup:** Play some background music/noise
- [ ] **Action:** Record normal speech over the noise
- [ ] **Expected:**
  - Speech is still transcribed accurately
  - Background noise filtered out
- [ ] **Result:** ________________

### Test 13: Window Focus Test
- [ ] **Action:** Switch between 3 different apps
- [ ] **Action:** Record a message in each app
- [ ] **Expected:**
  - Text always appears in the currently focused window
  - No pasting in wrong applications
- [ ] **Result:** ________________

### Test 14: Rapid Sequential Tests
- [ ] **Action:** Do 5 quick recordings back-to-back
- [ ] **Expected:**
  - No audio conflicts
  - All transcriptions complete
  - No system slowdown
- [ ] **Result:** ________________

---

## 🎛️ **Phase 7: Advanced Features**

### Test 15: Mic Bar Repositioning
- [ ] **Action:** Drag the mic bar to different screen positions
- [ ] **Expected:**
  - Bar moves smoothly
  - Stays in new position
  - Still functional after moving
- [ ] **Result:** ________________

### Test 16: Tray Icon Hide/Show
- [ ] **Action:** Use tray menu to hide/show mic bar
- [ ] **Expected:**
  - Mic bar disappears/reappears
  - Hotkeys still work when hidden
- [ ] **Result:** ________________

---

## 📊 **Final Assessment**

### Overall System Performance
- [ ] **Startup Time:** App launches quickly
- [ ] **Memory Usage:** No excessive RAM consumption  
- [ ] **CPU Usage:** Low impact when idle
- [ ] **Stability:** No crashes during testing

### User Experience
- [ ] **Intuitive:** Easy to understand and use
- [ ] **Responsive:** Immediate feedback on actions
- [ ] **Reliable:** Consistent behavior across tests
- [ ] **Polished:** Professional look and feel

---

## 🐛 **Issues Found**

| Test # | Issue Description | Severity | Notes |
|--------|------------------|----------|-------|
|        |                  |          |       |
|        |                  |          |       |
|        |                  |          |       |

**Severity Scale:** 🔴 Critical | 🟡 Major | 🟢 Minor

---

## ✅ **Test Summary**

**Passed:** ___/16 tests  
**Failed:** ___/16 tests  
**Partial:** ___/16 tests  

**Overall Status:** 🎯 Ready for Release | ⚠️ Needs Work | ❌ Major Issues

---

*Testing completed on: ________________*  
*VoxVibe version: 0.2.0*  
*Tester: ________________* 