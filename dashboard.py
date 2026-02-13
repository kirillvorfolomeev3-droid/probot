import json, os, httpx, secrets, datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-akemi")
templates = Jinja2Templates(directory="templates")

SETTINGS_FILE = "settings.json"
LOGS_FILE = "audit_logs.json"

def load_data(file):
    if not os.path.exists(file):
        with open(file, "w", encoding="utf-8") as f: json.dump([] if "logs" in file else {}, f)
    with open(file, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return [] if "logs" in file else {}

def save_data(file, data):
    with open(file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def add_audit_log(user, action):
    logs = load_data(LOGS_FILE)
    logs.append({"user": user, "action": action, "time": datetime.datetime.now().strftime("%d.%m %H:%M")})
    save_data(LOGS_FILE, logs[-20:]) # Храним только последние 20 записей

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = request.session.get("user_info")
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "page": "home", "logs": load_data(LOGS_FILE)})

@app.get("/{page}", response_class=HTMLResponse)
async def pages(request: Request, page: str):
    user = request.session.get("user_info")
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "page": page, "logs": load_data(LOGS_FILE)})

@app.post("/update")
async def update(request: Request, guild_id: str = Form(...)):
    user = request.session.get("user_info")
    form = await request.form()
    data = load_data(SETTINGS_FILE)
    g = data.setdefault(guild_id, {})

    # Сохраняем все поля из формы
    for key in form.keys():
        if key != "guild_id":
            g[key] = form[key]
    
    save_data(SETTINGS_FILE, data)
    add_audit_log(user['username'], f"Изменил настройки сервера {guild_id}")
    return RedirectResponse(url=request.headers.get("referer", "/"), status_code=303)

# Код для Логина/Коллбэка оставь из прошлого сообщения без изменений