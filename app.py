from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import json
import os
import random
import requests
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "mconstruction_crm_secret_2026"

DB_FILE = "crm_db.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

MOBIZON_API_KEY = os.environ.get("MOBIZON_API_KEY", "YOUR_MOBIZON_API_KEY")
ROP_PHONE = "+77764777278"

DEFAULT_USERS = {
    "director": {"pass": "dir123", "name": "Уралбаев Жанайдар Абишевич", "role": "director", "position": "Генеральный директор", "phone": "+7 771 054 77 66", "whatsapp": "+7 771 054 77 66", "email": "too.mamyr@mail.ru", "avatar": ""},
    "rop": {"pass": "rop123", "name": "Лемперт Александр Сергеевич", "role": "rop", "position": "Руководитель отдела продаж", "phone": "+7 776 477 72 78", "whatsapp": "+7 776 477 72 78", "email": "too.mamyr@mail.ru", "avatar": ""},
    "manager1": {"pass": "man123", "name": "Менеджер 1", "role": "manager", "position": "Менеджер по продажам", "phone": "+7 700 111 11 11", "whatsapp": "+7 700 111 11 11", "email": "", "avatar": ""},
    "manager2": {"pass": "man223", "name": "Менеджер 2", "role": "manager", "position": "Менеджер по продажам", "phone": "+7 700 222 22 22", "whatsapp": "+7 700 222 22 22", "email": "", "avatar": ""},
    "manager3": {"pass": "man323", "name": "Менеджер 3", "role": "manager", "position": "Менеджер по продажам", "phone": "+7 700 333 33 33", "whatsapp": "+7 700 333 33 33", "email": "", "avatar": ""}
}

STAGES = [
    ("stage_1", "1. Новый клиент", "#6c757d"),
    ("stage_2", "2. Не дозвон", "#ffc107"),
    ("stage_3", "3. Нужно выйти на ЛПР", "#212529"),
    ("stage_4", "4. Скинул презентацию / инфу", "#0dcaf0"),
    ("stage_5", "5. Скинул КП", "#198754"),
    ("stage_6", "6. Нет обратной связи", "#fd7e14"),
    ("stage_7", "7. Веду переговоры", "#0d6efd"),
    ("stage_8", "8. Отложил / Передумал", "#dc3545"),
    ("stage_9", "9. Купил у конкурентов", "#6c2323"),
    ("stage_10", "10. Готов контрактоваться", "#157347"),
    ("stage_11", "11. Сделали договор", "#0f5132"),
    ("stage_12", "12. Внес предоплату", "#6f42c1"),
    ("stage_13", "13. Выполнен (Дебиторка)", "#0d6efd"),
    ("stage_14", "14. Оплачен полностью", "#198754"),
    ("stage_15", "15. Повторный заказ (VIP)", "#8540f5")
]

STAGES_DICT = {sk: sn for sk, sn, sc in STAGES}
CONTRACT_STAGES = ["stage_11", "stage_12", "stage_13", "stage_14", "stage_15"]
LOST_STAGES = ["stage_8", "stage_9"]

def load_db():
    default_data = {"deals": [], "tz_list": [], "users": DEFAULT_USERS, "chats": [], "kp_registry": [], "pending_codes": {}}
    if not os.path.exists(DB_FILE):
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "deals" not in data:
                save_db(default_data)
                return default_data
            if "users" not in data: data["users"] = DEFAULT_USERS
            if "tz_list" not in data: data["tz_list"] = []
            if "chats" not in data: data["chats"] = []
            if "kp_registry" not in data: data["kp_registry"] = []
            if "pending_codes" not in data: data["pending_codes"] = {}
            return data
    except:
        save_db(default_data)
        return default_data

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def send_sms_code(code, req_phone):
    text = f"M-CONSTRUCTION: Запрос доступа от {req_phone}. Код: {code}"
    print(f"\n[SMS SECURITY VERIFICATION] {text}\n", flush=True)
    if MOBIZON_API_KEY == "YOUR_MOBIZON_API_KEY" or not MOBIZON_API_KEY:
        return True
    try:
        url = "https://api.mobizon.kz/service/message/sendSmsMessage"
        params = {"recipient": ROP_PHONE.replace("+", ""), "text": text, "apiKey": MOBIZON_API_KEY}
        res = requests.get(url, params=params, timeout=5)
        return res.status_code == 200
    except Exception as e:
        print(f"[MOBIZON ERROR] {e}", flush=True)
        return False

