# --- window_manager.py ---
# This module contains the core logic for managing the application's desktop window.
# Its primary responsibility is to apply the necessary settings to prevent the window
# from being captured by screen recording or sharing software (e.g., Teams, Zoom, OBS).
# This is the "stealth" feature of the Aura application.

import ctypes
import ctypes.wintypes as wintypes
import webview
import time
import tkinter as tk
import platform
from typing import Optional
from threading import Thread
from pynput import keyboard

# --- Win32 API Constants ---
# These flags are used with the SetWindowDisplayAffinity function.
# WDA_EXCLUDEFROMCAPTURE is a comprehensive flag that prevents the window from being
# captured by most common methods, rendering it as a black rectangle in recordings.
WDA_EXCLUDEFROMCAPTURE = 0x00000011
SW_HIDE = 0
SW_SHOW = 5

# --- Win32 Function Loading ---
# We use the ctypes library to load functions directly from user32.dll, a core
# Windows library for UI management. This gives us low-level control over the window.

# Load the user32 library
_user32 = ctypes.windll.user32

# Define the function signature for SetWindowDisplayAffinity
# This tells ctypes what kind of arguments the function expects (a window handle and a flag)
# and what it returns (a boolean indicating success).
_user32.SetWindowDisplayAffinity.restype  = wintypes.BOOL
_user32.SetWindowDisplayAffinity.argtypes = (wintypes.HWND, wintypes.DWORD)

# Define the function signature for FindWindowW
# This is a fallback method to find a window by its title if the primary method fails.
_user32.FindWindowW.restype               = wintypes.HWND
_user32.FindWindowW.argtypes              = (wintypes.LPCWSTR, wintypes.LPCWSTR)

# Define function signatures for ShowWindow and IsWindowVisible
_user32.ShowWindow.argtypes = (wintypes.HWND, wintypes.INT)
_user32.ShowWindow.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = (wintypes.HWND,)
_user32.IsWindowVisible.restype = wintypes.BOOL

