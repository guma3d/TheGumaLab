import os
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, Form, Response, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from dotenv import load_dotenv

import webauthn_router

load_dotenv()

app = FastAPI(title="GumaLab Auth Gateway")
app.include_router(webauthn_router.router)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_change_me")
ALGORITHM = "HS256"
COOKIE_NAME = "guma_sso_token"
DOMAIN = ".guma3d.com" # applies to home., photo., serverstatus. ...
# Fallback to local cookie domain if running directly on localhost for testing
if os.getenv("ENV") == "dev":
    DOMAIN = None

CORRECT_HTTP_PASSWORD = os.getenv("GUMA_AUTH_PASSWORD", "iloveguma")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/sw.js")
async def serve_sw():
    return FileResponse("static/sw.js")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse("static/manifest.json")

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request):
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return username
    except JWTError:
        return None

# Nginx auth_request endpoint
@app.get("/auth")
async def check_auth(request: Request):
    # Nginx will call this. Returns 200 OK if authenticated, 401 otherwise.
    username = get_current_user(request)
    if username is None:
        return Response(status_code=401)
    return Response(status_code=200)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, redirect_url: str = "/"):
    username = get_current_user(request)
    if username:
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("login.html", {"request": request, "redirect_url": redirect_url, "error": None})

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request, password: str = Form(...), redirect_url: str = Form("/")) :
    if password == CORRECT_HTTP_PASSWORD:
        # Create token
        token_expires = timedelta(days=365)
        token = create_access_token(data={"sub": "guma_admin"}, expires_delta=token_expires)
        
        # We redirect them back to the original app or main dashboard
        # But wait, redirect_url comes from Nginx which might send us the original URL via X-Original-URI
        response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
        
        # Set the SSO cookie with proper domain
        response.set_cookie(
            key=COOKIE_NAME,
            value=token,
            max_age=31536000,   # 1 year in seconds
            expires=31536000,
            path="/",
            domain=DOMAIN,
            httponly=True,
            secure=True,        # Requires HTTPS
            samesite="lax"
        )
        return response
    else:
        # Incorrect password
        return templates.TemplateResponse("login.html", {"request": request, "redirect_url": redirect_url, "error": "Invalid password"})

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    # The home dashboard is also protected
    username = get_current_user(request)
    if username is None:
        return RedirectResponse(url="/login?redirect_url=/", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=COOKIE_NAME, domain=DOMAIN, path="/")
    return response

# Fallback redirects for aggressively cached mobile browsers hitting old paths
@app.get("/ServerStatus/")
async def fallback_status():
    return RedirectResponse(url="https://gumaserverstatus.guma3d.com/", status_code=301)

@app.get("/StockMaster_01/")
async def fallback_stock():
    return RedirectResponse(url="https://gumastockreport.guma3d.com/", status_code=301)

@app.get("/YoutubeToDoc/")
async def fallback_youtube():
    return RedirectResponse(url="https://gumatube.guma3d.com/", status_code=301)

@app.get("/GumaTutorDoc/")
async def fallback_tutordoc():
    return RedirectResponse(url="https://gumatutordoc.guma3d.com/", status_code=301)

@app.get("/GumaKidsPython/")
async def fallback_kidspython():
    return RedirectResponse(url="https://gumakidspython.guma3d.com/", status_code=301)

@app.get("/ImageAnalyzer/")
async def fallback_image():
    return RedirectResponse(url="https://gumaimageanalyzer.guma3d.com/", status_code=301)