REQUEST_ACCESS_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Запрос доступа - M-CONSTRUCTION CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark d-flex align-items-center justify-content-center vh-100 p-3">
<div class="card p-4 shadow border-0 bg-white" style="width: 100%; max-width: 380px;">
    <h3 class="mb-1 text-center fw-bold" style="color: #b8860b;">M-CONSTRUCTION</h3>
    <div class="text-center text-muted small mb-3">Защищенная корпоративная CRM</div>
    {% if error %}<div class="alert alert-danger py-2 small">{{ error }}</div>{% endif %}
    {% if success %}<div class="alert alert-success py-2 small">{{ success }}</div>{% endif %}
    {% if step == 'phone' %}
    <form method="POST" action="/request_access">
        <div class="mb-3"><label class="form-label fw-bold">Введите ваш телефон:</label><input type="text" name="phone" class="form-control" placeholder="+7 700 000 00 00" required autofocus></div>
        <button type="submit" class="btn text-white w-100 fw-bold" style="background: #b8860b;">Запросить доступ (SMS)</button>
    </form>
    {% elif step == 'code' %}
    <form method="POST" action="/verify_code">
        <input type="hidden" name="phone" value="{{ phone }}">
        <div class="mb-3"><label class="form-label fw-bold">Код подтверждения:</label><input type="text" name="code" class="form-control text-center fw-bold fs-4" placeholder="0000" maxlength="4" required autofocus></div>
        <button type="submit" class="btn btn-success w-100 fw-bold">Подтвердить код</button>
    </form>
    {% endif %}
