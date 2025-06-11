import webview
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from threading import Thread
import asyncio
import aiofiles
import window_manager  # Our new module for capture protection
import os
import orjson
import tempfile
import time
from pathlib import Path
from api import websocket, config_api
from core.config import settings, print_config_debug

# --- Development Flag (now from .env) ---
# DEV_MODE is now controlled via .env file - see core/config.py
DEV_MODE = settings.DEV_MODE

# Print configuration debug info at startup
print_config_debug()

# --- Global Command Monitor ---
class GlobalCommandMonitor:
    """Monitors the temp command file for global hotkey commands"""
    
    def __init__(self):
        self.command_file = os.path.join(tempfile.gettempdir(), "aura_command.json")
        self.last_command_time = 0
        self.running = False
        self.websocket_manager = None
        self.startup_time = time.time()
        self.startup_delay = 5  # Ignore commands for first 5 seconds after startup
        self.last_processed_command = None
        self.command_cooldown = 0.5  # 500ms cooldown between same commands
        
    def set_websocket_manager(self, ws_manager):
        """Set the websocket manager for sending commands"""
        self.websocket_manager = ws_manager
        
    def start_monitoring(self):
        """Start the command monitoring thread"""
        # Clean up any old command files
        try:
            if os.path.exists(self.command_file):
                os.remove(self.command_file)
                print("🧹 Cleared old global command file")
        except Exception as e:
            print(f"⚠️ Could not clear old command file: {e}")
        
        self.running = True
        monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        print("🎮 Global command monitor started")
        
    def stop_monitoring(self):
        """Stop the command monitoring"""
        self.running = False
        
    def _monitor_loop(self):
        """Main monitoring loop that checks for commands - now runs async event loop"""
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            loop.run_until_complete(self._async_monitor_loop())
        finally:
            loop.close()
    
    async def _async_monitor_loop(self):
        """Async monitoring loop that checks for commands with improved performance"""
        while self.running:
            try:
                if os.path.exists(self.command_file):
                    # Check file modification time
                    file_mtime = os.path.getmtime(self.command_file)
                    
                    if file_mtime > self.last_command_time:
                        self.last_command_time = file_mtime
                        
                        # Read and process the command using async file I/O
                        try:
                            async with aiofiles.open(self.command_file, 'rb') as f:
                                file_content = await f.read()
                                command_data = orjson.loads(file_content)
                            
                            # Process the command
                            if self._process_command(command_data):
                                # Clean up the command file after successful processing
                                try:
                                    os.remove(self.command_file)
                                    print(f"🧹 Cleaned up command file after processing")
                                except Exception as cleanup_error:
                                    # Don't fail if cleanup fails
                                    pass
                            
                        except (orjson.JSONDecodeError, IOError) as e:
                            # Ignore file read errors (file might be being written)
                            pass
                            
                await asyncio.sleep(0.2)  # Check every 200ms (reduced frequency)
                
            except Exception as e:
                print(f"❌ Error in command monitor: {e}")
                await asyncio.sleep(1)  # Wait longer on error
                
    def _process_command(self, command_data):
        """Process a command from the global hotkey"""
        command = command_data.get('command', '')
        source = command_data.get('source', '')
        timestamp_str = command_data.get('timestamp', '')
        
        if source != 'global_hotkey':
            return False  # Only process global hotkey commands
        
        # Ignore commands during startup to prevent processing old/accidental commands
        if time.time() - self.startup_time < self.startup_delay:
            print(f"🎮 Ignoring global command during startup: {command}")
            return False
        
        # Create a unique command identifier for deduplication
        command_id = f"{command}_{command_data.get('level', '')}_{command_data.get('preset_key', '')}"
        current_time = time.time()
        
        # Check for duplicate commands within cooldown period
        if (self.last_processed_command and 
            self.last_processed_command['id'] == command_id and 
            current_time - self.last_processed_command['time'] < self.command_cooldown):
            print(f"🎮 Ignoring duplicate command within cooldown: {command}")
            return False
        
        # Update last processed command
        self.last_processed_command = {
            'id': command_id,
            'time': current_time,
            'command': command
        }
            
        print(f"🎮 Processing global command: {command}")
        
        # Execute the command by sending it to the browser
        try:
            if command == 'toggle_vision_mode':
                self._execute_browser_command('if (window.toggleVisionMode) { window.toggleVisionMode(); } else { console.warn("toggleVisionMode not available"); }')
            elif command == 'capture_screenshot':
                self._execute_browser_command('if (window.captureScreenshot) { window.captureScreenshot(); } else { console.warn("captureScreenshot not available"); }')
            elif command == 'process_screenshots':
                self._execute_browser_command('if (window.processScreenshots) { window.processScreenshots(); } else { console.warn("processScreenshots not available"); }')
            elif command == 'reset_screenshot_queue':
                self._execute_browser_command('if (window.resetScreenshotQueue) { window.resetScreenshotQueue(); } else { console.warn("resetScreenshotQueue not available"); }')
            elif command == 'switch_preset':
                preset_key = command_data.get('preset_key', 'primary')
                self._execute_browser_command(f'if (window.switchPreset) {{ window.switchPreset("{preset_key}"); }} else {{ console.warn("switchPreset not available"); }}')
            elif command == 'set_transparency':
                transparency_level = command_data.get('level', 'opaque')
                self._execute_browser_command(f'if (window.setTransparency) {{ window.setTransparency("{transparency_level}"); }} else {{ console.warn("setTransparency not available"); }}')
            elif command == 'toggle_mic_mute':
                self._execute_browser_command('if (window.toggleMicMute) { window.toggleMicMute(); } else { console.warn("toggleMicMute not available"); }')
            elif command == 'toggle_universal_mute':
                self._execute_browser_command('if (window.toggleUniversalMute) { window.toggleUniversalMute(); } else { console.warn("toggleUniversalMute not available"); }')
            elif command == 'switch_vision_model':
                self._execute_browser_command('if (window.switchVisionModel) { window.switchVisionModel(); } else { console.warn("switchVisionModel not available"); }')
            elif command == 'context_aware_action':
                action = command_data.get('action', '')
                if action == 'auto_select_preset':
                    # Auto-select AI preset
                    self._execute_browser_command('if (window.switchPreset) { window.switchPreset("auto"); } else { console.warn("switchPreset not available"); }')
                else:
                    print(f"⚠️ Unknown context-aware action: {action}")
                    return False
            else:
                print(f"⚠️ Unknown global command: {command}")
                return False
                
            return True  # Command processed successfully
            
        except Exception as e:
            print(f"❌ Error executing global command: {e}")
            return False
            
    def _execute_browser_command(self, js_code):
        """Execute JavaScript code in the browser"""
        try:
            # Use webview's evaluate_js to run the command
            if hasattr(webview, 'windows') and webview.windows:
                window = webview.windows[0]  # Get the first (main) window
                
                # Add a small delay to ensure the page is loaded
                time.sleep(0.1)
                
                # Try to execute with error handling
                try:
                    result = window.evaluate_js(js_code)
                    print(f"✅ Executed global command in browser: {js_code.split('&&')[0]}...")
                except Exception as js_error:
                    # If direct execution fails, try wrapping in setTimeout
                    wrapped_code = f"setTimeout(() => {{ try {{ {js_code} }} catch(e) {{ console.warn('Global command error:', e); }} }}, 100);"
                    window.evaluate_js(wrapped_code)
                    print(f"✅ Executed global command in browser (delayed): {js_code.split('&&')[0]}...")
            else:
                print("⚠️ No webview window available for command execution")
        except Exception as e:
            print(f"❌ Failed to execute browser command: {e}")