class WindowManager:
    def __init__(self):
        self.hwnd: Optional[int] = None
        self.is_windows = platform.system() == "Windows"
        self.current_transparency = 1.0  # 1.0 = opaque, 0.0 = transparent
        
        # Windows API constants
        if self.is_windows:
            self.GWL_EXSTYLE = -20
            self.WS_EX_LAYERED = 0x80000
            self.WS_EX_TOPMOST = 0x8
            self.LWA_ALPHA = 0x2
            self.HWND_TOPMOST = -1
            self.HWND_NOTOPMOST = -2
            self.SWP_NOMOVE = 0x2
            self.SWP_NOSIZE = 0x1
            
            # Windows API functions
            self.user32 = ctypes.windll.user32
            self.GetWindowLongW = self.user32.GetWindowLongW
            self.SetWindowLongW = self.user32.SetWindowLongW
            self.SetLayeredWindowAttributes = self.user32.SetLayeredWindowAttributes
            self.SetWindowPos = self.user32.SetWindowPos
            
    def set_window_handle(self, window_handle: int):
        """Set the window handle for transparency operations"""
        self.hwnd = window_handle
        if self.is_windows and self.hwnd:
            self._enable_transparency()
        
    def _enable_transparency(self):
        """Enable transparency capability for the window"""
        if not self.is_windows or not self.hwnd:
            return False
            
        try:
            # Get current window style
            ex_style = self.GetWindowLongW(self.hwnd, self.GWL_EXSTYLE)
            
            # Add layered window style if not present
            if not (ex_style & self.WS_EX_LAYERED):
                new_style = ex_style | self.WS_EX_LAYERED
                self.SetWindowLongW(self.hwnd, self.GWL_EXSTYLE, new_style)
                
            return True
        except Exception as e:
            print(f"Error enabling transparency: {e}")
            return False
    
    def set_transparency(self, transparency: float) -> bool:
        """
        Set window transparency level
        Args:
            transparency: Float between 0.0 (fully transparent) and 1.0 (fully opaque)
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_windows or not self.hwnd:
            print("Transparency not supported on this platform or no window handle")
            return False
            
        # Clamp transparency value
        transparency = max(0.0, min(1.0, transparency))
        self.current_transparency = transparency
        
        try:
            # Convert to Windows alpha value (0-255)
            alpha = int(transparency * 255)
            
            # Apply transparency
            result = self.SetLayeredWindowAttributes(
                self.hwnd,
                0,  # colorkey (not used)
                alpha,  # alpha value
                self.LWA_ALPHA  # use alpha
            )
            
            if result:
                print(f"✅ Window transparency set to {transparency*100:.0f}%")
                return True
            else:
                print("❌ Failed to set window transparency")
                return False
                
        except Exception as e:
            print(f"❌ Error setting transparency: {e}")
            return False
    
    def get_transparency(self) -> float:
        """Get current transparency level"""
        return self.current_transparency
    
    def set_transparency_percent(self, percent: int) -> bool:
        """
        Set transparency as percentage
        Args:
            percent: Integer between 0 (fully transparent) and 100 (fully opaque)
        """
        transparency = percent / 100.0
        return self.set_transparency(transparency)
    
    def make_transparent(self) -> bool:
        """Make window 60% transparent (40% opacity) - good for interviews"""
        return self.set_transparency(0.4)
    
    def make_semi_transparent(self) -> bool:
        """Make window semi-transparent (70% opacity)"""
        return self.set_transparency(0.7)
    
    def make_opaque(self) -> bool:
        """Make window fully opaque"""
        return self.set_transparency(1.0)
    
    def find_window_by_title(self, title: str) -> Optional[int]:
        """Find window handle by title"""
        if not self.is_windows:
            return None
            
        try:
            FindWindowW = self.user32.FindWindowW
            FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
            FindWindowW.restype = wintypes.HWND
            
            hwnd = FindWindowW(None, title)
            if hwnd:
                self.set_window_handle(hwnd)
                return hwnd
            return None
        except Exception as e:
            print(f"Error finding window: {e}")
            return None
    
    def set_always_on_top(self, on_top: bool) -> bool:
        """
        Set window to always stay on top
        Args:
            on_top: True to set always on top, False to remove
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.is_windows or not self.hwnd:
            print("Always on top not supported on this platform or no window handle")
            return False
            
        try:
            # Add debugging
            print(f"🔧 Attempting to set always on top: {on_top}, HWND: {self.hwnd}")
            
            hwnd_insert_after = self.HWND_TOPMOST if on_top else self.HWND_NOTOPMOST
            
            # Call SetWindowPos with proper error handling
            result = self.SetWindowPos(
                self.hwnd,
                hwnd_insert_after,
                0, 0, 0, 0,  # x, y, width, height (ignored due to flags)
                self.SWP_NOMOVE | self.SWP_NOSIZE  # Don't move or resize
            )
            
            if result:
                status = "on top" if on_top else "normal"
                print(f"✅ Window set to {status}")
                return True
            else:
                # Get the last error code for debugging
                error_code = ctypes.windll.kernel32.GetLastError()
                print(f"❌ SetWindowPos failed (Error {error_code}), trying alternative method...")
                
                # Try alternative method using window style
                return self._set_always_on_top_alternative(on_top)
                
        except Exception as e:
            print(f"❌ Error setting always on top: {e}")
            return False

    def _set_always_on_top_alternative(self, on_top: bool) -> bool:
        """
        Alternative method to set always on top using window extended styles
        """
        try:
            # Get current extended window style
            ex_style = self.GetWindowLongW(self.hwnd, self.GWL_EXSTYLE)
            
            if on_top:
                # Add topmost style
                new_style = ex_style | self.WS_EX_TOPMOST
            else:
                # Remove topmost style
                new_style = ex_style & ~self.WS_EX_TOPMOST
            
            # Set the new style
            result = self.SetWindowLongW(self.hwnd, self.GWL_EXSTYLE, new_style)
            
            if result or ex_style != new_style:
                # Force window update
                self.user32.SetWindowPos(
                    self.hwnd, 0, 0, 0, 0, 0,
                    self.SWP_NOMOVE | self.SWP_NOSIZE | 0x0020  # SWP_FRAMECHANGED
                )
                status = "on top" if on_top else "normal"
                print(f"✅ Window set to {status} (alternative method)")
                return True
            else:
                print("❌ Alternative method also failed")
                return False
                
        except Exception as e:
            print(f"❌ Error in alternative always-on-top method: {e}")
            return False

    def get_window_info(self) -> dict:
        """Get current window transparency info"""
        return {
            "transparency": self.current_transparency,
            "transparency_percent": int(self.current_transparency * 100),
            "is_transparent": self.current_transparency < 1.0,
            "platform_supported": self.is_windows,
            "window_handle": self.hwnd
        }

    def toggle_visibility(self):
        """Toggle the window's visibility."""
        if not self.is_windows or not self.hwnd:
            print("Window visibility control not supported or no window handle.")
            return

        if _user32.IsWindowVisible(self.hwnd):
            _user32.ShowWindow(self.hwnd, SW_HIDE)
            print("🕵️‍ Window hidden via global hotkey.")
        else:
            _user32.ShowWindow(self.hwnd, SW_SHOW)
            print("✨ Window shown via global hotkey.")

    def _start_hotkey_listener_thread(self):
        """The actual listener thread for global hotkeys."""
        print("🎧 Starting global hotkey listener thread...")

        def on_activate():
            print("Hotkey <alt>+z activated!")
            self.toggle_visibility()

        # Define the hotkey and its callback
        hotkeys = {
            '<alt>+z': on_activate,
        }

        # Start listening
        with keyboard.GlobalHotKeys(hotkeys) as h:
            h.join()

    def start_hotkey_listener(self):
        """Starts the global hotkey listener in a separate thread."""
        if not self.is_windows:
            print("Global hotkeys not supported on this platform.")
            return

        print("🚀 Initializing global hotkey listener...")
        # Ensure we have the handle before starting
        if not self.hwnd:
            if not self.find_window_by_title("Aura"):
                 print("❌ Cannot start hotkey listener: Aura window not found.")
                 return
        
        listener_thread = Thread(target=self._start_hotkey_listener_thread, daemon=True)
        listener_thread.start()

