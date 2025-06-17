import subprocess
import os
import time
import json
from typing import Optional

try:
    from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusReply
    QTDBUS_AVAILABLE = True
except ImportError:
    QTDBUS_AVAILABLE = False


class WindowManager:
    def __init__(self):
        """Initialize window manager with auto-detection of display server"""
        self.display_server = self._detect_display_server()
        self.previous_window_id = None
        
    def _detect_display_server(self) -> str:
        """Detect if running on X11 or Wayland"""
        if os.environ.get('WAYLAND_DISPLAY'):
            return 'wayland'
        elif os.environ.get('DISPLAY'):
            return 'x11'
        else:
            return 'unknown'
    
    def get_active_window(self) -> Optional[str]:
        """Get the ID/info of the currently active window"""
        # Try QtDBus approach first (works on GNOME/Wayland)
        if QTDBUS_AVAILABLE:
            window_info = self._get_active_window_qtdbus()
            if window_info:
                return window_info
        
        # Fallback to xdotool for X11
        if self.display_server == 'x11':
            try:
                result = subprocess.run(
                    ['xdotool', 'getactivewindow'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                return result.stdout.strip() if result.returncode == 0 else None
            except Exception as e:
                print(f"Error getting active window with xdotool: {e}")
        
        return "unknown_window"
    
    def _get_active_window_qtdbus(self) -> Optional[str]:
        """Get active window info using QtDBus (GNOME Shell)"""
        try:
            # Connect to session bus
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                print("Cannot connect to session bus")
                return None
            
            # Create interface to GNOME Shell
            shell = QDBusInterface(
                "org.gnome.Shell",
                "/org/gnome/Shell", 
                "org.gnome.Shell",
                bus
            )
            
            if not shell.isValid():
                print("GNOME Shell DBus interface not available")
                return None
            
            # Get the focused window via GNOME Shell
            js_code = """
                let win = global.display.get_focus_window();
                if (win) {
                    JSON.stringify({
                        title: win.get_title(),
                        wm_class: win.get_wm_class(),
                        id: win.get_id()
                    });
                } else {
                    null;
                }
            """
            
            reply = shell.call("Eval", js_code)
            
            if reply.type() != QDBusReply.NoError:
                print(f"DBus call failed: {reply.error().message()}")
                return None
            
            # Parse the reply - GNOME Shell Eval returns [success, result]
            result = reply.value()
            if result and len(result) >= 2 and result[0] and result[1]:
                window_data = result[1]
                print(f"Active window via QtDBus: {window_data}")
                return window_data
                
        except Exception as e:
            print(f"Error getting active window via QtDBus: {e}")
        
        return None
    
    def store_current_window(self):
        """Store the currently active window before showing our app"""
        self.previous_window_id = self.get_active_window()
        print(f"Stored previous window: {self.previous_window_id}")
    
    def focus_previous_window(self) -> bool:
        """Focus the previously active window"""
        if not self.previous_window_id:
            print("No previous window stored")
            return False
        
        # Try QtDBus approach first (GNOME/Wayland)
        if QTDBUS_AVAILABLE:
            success = self._focus_window_qtdbus()
            if success:
                return True
        
        # Fallback to xdotool for X11
        if self.display_server == 'x11' and self.previous_window_id != "unknown_window":
            try:
                result = subprocess.run(
                    ['xdotool', 'windowfocus', self.previous_window_id],
                    capture_output=True,
                    timeout=2
                )
                if result.returncode == 0:
                    print("✅ Focused previous window with xdotool")
                    return True
            except Exception as e:
                print(f"xdotool focus failed: {e}")
        
        # Last resort fallback
        print("Trying Alt+Tab fallback...")
        return self._alt_tab_fallback()
    
    def _focus_window_qtdbus(self) -> bool:
        """Focus the previous window using QtDBus and stored window info"""
        try:
            # Connect to session bus
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                print("Cannot connect to session bus")
                return False
            
            # Create interface to GNOME Shell
            shell = QDBusInterface(
                "org.gnome.Shell",
                "/org/gnome/Shell", 
                "org.gnome.Shell",
                bus
            )
            
            if not shell.isValid():
                print("GNOME Shell DBus interface not available")
                return False
            
            # Parse the stored window data
            if isinstance(self.previous_window_id, str) and self.previous_window_id.startswith('{'):
                window_data = json.loads(self.previous_window_id)
                window_id = window_data.get('id')
                
                if window_id:
                    # Use GNOME Shell to activate the window by ID
                    js_code = f"""
                        let windows = global.get_window_actors();
                        for (let i = 0; i < windows.length; i++) {{
                            let win = windows[i].get_meta_window();
                            if (win.get_id() == {window_id}) {{
                                win.activate(global.get_current_time());
                                true;
                                break;
                            }}
                        }}
                        false;
                    """
                    
                    reply = shell.call("Eval", js_code)
                    
                    if reply.type() == QDBusReply.NoError:
                        result = reply.value()
                        if result and len(result) >= 2 and result[0]:
                            print(f"✅ Focused previous window via QtDBus (ID: {window_id})")
                            return True
                        else:
                            print(f"❌ Could not find window with ID: {window_id}")
                        
            # If we can't parse window data or find the specific window,
            # try to focus the most recent non-voxvibe window
            js_code = """
                let windows = global.get_window_actors();
                for (let i = 0; i < windows.length; i++) {
                    let win = windows[i].get_meta_window();
                    let wm_class = win.get_wm_class();
                    if (wm_class && wm_class.toLowerCase() !== 'python' && 
                        !wm_class.toLowerCase().includes('voice')) {
                        win.activate(global.get_current_time());
                        true;
                        break;
                    }
                }
                false;
            """
            
            reply = shell.call("Eval", js_code)
            
            if reply.type() == QDBusReply.NoError:
                result = reply.value()
                if result and len(result) >= 2 and result[0]:
                    print("✅ Focused most recent non-voxvibe window")
                    return True
                
        except Exception as e:
            print(f"Error focusing window via QtDBus: {e}")
        
        return False
    
    def _alt_tab_fallback(self) -> bool:
        """Fallback method using keyboard simulation"""
        try:
            # Try different methods for sending Alt+Tab
            methods = [
                # Method 1: using gdbus to send key events (GNOME specific)
                ['gdbus', 'call', '--session', '--dest', 'org.gnome.Shell',
                 '--object-path', '/org/gnome/Shell', '--method',
                 'org.gnome.Shell.Eval', 'global.stage.get_key_focus().event(new Clutter.Event(Clutter.EventType.KEY_PRESS))'],
                 
                # Method 2: xdotool if available (works on X11)
                ['xdotool', 'key', 'alt+Tab'],
                
                # Method 3: ydotool if available (works on Wayland)
                ['ydotool', 'key', 'alt+Tab']
            ]
            
            for method in methods:
                try:
                    result = subprocess.run(method, capture_output=True, timeout=1)
                    if result.returncode == 0:
                        return True
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue
                    
        except Exception as e:
            print(f"Alt+Tab fallback failed: {e}")
        
        return False
    
    def simulate_paste(self) -> bool:
        """Simulate Ctrl+V paste action using ydotool"""
        try:
            # Use ydotool for Wayland
            print("Simulating Ctrl+V with ydotool...")
            result = subprocess.run(
                ['ydotool', 'key', 'ctrl+v'],
                capture_output=True,
                timeout=3
            )
            
            if result.returncode == 0:
                print("✅ ydotool paste successful")
                return True
            else:
                print(f"❌ ydotool failed with return code: {result.returncode}")
                if result.stderr:
                    print(f"ydotool stderr: {result.stderr.decode()}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ ydotool timed out")
            return False
        except FileNotFoundError:
            print("❌ ydotool not found - please install it")
            return False
        except Exception as e:
            print(f"❌ ydotool error: {e}")
            return False
    
    def paste_to_previous_window(self, delay_ms=500) -> bool:
        """
        Focus previous window and paste clipboard contents
        
        Args:
            delay_ms: Delay in milliseconds between focus and paste
            
        Returns:
            True if successful, False otherwise
        """
        # First focus the previous window
        focus_success = self.focus_previous_window()
        
        # Wait a bit for the window to become active
        time.sleep(delay_ms / 1000.0)
        
        # Then simulate paste
        paste_success = self.simulate_paste()
        
        print(f"Focus: {focus_success}, Paste: {paste_success}")
        return focus_success and paste_success
    
    def check_dependencies(self) -> dict:
        """Check which window management tools are available"""
        tools = {}
        
        if self.display_server == 'x11':
            tools['xdotool'] = subprocess.run(['which', 'xdotool'], capture_output=True).returncode == 0
        elif self.display_server == 'wayland':
            tools['ydotool'] = subprocess.run(['which', 'ydotool'], capture_output=True).returncode == 0
        
        return {
            'display_server': self.display_server,
            'tools': tools
        }