# Create global command monitor instance
command_monitor = GlobalCommandMonitor()


# --- FastAPI App Setup ---
app = FastAPI()
app.include_router(websocket.router)
app.include_router(config_api.router)

# Mount the 'web' directory to serve static files (CSS, JS)
# This makes files in 'web/css' and 'web/js' available under '/static/css' and '/static/js'
app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/")
async def read_index(request: Request):
    """Serves the main index.html file."""
    return FileResponse(os.path.join('web', 'index.html'))


# --- Server and Window Management ---
def run_server():
    """Runs the Uvicorn server in a separate thread."""
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="warning")

if __name__ == '__main__':
    # 3. Run the server in a separate thread
    server_thread = Thread(target=run_server)
    server_thread.daemon = True  # Allows main thread to exit even if server is running
    server_thread.start()

    # 4. Create the pywebview window, loading the FastAPI server
    window = webview.create_window(
        'Aura',
        'http://127.0.0.1:8002',
        width=1000,
        height=750,
        resizable=True
    )

    # 5. Apply capture protection and transparency (or skip in DEV_MODE)
    def on_window_shown():
        print(f"🔧 Window shown event fired. DEV_MODE = {DEV_MODE}")
        
        if not DEV_MODE:
            print("🛡️ DEV_MODE is False - Applying screen capture protection...")
            protection_success = window_manager.apply_capture_protection(window)
            if protection_success:
                print("✅ Screen capture protection successfully applied!")
            else:
                print("❌ CRITICAL: Screen capture protection FAILED!")
                print("   🚨 WARNING: Window will be visible in screen recordings!")
        else:
            print("ℹ️ DEV_MODE is True. Skipping screen capture protection.")
            print("   📋 Note: Window WILL be visible in screen recordings during development")
        
        # Set up window transparency and always-on-top
        import time
        time.sleep(1.0)  # Give window more time to fully initialize
        
        # Find window and configure always-on-top (but NOT transparency yet)
        if window_manager.find_aura_window():
            print("🔍 Window found - setting up always-on-top only")
            
            # Wait a bit more before setting always-on-top
            time.sleep(0.5)
            
            # Set window to always stay on top with retries
            always_on_top_success = False
            for attempt in range(3):
                always_on_top_success = window_manager.set_app_always_on_top(True)
                if always_on_top_success:
                    print("📌 Window set to always stay on top")
                    break
                else:
                    print(f"⚠️ Always-on-top attempt {attempt + 1} failed, retrying...")
                    time.sleep(0.3)
            
            if not always_on_top_success:
                print("⚠️ Failed to set always on top after 3 attempts")
                
            print("ℹ️ Transparency will be applied only during live interview")
        else:
            print("⚠️ Could not find Aura window for window management")
        
        # Start the global hotkey listener
        window_manager.window_manager.start_hotkey_listener()
        
        # Start the global command monitor
        command_monitor.start_monitoring()
    
    window.events.shown += on_window_shown

    # 6. Start the pywebview event loop with debug based on DEV_MODE
    webview.start(debug=DEV_MODE)