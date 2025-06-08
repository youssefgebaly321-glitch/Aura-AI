from fastapi import APIRouter, HTTPException
from core.config import settings
from pydantic import BaseModel
import window_manager

router = APIRouter()

class TransparencyRequest(BaseModel):
    transparency: float  # 0.0 to 1.0

class TransparencyPercentRequest(BaseModel):
    percent: int  # 0 to 100

@router.get("/api/config")
async def get_config():
    """
    Returns frontend configuration values including DEV_MODE.
    This allows JavaScript to access centralized config values.
    """
    return {
        "DEV_MODE": settings.DEV_MODE,
        "LOG_LEVEL": settings.LOG_LEVEL,
        "CAPTURE_PROTECTION_ENABLED": not settings.DEV_MODE
    }

@router.get("/api/transparency")
async def get_transparency():
    """Get current window transparency information"""
    return window_manager.get_transparency_info()

@router.post("/api/transparency")
async def set_transparency(request: TransparencyRequest):
    """Set window transparency (0.0 = transparent, 1.0 = opaque)"""
    success = window_manager.set_app_transparency(request.transparency)
    if success:
        return {
            "success": True,
            "transparency": request.transparency,
            "message": f"Transparency set to {request.transparency*100:.0f}%"
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to set transparency")

@router.post("/api/transparency/percent")
async def set_transparency_percent(request: TransparencyPercentRequest):
    """Set window transparency as percentage (0 = transparent, 100 = opaque)"""
    success = window_manager.set_app_transparency_percent(request.percent)
    if success:
        return {
            "success": True,
            "percent": request.percent,
            "transparency": request.percent / 100.0,
            "message": f"Transparency set to {request.percent}%"
        }
    else:
        raise HTTPException(status_code=400, detail="Failed to set transparency")

@router.post("/api/transparency/presets/transparent")
async def make_transparent():
    """Make window 60% transparent (40% opacity) - good for interviews"""
    success = window_manager.make_app_transparent()
    if success:
        return {"success": True, "message": "Window set to interview mode (40% opacity)"}
    else:
        raise HTTPException(status_code=400, detail="Failed to set transparency")

@router.post("/api/transparency/presets/semi-transparent")
async def make_semi_transparent():
    """Make window semi-transparent (70% opacity)"""
    success = window_manager.make_app_semi_transparent()
    if success:
        return {"success": True, "message": "Window set to semi-transparent (70% opacity)"}
    else:
        raise HTTPException(status_code=400, detail="Failed to set transparency")

@router.post("/api/transparency/presets/opaque")
async def make_opaque():
    """Make window fully opaque (100% opacity)"""
    success = window_manager.make_app_opaque()
    if success:
        return {"success": True, "message": "Window set to opaque (100% opacity)"}
    else:
        raise HTTPException(status_code=400, detail="Failed to set transparency")

@router.post("/api/window/always-on-top")
async def set_always_on_top(request: dict):
    """Set window to always stay on top"""
    on_top = request.get("on_top", True)
    success = window_manager.set_app_always_on_top(on_top)
    if success:
        status = "enabled" if on_top else "disabled"
        return {"success": True, "message": f"Always on top {status}"}
    else:
        raise HTTPException(status_code=400, detail="Failed to set always on top")

@router.post("/api/interview/start")
async def start_interview_mode():
    """Enable transparency for live interview"""
    success = window_manager.set_app_transparency(0.6)  # 60% opacity for interviews
    if success:
        return {"success": True, "message": "Interview mode enabled - window is now transparent"}
    else:
        raise HTTPException(status_code=400, detail="Failed to enable interview transparency")

@router.post("/api/interview/end")
async def end_interview_mode():
    """Disable transparency when leaving live interview"""
    success = window_manager.set_app_transparency(1.0)  # 100% opacity for other views
    if success:
        return {"success": True, "message": "Interview mode disabled - window is now opaque"}
    else:
        raise HTTPException(status_code=400, detail="Failed to disable interview transparency") 