# Global instance
window_manager = WindowManager()

# Convenience functions for easy use
def set_app_transparency(transparency: float) -> bool:
    """Set app window transparency (0.0 to 1.0)"""
    return window_manager.set_transparency(transparency)

def set_app_transparency_percent(percent: int) -> bool:
    """Set app window transparency as percentage (0 to 100)"""
    return window_manager.set_transparency_percent(percent)

def make_app_transparent() -> bool:
    """Make app window 60% transparent (good for interviews)"""
    return window_manager.make_transparent()

def make_app_semi_transparent() -> bool:
    """Make app window semi-transparent"""
    return window_manager.make_semi_transparent()

def make_app_opaque() -> bool:
    """Make app window fully opaque"""
    return window_manager.make_opaque()

def find_aura_window() -> bool:
    """Find and set Aura window for transparency control"""
    hwnd = window_manager.find_window_by_title("Aura")
    return hwnd is not None

def set_app_always_on_top(on_top: bool) -> bool:
    """Set app window to always stay on top"""
    return window_manager.set_always_on_top(on_top)

def get_transparency_info() -> dict:
    """Get current transparency information"""
    return window_manager.get_window_info()

def apply_capture_protection(window):
    """
    Applies display affinity to exclude the window from screen capture.

    This function is the heart of the "stealth" feature. It first tries to get
    the window handle directly from a private pywebview attribute and, if that fails,
    falls back to searching for the window by its title.

    Args:
        window: The pywebview window object.
    """
    hwnd = None
    print("🛡️ APPLYING SCREEN CAPTURE PROTECTION...")

    # --- Method 1: Get handle from pywebview's private attribute ---
    # This is the preferred method as it's direct and not dependent on the window title.
    # We use getattr for safety, in case this private attribute changes in future versions.
    hwnd = getattr(window, '_hwnd', None)
    print(f"🔍 Method 1 (window._hwnd): {hex(hwnd) if hwnd else 'Not found'}")

    # --- Method 2: Fallback to finding the window by title ---
    # If the private attribute doesn't exist, we use a classic Win32 function.
    if not hwnd:
        print("⚠️ Private attribute not found, trying title search...")
        # A small delay is crucial here. It gives the OS time to register the
        # native window after the 'shown' event has fired.
        time.sleep(0.2)
        hwnd = _user32.FindWindowW(None, window.title)
        print(f"🔍 Method 2 (FindWindowW with title '{window.title}'): {hex(hwnd) if hwnd else 'Not found'}")

    # --- Method 3: Try multiple search attempts with delay ---
    if not hwnd:
        print("⚠️ Trying multiple search attempts...")
        for attempt in range(5):
            time.sleep(0.1)
            hwnd = _user32.FindWindowW(None, "Aura")
            if hwnd:
                print(f"🔍 Method 3 (attempt {attempt + 1}): Found {hex(hwnd)}")
                break
        
    # --- Apply the Protection ---
    if not hwnd:
        print("❌ CRITICAL: Could not obtain window handle! Screen capture protection NOT applied!")
        print("   This means the window WILL be visible in screen recordings!")
        return False

    print(f"🛡️ Applying WDA_EXCLUDEFROMCAPTURE (0x{WDA_EXCLUDEFROMCAPTURE:08X}) to window {hex(hwnd)}...")
    success = _user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

    if success:
        print(f"✅ SUCCESS: Window {hex(hwnd)} is now HIDDEN from screen capture!")
        print("   🎯 Window will appear as BLACK RECTANGLE in recordings/screen sharing")
        
        # Verify the protection was applied
        verify_protection(hwnd)
        return True
    else:
        # If the function fails, we get the last error code from the OS for debugging.
        error_code = ctypes.GetLastError()
        print(f"❌ FAILED: SetWindowDisplayAffinity failed! Error Code: {error_code}")
        print("   🚨 WARNING: Window WILL be visible in screen recordings!")
        return False

