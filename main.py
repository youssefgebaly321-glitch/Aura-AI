import webview
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from threading import Thread
import window_manager  # Our new module for capture protection
import os
from api import websocket, config_api
from core.config import settings, print_config_debug

# --- Development Flag (now from .env) ---
# DEV_MODE is now controlled via .env file - see core/config.py
DEV_MODE = settings.DEV_MODE

# Print configuration debug info at startup
print_config_debug()


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
    
    window.events.shown += on_window_shown

    # 6. Start the pywebview event loop with debug based on DEV_MODE
    webview.start(debug=DEV_MODE)