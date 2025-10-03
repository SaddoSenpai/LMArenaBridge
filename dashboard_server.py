"""
LMArena Bridge Dashboard Server
Provides web interface for token management and usage statistics
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException, Depends, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from database import DashboardDatabase

# Load environment variables
load_dotenv()

app = FastAPI(title="LMArena Bridge Dashboard")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Database
db = DashboardDatabase(os.getenv("DB_FILE", "dashboard_data.json"))

# Session storage (in-memory for simplicity)
sessions = {}

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "change_this_secure_password")
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))

def create_session(username: str) -> str:
    """Create a new session"""
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "username": username,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    return session_id

def validate_session(session_id: Optional[str]) -> bool:
    """Validate session"""
    if not session_id or session_id not in sessions:
        return False
    
    session = sessions[session_id]
    if datetime.now() > session["expires_at"]:
        del sessions[session_id]
        return False
    
    return True

def get_current_user(session_id: Optional[str] = Cookie(None)):
    """Dependency to get current user"""
    if not validate_session(session_id):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return sessions[session_id]["username"]

@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page - public view"""
    stats = db.get_global_stats()
    recent_usage = db.get_recent_usage(limit=10)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "recent_usage": recent_usage
    })

@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """Admin login page"""
    return templates.TemplateResponse("admin_login.html", {
        "request": request
    })

@app.post("/admin/login")
async def admin_login(
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle admin login"""
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session_id = create_session(username)
        response = RedirectResponse(url="/admin", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=86400,
            samesite="lax"
        )
        return response
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/admin/logout")
async def admin_logout(session_id: Optional[str] = Cookie(None)):
    """Handle admin logout"""
    if session_id and session_id in sessions:
        del sessions[session_id]
    
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie("session_id")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(
    request: Request,
    username: str = Depends(get_current_user)
):
    """Admin panel - token management"""
    tokens = db.get_all_tokens()
    stats = db.get_global_stats()
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "tokens": tokens,
        "stats": stats,
        "username": username
    })

@app.post("/admin/token/create")
async def create_token(
    user_name: str = Form(""),
    user_email: str = Form(""),
    username: str = Depends(get_current_user)
):
    """Create a new token"""
    user_info = {}
    if user_name:
        user_info["name"] = user_name
    if user_email:
        user_info["email"] = user_email
    
    token = db.generate_token(user_info)
    return JSONResponse({"success": True, "token": token})

@app.post("/admin/token/{token_id}/revoke")
async def revoke_token(
    token_id: str,
    username: str = Depends(get_current_user)
):
    """Revoke a token"""
    success = db.revoke_token(token_id)
    return JSONResponse({"success": success})

@app.post("/admin/token/{token_id}/activate")
async def activate_token(
    token_id: str,
    username: str = Depends(get_current_user)
):
    """Activate a token"""
    success = db.activate_token(token_id)
    return JSONResponse({"success": success})

@app.post("/admin/token/{token_id}/delete")
async def delete_token(
    token_id: str,
    username: str = Depends(get_current_user)
):
    """Delete a token"""
    success = db.delete_token(token_id)
    return JSONResponse({"success": success})

@app.get("/api/stats")
async def get_stats():
    """Get global statistics"""
    return db.get_global_stats()

@app.get("/api/token/{token}/info")
async def get_token_info(token: str):
    """Get token information (public endpoint for users to check their token)"""
    token_info = db.get_token_info(token)
    
    if not token_info:
        raise HTTPException(status_code=404, detail="Token not found")
    
    # Return sanitized info (without the actual key)
    return {
        "created_at": token_info["created_at"],
        "last_used": token_info["last_used"],
        "is_active": token_info["is_active"],
        "usage_stats": token_info["usage_stats"]
    }

@app.get("/api/usage/timeline")
async def get_usage_timeline(days: int = 7, token: Optional[str] = None):
    """Get usage timeline for charts"""
    token_id = None
    if token:
        import hashlib
        token_id = hashlib.sha256(token.encode()).hexdigest()[:16]
    
    timeline = db.get_usage_timeline(token_id, days)
    return timeline

@app.get("/api/admin/tokens")
async def get_all_tokens_api(username: str = Depends(get_current_user)):
    """Get all tokens (admin only)"""
    return db.get_all_tokens()

@app.get("/api/admin/recent-usage")
async def get_recent_usage_api(
    limit: int = 100,
    username: str = Depends(get_current_user)
):
    """Get recent usage logs (admin only)"""
    return db.get_recent_usage(limit)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_tokens": db.get_active_token_count()}

if __name__ == "__main__":
    port = int(os.getenv("DASHBOARD_PORT", 5103))
    print(f"Starting LMArena Bridge Dashboard on http://127.0.0.1:{port}")
    print(f"Admin panel: http://127.0.0.1:{port}/admin")
    print(f"Admin username: {ADMIN_USERNAME}")
    uvicorn.run(app, host="0.0.0.0", port=port)