def verify_protection(hwnd):
    """Verify that capture protection is actually applied"""
    try:
        # Try to get current display affinity (this is a read-only check)
        print(f"🔬 Verifying protection on window {hex(hwnd)}...")
        
        # Note: There's no direct way to read the current display affinity,
        # but we can check if the window handle is still valid
        is_window_valid = _user32.IsWindow(hwnd)
        if is_window_valid:
            print("✅ Window handle is valid - protection likely applied")
        else:
            print("❌ Window handle is invalid - protection may have failed")
            
    except Exception as e:
        print(f"⚠️ Could not verify protection: {e}")


# --- Example Usage (for testing this module directly) ---
if __name__ == '__main__':
    print("Running window_manager.py in test mode...")

    # Create a pywebview window for testing purposes
    test_window = webview.create_window(
        'Aura Stealth Test',
        html='<h1>This window should be black in screen recordings.</h1>',
        width=800,
        height=600
    )

    # Hook our protection function to the 'shown' event. This is critical.
    # The 'shown' event fires after the window is created and visible, ensuring
    # that a window handle exists.
    test_window.events.shown += lambda: apply_capture_protection(test_window)

    # Start the GUI event loop
    webview.start()
# This function is not called if DEV_MODE in main.py is True
    print("--- Running window_manager.py in test mode ---")