</div>
</body>
</html>
"""

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Вход в M-CONSTRUCTION CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark d-flex align-items-center justify-content-center vh-100 p-3">
<form method="POST" action="/login" class="card p-4 shadow border-0 bg-white" style="width: 100%; max-width: 340px;">
    <h3 class="mb-1 text-center fw-bold" style="color: #b8860b;">M-CONSTRUCTION</h3>
    <div class="text-center text-muted small mb-3">Авторизация сотрудника</div>
    {% if error %}<div class="alert alert-danger py-1 small">{{ error }}</div>{% endif %}
    <div class="mb-3"><label class="form-label">Логин:</label><input type="text" name="username" class="form-control" required autofocus></div>
    <div class="mb-3"><label class="form-label">Пароль:</label><input type="password" name="password" class="form-control" required></div>
    <button type="submit" class="btn text-white w-100 fw-bold" style="background: #b8860b;">Войти в систему</button>
</form>
</body>
</html>
"""

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ page_title }} - M-CONSTRUCTION CRM</title>
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1a365d">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="Мамыр CRM">

    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; font-family: Arial, sans-serif; overflow: hidden; height: 100vh; margin: 0; }
        .wrapper { display: flex; width: 100%; height: 100vh; overflow: hidden; }
        
        .sidebar { width: 55px; background: #1a1e21; color: #fff; display: flex; flex-direction: column; flex-shrink: 0; transition: width 0.25s ease-in-out; overflow: hidden; white-space: nowrap; z-index: 1000; border-right: 2px solid #b8860b; }
        .sidebar:hover, .sidebar:focus-within { width: 220px; }
        .sidebar .brand { padding: 12px; font-size: 14px; font-weight: bold; background: #111; border-bottom: 1px solid #373b3e; text-align: left; color: #b8860b; display: flex; align-items: center; gap: 10px; }
        .sidebar .brand img { width: 32px; height: 32px; object-fit: contain; }
        .sidebar .menu { padding: 15px 5px; display: flex; flex-direction: column; gap: 8px; flex-grow: 1; overflow-y: auto; }
        .sidebar .menu a { color: #adb5bd; text-decoration: none; padding: 10px 12px; border-radius: 4px; font-size: 13px; display: flex; align-items: center; gap: 12px; transition: 0.2s; position: relative; }
        .sidebar .menu a:hover, .sidebar .menu a.active { background: #b8860b; color: #fff; }
        .sidebar .menu a span.icon-sym { font-size: 16px; min-width: 24px; text-align: center; display: inline-block; }
        .nav-badge { background: #e53e3e; color: #fff; font-size: 10px; font-weight: bold; padding: 2px 6px; border-radius: 10px; line-height: 1; margin-left: auto; }
        
        .main-content { flex-grow: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        .top-bar { background: #ffffff; border-bottom: 1px solid #dee2e6; padding: 8px 15px; display: flex; justify-content: space-between; align-items: center; min-height: 60px; flex-shrink: 0; flex-wrap: wrap; gap: 10px; }
        .content-body { flex-grow: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 12px; background: #f8f9fa; }
        
        .kanban-outer { flex-grow: 1; overflow-x: auto; overflow-y: hidden; white-space: nowrap; padding-bottom: 10px; }
        .kanban { display: inline-flex; gap: 12px; height: 100%; align-items: flex-start; }
        .kanban-outer::-webkit-scrollbar { height: 10px; }
        .kanban-outer::-webkit-scrollbar-track { background: #dee2e6; border-radius: 6px; }
        .kanban-outer::-webkit-scrollbar-thumb { background: #b8860b; border-radius: 6px; }

        .k-col { width: 280px; min-width: 280px; max-width: 280px; background: #e9ecef; border-radius: 6px; display: flex; flex-direction: column; max-height: 100%; white-space: normal; }
        .k-header { padding: 10px; font-weight: bold; font-size: 13px; color: white; border-top-left-radius: 6px; border-top-right-radius: 6px; text-align: center; flex-shrink: 0; }
        .k-body { padding: 8px; overflow-y: auto; flex-grow: 1; min-height: 150px; }
        
        .deal-card { background: #ffffff; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 12px; border: 1px solid #ced4da; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab; transition: 0.15s; }
        .deal-card:hover { border-color: #b8860b; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
        .history-box { background: #f1f3f5; border-radius: 4px; padding: 8px; max-height: 130px; overflow-y: auto; font-size: 11px; }
        .drag-over { background-color: #fdf3d0 !important; border: 2px dashed #b8860b; }
        .blink-remind { animation: blinker 1.2s linear infinite; }
        @keyframes blinker { 50% { opacity: 0.3; } }

        @media (max-width: 768px) {
            .sidebar { width: 55px; }
            .sidebar:hover, .sidebar:focus-within { width: 220px; }
            .top-bar h5 { font-size: 13px !important; }
            .top-bar { padding: 8px 10px; height: auto; }
        }
    </style>
</head>
<body>

<div class="wrapper">
    <div class="sidebar">
        <div class="brand">
            <img src="{{ url_for('uploaded_file', filename='1000100784.jpg') }}" onerror="this.style.display='none'">
            <span><b>M-CONSTRUCTION</b></span>
        </div>
        <div class="menu">
            <a href="/" class="{% if active_page == 'kanban' %}active{% endif %}"><span class="icon-sym">&#128202;</span> <span>Канбан CRM</span></a>
            <a href="/tz" class="{% if active_page == 'tz' %}active{% endif %}"><span class="icon-sym">&#128221;</span> <span>Тех. задания</span><span class="nav-badge" id="tzBadge" {% if unread_tz_count == 0 %}style="display:none;"{% endif %}>{{ unread_tz_count }}</span></a>
            <a href="/generator" class="{% if active_page == 'generator' %}active{% endif %}"><span class="icon-sym">&#128196;</span> <span>Генератор КП</span></a>
            {% if current_user_data.role in ['director', 'rop'] %}
            <a href="/registry" class="{% if active_page == 'registry' %}active{% endif %}"><span class="icon-sym">&#128198;</span> <span>Реестр КП</span></a>
            <a href="/analytics" class="{% if active_page == 'analytics' %}active{% endif %}"><span class="icon-sym">&#128200;</span> <span>Воронка (Отчеты)</span></a>
            {% endif %}
            <a href="/chat" class="{% if active_page == 'chat' %}active{% endif %}"><span class="icon-sym">&#128172;</span> <span>Чат сотрудников</span><span class="nav-badge" id="chatBadge" {% if unread_msgs_count == 0 %}style="display:none;"{% endif %}>{{ unread_msgs_count }}</span></a>
        </div>
        
        <div class="p-2 bg-dark border-top border-secondary text-muted small flex-shrink-0">
            <a href="/profile" class="text-white text-decoration-none d-flex align-items-center gap-2 p-2 rounded {% if active_page == 'profile' %}bg-warning text-dark fw-bold{% endif %}">
                {% if current_user_data.get('avatar') %}
                <img src="{{ url_for('uploaded_file', filename=current_user_data['avatar']) }}" style="width:28px; height:28px; border-radius:50%; object-fit:cover;">
                {% else %}
                <span class="icon-sym">&#128100;</span>
                {% endif %}
                <span class="text-truncate"><b>{{ current_user_data.name }}</b></span>
            </a>
            <a href="/logout" class="text-danger text-decoration-none d-flex align-items-center gap-2 p-2 mt-1">
                <span class="icon-sym">&#128682;</span> <span>Выйти</span>
            </a>
        </div>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <div class="d-flex align-items-center gap-2 flex-wrap">
                {% if active_page == 'kanban' %}
                <h5 class="m-0 fw-bold text-secondary">📊 Канбан CRM</h5>
                <button class="btn btn-success btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить сделку</button>
                {% elif active_page == 'tz' %}
                <h5 class="m-0 fw-bold text-secondary">📋 Технические задания</h5>
                <button class="btn btn-primary btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addTzModal">+ Создать ТЗ</button>
                {% elif active_page == 'generator' %}
                <h5 class="m-0 fw-bold text-secondary">📄 Генератор коммерческих предложений</h5>
                {% elif active_page == 'registry' %}
                <h5 class="m-0 fw-bold text-secondary">🗂️ Реестр коммерческих предложений</h5>
                {% elif active_page == 'chat' %}
                <h5 class="m-0 fw-bold text-secondary">💬 Внутренний чат сотрудников</h5>
                {% elif active_page == 'profile' %}
                <h5 class="m-0 fw-bold text-secondary">👤 Настройки профиля</h5>
                {% else %}
                <h5 class="m-0 fw-bold text-secondary">📈 Управленческая аналитика</h5>
                {% endif %}
            </div>
            <div class="d-flex align-items-center gap-2">
                {% if active_page == 'kanban' %}
                <button class="btn btn-warning btn-sm fw-bold text-dark" data-bs-toggle="modal" data-bs-target="#tasksListModal">
                    🔔 Задачи <span class="badge bg-primary ms-1">{{ total_tasks_count }}</span>
                    {% if overdue_count > 0 %}<span class="badge bg-danger ms-1">⚠️ Просрочено: {{ overdue_count }}</span>{% endif %}
                    {% if has_reminders %}<span class="badge bg-danger ms-1 blink-remind">⚡ РОП!</span>{% endif %}
                </button>
                {% endif %}
                <span class="badge d-none d-md-inline-block" style="background: #b8860b;">M-CONSTRUCTION CRM</span>
            </div>
        </div>

        <div class="content-body">
            {{ content|safe }}
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js');
    }

function addPhoneField(containerId, inputName, val="") {
    var c = document.getElementById(containerId);
    var d = document.createElement('div');
    d.className = 'input-group mb-2';
    d.innerHTML = '<input type="text" name="' + inputName + '" class="form-control" value="' + val + '" placeholder="+7..."><button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">Удалить</button>';
    c.appendChild(d);
}
function dragDeal(ev, id) { ev.dataTransfer.setData("dealId", id); }
function allowDrop(ev) { ev.preventDefault(); ev.currentTarget.classList.add("drag-over"); }
function removeDragOver(ev) { ev.currentTarget.classList.remove("drag-over"); }
function dropDeal(ev, stage) {
    ev.preventDefault();
    ev.currentTarget.classList.remove("drag-over");
    var id = ev.dataTransfer.getData("dealId");
    fetch('/move_deal', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({id: id, stage: stage})})
    .then(res => res.json()).then(data => { if(data.success) location.reload(); });
}
</script>
</body>
</html>
"""

def check_phone_approved():
    return session.get("phone_approved", False)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "M-CONSTRUCTION CRM", "short_name": "Мамыр CRM", "start_url": "/", "display": "standalone",
        "background_color": "#eaeff5", "theme_color": "#1a365d", "orientation": "portrait-primary",
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", "sizes": "192x192", "type": "image/png"}]
    })

@app.route('/sw.js')
def service_worker():
    return app.response_class("self.addEventListener('fetch', (event) => {});", mimetype='application/javascript')

def get_counters(db, uname, user_data):
    unread_tz_count = sum(1 for tz in db.get("tz_list", []) if not tz.get("done", False) and (tz.get("responsible") == user_data["name"] or user_data["role"] in ["director", "rop"]))
    user_chats = [c for c in db.get("chats", []) if uname in c.get("members", [])]
    unread_msgs_count = sum(max(0, len(c.get("messages", [])) - c.get(f"read_{uname}", 0)) for c in user_chats)
    return unread_tz_count, unread_msgs_count

@app.route("/request_access", methods=["GET", "POST"])
def request_access():
    if check_phone_approved(): return redirect(url_for("login"))
    error = None
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        if phone:
            code = str(random.randint(1000, 9999))
            db = load_db()
            db["pending_codes"][phone] = code
            save_db(db)
            send_sms_code(code, phone)
            return render_template_string(REQUEST_ACCESS_HTML, step="code", phone=phone, rop_phone=ROP_PHONE, success="Код запрошен.")
        error = "Введите номер."
    return render_template_string(REQUEST_ACCESS_HTML, step="phone", error=error)

@app.route("/verify_code", methods=["POST"])
def verify_code():
    phone = request.form.get("phone", "").strip()
    user_code = request.form.get("code", "").strip()
    db = load_db()
    if db.get("pending_codes", {}).get(phone) == user_code:
        session["phone_approved"] = True
        del db["pending_codes"][phone]
        save_db(db)
        return redirect(url_for("login"))
    return render_template_string(REQUEST_ACCESS_HTML, step="code", phone=phone, rop_phone=ROP_PHONE, error="Неверный код.")

@app.route("/login", methods=["GET", "POST"])
def login():
    if not check_phone_approved(): return redirect(url_for("request_access"))
    error, db = None, load_db()
    if request.method == "POST":
        u, p = request.form.get("username"), request.form.get("password")
        if u in db.get("users", DEFAULT_USERS) and db["users"][u]["pass"] == p:
            session["user"] = u
            return redirect(url_for("index"))
        error = "Неверный логин/пароль."
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
def profile_page():
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    msg = None
    if request.method == "POST":
        for k in ["name", "position", "phone", "whatsapp", "email"]:
            user_data[k] = request.form.get(k, user_data.get(k, ""))
        file = request.files.get("avatar")
        if file and file.filename:
            fn = secure_filename(f"avatar_{uname}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
            user_data["avatar"] = fn
        if request.form.get("new_password"): user_data["pass"] = request.form.get("new_password")
        save_db(db)
        msg = "Обновлено!"
    
    html = f"""<div class="container" style="max-width:600px; margin:0 auto;"><div class="card p-4 bg-white"><h4>Профиль</h4>{f'<div class="alert alert-success">{msg}</div>' if msg else ''}<form method="POST" enctype="multipart/form-data"><div class="mb-3"><label>ФИО:</label><input type="text" name="name" class="form-control" value="{user_data['name']}" required></div><div class="mb-3"><label>Телефон:</label><input type="text" name="phone" class="form-control" value="{user_data.get('phone','')}"></div><button class="btn text-white w-100" style="background:#b8860b;">Сохранить</button></form></div></div>"""
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="Профиль", active_page="profile", current_user_data=user_data, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=html)

@app.route("/analytics")
def analytics_page():
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    if user_data["role"] not in ["director", "rop"]: return "Доступ запрещен"
    
    deals = db.get("deals", [])
    total_deals = len(deals)
    won_sum = sum(d.get("total_sum", 0) for d in deals if d.get("stage") in CONTRACT_STAGES)
    
    html = f"""<div class="card p-4 bg-white"><h4>📈 Управленческая аналитика</h4><hr>
    <p>Всего сделок в воронке: <b>{total_deals}</b></p>
    <p>Общая сумма закрытых договоров: <b class="text-success">{won_sum:,} ₸</b></p></div>"""
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="Аналитика", active_page="analytics", current_user_data=user_data, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=html)

@app.route("/generator")
def generator_page():
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    
    users_json = json.dumps([{"key": k, "name": v["name"], "position": v.get("position",""), "phone": v.get("phone","")} for k, v in db["users"].items()], ensure_ascii=False)
    curr_json = json.dumps({"key": uname, "name": user_data["name"], "position": user_data.get("position",""), "phone": user_data.get("phone","")}, ensure_ascii=False)
    logo_url = url_for('uploaded_file', filename='1000100784.jpg')

    html = f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        .gen-container {{ max-width: 900px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
        .section-title {{ font-size: 13px; font-weight: bold; color: #b8860b; margin: 18px 0 8px 0; text-transform: uppercase; }}
        .form-row {{ display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 12px; }}
        .form-group {{ flex: 1; min-width: 180px; }}
        label {{ display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #4a5568; }}
        input, select {{ width: 100%; padding: 9px 11px; font-size: 14px; border: 1px solid #cbd5e0; border-radius: 6px; }}
        .btn-generate {{ width: 100%; padding: 14px; background: #b8860b; color: #fff; font-size: 16px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 20px; }}
    </style>
    <div class="gen-container">
        <div class="alert alert-secondary py-2 mb-3 d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div>💻 Вы вошли как: <b>{user_data['name']}</b></div>
            <div style="width: 280px;">
                <label style="margin:0; font-size:11px;">Чью подпись использовать в КП?</label>
                <select id="kpSignerSelect" class="form-select form-select-sm"></select>
            </div>
        </div>
        <div class="section-title">1. Данные Заказчика</div>
        <div class="form-row">
            <div class="form-group"><label>Заказчик (ТОО / ИП):</label><input type="text" id="clientName" value="ТОО «Мамыр»"></div>
            <div class="form-group"><label>Телефон:</label><input type="text" id="clientPhone" value="+7 700 000 00 00"></div>
            <div class="form-group"><label>Назначение:</label><input type="text" id="purpose" value="Зернохранилище"></div>
        </div>
        <div class="section-title">2. Параметры ангара</div>
        <div class="form-row">
            <div class="form-group"><label>Ширина (м):</label><input type="number" id="width" value="18"></div>
            <div class="form-group"><label>Длина (м):</label><input type="number" id="length" value="36"></div>
        </div>
        <button class="btn-generate" id="btnGen" onclick="generateAndSaveKP()">📄 Сформировать и скачать КП (PDF)</button>
    </div>
    <script>
        var allUsers = {users_json};
        var currUser = {curr_json};
        var sel = document.getElementById('kpSignerSelect');
        allUsers.forEach(u => {{
            var opt = document.createElement('option');
            opt.value = u.key; opt.text = u.name + ' (' + u.position + ')';
            if(u.key === currUser.key) opt.selected = true;
            sel.appendChild(opt);
        }});
        function generateAndSaveKP() {{
            alert('Генератор КП готов к работе!');
        }}
    </script>
    """
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="Генератор КП", active_page="generator", current_user_data=user_data, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=html)

@app.route("/registry")
def registry_page():
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    if user_data["role"] not in ["director", "rop"]: return "Доступ запрещен"
    
    registry = db.get("kp_registry", [])
    rows = "".join([f"<tr><td>{item.get('id')}</td><td>{item.get('date')}</td><td>{item.get('client')}</td><td>{item.get('manager')}</td><td><b>{item.get('price')}</b></td></tr>" for item in registry])
    
    html = f"""<div class="card p-4 bg-white"><h4>🗂️ Общий реестр КП</h4><hr>
    <table class="table table-bordered"><thead><tr><th>№ КП</th><th>Дата</th><th>Заказчик</th><th>Менеджер</th><th>Сумма</th></tr></thead>
    <tbody>{rows or "<tr><td colspan='5' class='text-center text-muted'>Нет сохраненных КП</td></tr>"}</tbody></table></div>"""
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="Реестр КП", active_page="registry", current_user_data=user_data, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=html)

@app.route("/chat", methods=["GET", "POST"])
@app.route("/chat/<chat_id>", methods=["GET", "POST"])
def chat_page(chat_id=None):
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_chat":
            members = request.form.getlist("members")
            members.append(uname)
            members = list(set(members))
            title = request.form.get("title", "").strip() or "Диалог"
            new_id = f"chat_{len(db.get('chats', []))+1}"
            db["chats"].append({"id": new_id, "title": title, "members": members, "messages": []})
            save_db(db)
            return redirect(url_for("chat_page", chat_id=new_id))
        elif chat_id:
            msg = request.form.get("message", "").strip()
            if msg:
                for c in db["chats"]:
                    if c["id"] == chat_id:
                        c["messages"].append({"author_key": uname, "author_name": user_data["name"], "text": msg, "time": datetime.now().strftime("%d.%m %H:%M")})
                        c[f"read_{uname}"] = len(c["messages"])
                        break
                save_db(db)
                return redirect(url_for("chat_page", chat_id=chat_id))
            
    if chat_id:
        for c in db.get("chats", []):
            if c["id"] == chat_id and uname in c.get("members", []):
                c[f"read_{uname}"] = len(c.get("messages", []))
                save_db(db)
                break

    user_chats = [c for c in db.get("chats", []) if uname in c.get("members", [])]
    active_chat = next((c for c in user_chats if c["id"] == chat_id), None)
    
    chat_list = "".join([f'<a href="/chat/{c["id"]}" class="list-group-item list-group-item-action {"active text-white" if active_chat and c["id"]==active_chat["id"] else ""}">{c["title"]}</a>' for c in user_chats])
    msgs = "".join([f'<div class="mb-2"><b>{m["author_name"]}:</b> {m["text"]} <span class="text-muted small">({m["time"]})</span></div>' for m in active_chat.get("messages", [])]) if active_chat else "<div class='text-muted m-auto'>Выберите чат из списка слева</div>"
    members_chk = "".join([f'<div class="form-check"><input class="form-check-input" type="checkbox" name="members" value="{k}"><label class="form-check-label">{v["name"]}</label></div>' for k, v in db["users"].items() if k != uname])

    html = f"""
    <div class="container-fluid h-100 p-0">
        <div class="row g-0 h-100">
            <div class="col-md-4 border-end bg-white d-flex flex-column h-100">
                <div class="p-3 border-bottom d-flex justify-content-between align-items-center">
                    <b>💬 Диалоги</b>
                    <button class="btn btn-sm btn-dark" data-bs-toggle="modal" data-bs-target="#newChatModal">+ Чат</button>
                </div>
                <div class="list-group list-group-flush overflow-auto flex-grow-1">{chat_list or '<div class="p-3 text-muted">Нет чатов</div>'}</div>
            </div>
            <div class="col-md-8 d-flex flex-column bg-light h-100">
                {f'<div class="p-3 border-bottom bg-white"><b>{active_chat["title"]}</b></div><div class="p-3 flex-grow-1 overflow-auto">{msgs}</div><div class="p-3 bg-white border-top"><form method="POST"><div class="input-group"><input type="text" name="message" class="form-control" placeholder="Сообщение..." required><button class="btn text-white" style="background:#b8860b;">Отправить</button></div></form></div>' if active_chat else '<div class="m-auto text-muted">Выберите или создайте чат</div>'}
            </div>
        </div>
    </div>
    <div class="modal fade" id="newChatModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><form method="POST"><input type="hidden" name="action" value="create_chat">
    <div class="modal-header"><h5 class="modal-title">Новый чат</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
    <div class="modal-body"><div class="mb-3"><label>Название:</label><input type="text" name="title" class="form-control" placeholder="Проект..."></div><label>Участники:</label>{members_chk}</div>
    <div class="modal-footer"><button class="btn text-white" style="background:#b8860b;">Создать</button></div></form></div></div></div>
    """
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="Чат", active_page="chat", current_user_data=user_data, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=html)

@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    
    total_tasks = sum(1 for d in db["deals"] for t in d.get("tasks", []) if not t.get("done", False))
    overdue_count = sum(1 for d in db["deals"] for t in d.get("tasks", []) if not t.get("done", False) and t.get("date", "") < datetime.now().strftime("%Y-%m-%d"))
    
    kanban = '<div class="kanban-outer"><div class="kanban">'
    for sk, sn, sc in STAGES:
        kanban += f'<div class="k-col"><div class="k-header" style="background:{sc};">{sn}</div><div class="k-body">'
        for d in db["deals"]:
            if d.get("stage") == sk:
                kanban += f'<div class="deal-card"><b>{d["client"]}</b><div class="text-muted">Регион: {d.get("region","—")}</div></div>'
        kanban += '</div></div>'
    kanban += '</div></div>'
    
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="Канбан", active_page="kanban", current_user_data=user_data, total_tasks_count=total_tasks, overdue_count=overdue_count, has_reminders=False, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=kanban)

@app.route("/tz")
def tz_page():
    if "user" not in session: return redirect(url_for("login"))
    uname, db = session["user"], load_db()
    user_data = db["users"][uname]
    
    tz_list = "".join([f'<tr><td><b>{t["title"]}</b></td><td>{t["responsible"]}</td><td>{"✓ Выполнено" if t.get("done") else "В работе"}</td></tr>' for t in db.get("tz_list", [])])
    html = f'<div class="container-fluid p-3"><div class="card p-3"><h4>Технические задания</h4><table class="table"><thead><tr><th>Название</th><th>Ответственный</th><th>Статус</th></tr></thead><tbody>{tz_list or "<tr><td colspan=3>Нет ТЗ</td></tr>"}</tbody></table></div></div>'
    tz_c, msg_c = get_counters(db, uname, user_data)
    return render_template_string(BASE_TEMPLATE, page_title="ТЗ", active_page="tz", current_user_data=user_data, unread_tz_count=tz_c, unread_msgs_count=msg_c, content=html)

@app.route("/move_deal", methods=["POST"])
def move_deal():
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
