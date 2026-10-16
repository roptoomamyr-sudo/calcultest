from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, send_from_directory
import json
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "angar_crm_secret_2026"

DB_FILE = "crm_db.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Базовые данные пользователей (теперь с расширенными полями профиля)
DEFAULT_USERS = {
    "director": {"pass": "dir123", "name": "Уралбаев Ж.А.", "role": "director", "phone": "", "whatsapp": "", "email": "", "avatar": ""},
    "rop": {"pass": "rop123", "name": "Лемперт Александр Сергеевич", "role": "rop", "phone": "", "whatsapp": "", "email": "", "avatar": ""},
    "manager1": {"pass": "man123", "name": "Менеджер 1", "role": "manager", "phone": "", "whatsapp": "", "email": "", "avatar": ""},
    "manager2": {"pass": "man223", "name": "Менеджер 2", "role": "manager", "phone": "", "whatsapp": "", "email": "", "avatar": ""},
    "manager3": {"pass": "man323", "name": "Менеджер 3", "role": "manager", "phone": "", "whatsapp": "", "email": "", "avatar": ""}
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

CONTRACT_STAGES = ["stage_11", "stage_12", "stage_13", "stage_14", "stage_15"]

def load_db():
    default_data = {
        "deals": [],
        "tz_list": [],
        "users": DEFAULT_USERS
    }
    if not os.path.exists(DB_FILE):
        save_db(default_data)
        return default_data
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict) or "deals" not in data:
                save_db(default_data)
                return default_data
            if "users" not in data:
                data["users"] = DEFAULT_USERS
            if "tz_list" not in data:
                data["tz_list"] = []
            return data
    except:
        save_db(default_data)
        return default_data

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_all_users():
    db = load_db()
    return db.get("users", DEFAULT_USERS)

LOGIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход в Ангар CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light d-flex align-items-center justify-content-center vh-100">
<form method="POST" class="card p-4 shadow border-0" style="width: 340px;">
    <h3 class="mb-3 text-center text-primary fw-bold">Ангар CRM</h3>
    {% if error %}<div class="alert alert-danger py-1">{{ error }}</div>{% endif %}
    <div class="mb-3"><label class="form-label">Логин:</label><input type="text" name="username" class="form-control" required autofocus></div>
    <div class="mb-3"><label class="form-label">Пароль:</label><input type="password" name="password" class="form-control" required></div>
    <button type="submit" class="btn btn-primary w-100">Войти в систему</button>
</form>
</body>
</html>
"""

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>{{ page_title }} - Ангар CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; font-family: Arial, sans-serif; overflow-x: hidden; }
        .wrapper { display: flex; width: 100%; height: 100vh; overflow: hidden; }
        .sidebar { width: 60px; background: #212529; color: #fff; display: flex; flex-direction: column; flex-shrink: 0; transition: width 0.25s ease-in-out; overflow: hidden; white-space: nowrap; z-index: 1000; }
        .sidebar:hover { width: 240px; }
        .sidebar .brand { padding: 15px; font-size: 16px; font-weight: bold; background: #1a1e21; border-bottom: 1px solid #373b3e; text-align: left; }
        .sidebar .menu { padding: 15px 5px; display: flex; flex-direction: column; gap: 8px; flex-grow: 1; }
        .sidebar .menu a { color: #adb5bd; text-decoration: none; padding: 10px 12px; border-radius: 4px; font-size: 13px; display: flex; align-items: center; gap: 12px; transition: 0.2s; }
        .sidebar .menu a:hover, .sidebar .menu a.active { background: #0d6efd; color: #fff; }
        .sidebar .menu a i { font-size: 16px; min-width: 24px; text-align: center; font-style: normal; }
        
        .main-content { flex-grow: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        .top-bar { background: #ffffff; border-bottom: 1px solid #dee2e6; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; height: 60px; flex-shrink: 0; }
        
        .content-body { flex-grow: 1; display: flex; flex-direction: column; overflow: hidden; padding: 15px; background: #f8f9fa; }
        
        .kanban-outer { flex-grow: 1; overflow-x: auto; overflow-y: hidden; white-space: nowrap; padding-bottom: 10px; }
        .kanban { display: inline-flex; gap: 12px; height: 100%; align-items: flex-start; }

        .kanban-outer::-webkit-scrollbar { height: 12px; }
        .kanban-outer::-webkit-scrollbar-track { background: #dee2e6; border-radius: 6px; }
        .kanban-outer::-webkit-scrollbar-thumb { background: #0d6efd; border-radius: 6px; }

        .k-col { width: 280px; min-width: 280px; max-width: 280px; background: #e9ecef; border-radius: 6px; display: flex; flex-direction: column; max-height: 100%; white-space: normal; }
        .k-header { padding: 10px; font-weight: bold; font-size: 13px; color: white; border-top-left-radius: 6px; border-top-right-radius: 6px; text-align: center; flex-shrink: 0; }
        .k-body { padding: 8px; overflow-y: auto; flex-grow: 1; min-height: 150px; }
        
        .deal-card { background: #ffffff; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 12px; border: 1px solid #ced4da; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab; transition: 0.15s; }
        .deal-card:active { cursor: grabbing; opacity: 0.7; }
        .deal-card:hover { border-color: #0d6efd; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
        .history-box { background: #f1f3f5; border-radius: 4px; padding: 8px; max-height: 130px; overflow-y: auto; font-size: 11px; }
        .drag-over { background-color: #d0e1fd !important; border: 2px dashed #0d6efd; }
        .blink-remind { animation: blinker 1.2s linear infinite; }
        @keyframes blinker { 50% { opacity: 0.3; } }
    </style>
</head>
<body>

<div class="wrapper">
    <div class="sidebar">
        <div class="brand">🏗️ <span>Ангар CRM</span></div>
        <div class="menu">
            <a href="/" class="{% if active_page == 'kanban' %}active{% endif %}"><i>📊</i> <span>Канбан CRM</span></a>
            <a href="/tz" class="{% if active_page == 'tz' %}active{% endif %}"><i>📐</i> <span>Тех. задания</span></a>
            {% if current_user_data.role in ['director', 'rop'] %}
            <a href="/analytics" class="{% if active_page == 'analytics' %}active{% endif %}"><i>📈</i> <span>Воронка (Отчеты)</span></a>
            {% endif %}
            <a href="/profile" class="{% if active_page == 'profile' %}active{% endif %}"><i>👤</i> <span>Мой профиль</span></a>
        </div>
        <div class="p-3 bg-dark border-top border-secondary text-muted small">
            <div class="text-truncate">👤 <b>{{ current_user_data.name }}</b></div>
            <a href="/logout" class="text-danger text-decoration-none mt-1 d-inline-block">🚪 <span>Выйти</span></a>
        </div>
    </div>

    <div class="main-content">
        <div class="top-bar">
            <div class="d-flex align-items-center gap-3">
                {% if active_page == 'kanban' %}
                <h5 class="m-0 fw-bold text-secondary">🗂️ Воронка продаж</h5>
                <button class="btn btn-success btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить сделку</button>
                {% elif active_page == 'tz' %}
                <h5 class="m-0 fw-bold text-secondary">📐 Технические задания</h5>
                <button class="btn btn-primary btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addTzModal">+ Создать ТЗ</button>
                {% elif active_page == 'profile' %}
                <h5 class="m-0 fw-bold text-secondary">👤 Настройки профиля</h5>
                {% else %}
                <h5 class="m-0 fw-bold text-secondary">📈 Воронка продаж и Отчеты</h5>
                {% endif %}
            </div>
            <div class="d-flex align-items-center gap-3">
                {% if active_page == 'kanban' %}
                <button class="btn btn-warning btn-sm fw-bold text-dark" data-bs-toggle="modal" data-bs-target="#tasksListModal">
                    🔔 Задачи <span class="badge bg-primary ms-1">{{ total_tasks_count }}</span>
                    {% if overdue_count > 0 %}<span class="badge bg-danger ms-1">⚠️ Просрочено: {{ overdue_count }}</span>{% endif %}
                    {% if has_reminders %}<span class="badge bg-danger ms-1 blink-remind">⚡ РОП Напоминает!</span>{% endif %}
                </button>
                {% endif %}
                <span class="badge bg-success">Render Cloud Активен</span>
            </div>
        </div>

        <div class="content-body">
            {{ content|safe }}
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script>
function addPhoneField(id) {
    var c = document.getElementById(id);
    var d = document.createElement('div');
    d.className = 'input-group mb-2';
    d.innerHTML = '<input type="text" name="phones" class="form-control" placeholder="+7..."><button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">Удалить</button>';
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

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u in users and users[u]["pass"] == p:
            session["user"] = u
            return redirect(url_for("index"))
        error = "Неверный логин или пароль"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/profile", methods=["GET", "POST"])
def profile_page():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    success_msg = ""
    error_msg = ""
    
    if request.method == "POST":
        new_name = request.form.get("name", "").strip()
        new_phone = request.form.get("phone", "").strip()
        new_whatsapp = request.form.get("whatsapp", "").strip()
        new_email = request.form.get("email", "").strip()
        old_pass = request.form.get("old_pass", "").strip()
        new_pass = request.form.get("new_pass", "").strip()
        
        avatar_file = request.files.get("avatar")
        if avatar_file and avatar_file.filename:
            filename_str = secure_filename(f"avatar_{uname}_{int(datetime.now().timestamp())}_{avatar_file.filename}")
            avatar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_str))
            user_data["avatar"] = filename_str

        if new_name:
            user_data["name"] = new_name
        user_data["phone"] = new_phone
        user_data["whatsapp"] = new_whatsapp
        user_data["email"] = new_email
        
        if new_pass:
            if old_pass == user_data["pass"]:
                user_data["pass"] = new_pass
                success_msg = "Профиль и пароль успешно обновлены!"
            else:
                error_msg = "Неверно указан текущий пароль!"
        else:
            success_msg = "Профиль успешно обновлен!"
            
        users[uname] = user_data
        db["users"] = users
        save_db(db)

    avatar_html = f'<img src="/uploads/{user_data["avatar"]}" class="rounded-circle border" width="100" height="100" style="object-fit: cover;">' if user_data.get("avatar") else '<div class="rounded-circle bg-secondary text-white d-flex align-items-center justify-content-center fw-bold fs-2" style="width: 100px; height: 100px;">👤</div>'

    profile_content = f"""
    <div class="container-fluid p-4" style="max-width: 700px;">
        <div class="card shadow-sm border-0">
            <div class="card-header bg-primary text-white fw-bold">⚙️ Редактирование профиля сотрудника</div>
            <div class="card-body">
                {f'<div class="alert alert-success">{success_msg}</div>' if success_msg else ''}
                {f'<div class="alert alert-danger">{error_msg}</div>' if error_msg else ''}
                <form method="POST" enctype="multipart/form-data">
                    <div class="d-flex align-items-center gap-4 mb-4">
                        <div>{avatar_html}</div>
                        <div>
                            <label class="form-label fw-bold">Фото профиля:</label>
                            <input type="file" name="avatar" class="form-control form-control-sm">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">ФИО сотрудника:</label>
                        <input type="text" name="name" class="form-control" value="{user_data.get('name', '')}" required>
                    </div>
                    <div class="row g-3 mb-3">
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Прямый номер телефона:</label>
                            <input type="text" name="phone" class="form-control" value="{user_data.get('phone', '')}" placeholder="+7...">
                        </div>
                        <div class="col-md-6">
                            <label class="form-label fw-bold">Номер WhatsApp:</label>
                            <input type="text" name="whatsapp" class="form-control" value="{user_data.get('whatsapp', '')}" placeholder="+7...">
                        </div>
                    </div>
                    <div class="mb-3">
                        <label class="form-label fw-bold">Email:</label>
                        <input type="email" name="email" class="form-control" value="{user_data.get('email', '')}" placeholder="example@mail.kz">
                    </div>
                    <hr class="my-4">
                    <h6 class="fw-bold text-secondary mb-3">🔒 Смена пароля (если требуется)</h6>
                    <div class="mb-3">
                        <label class="form-label">Текущий пароль:</label>
                        <input type="password" name="old_pass" class="form-control">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Новый пароль:</label>
                        <input type="password" name="new_pass" class="form-control">
                    </div>
                    <button type="submit" class="btn btn-primary fw-bold w-100">Сохранить изменения</button>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE, page_title="Профиль", active_page="profile", current_user_data=user_data, content=profile_content)

@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    search_query = request.args.get("q", "").strip().lower()
    selected_manager = request.args.get("manager_filter", "all")
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    total_tasks = 0
    overdue_count = 0
    has_reminders = False
    
    for d in db["deals"]:
        for t in d.get("tasks", []):
            if not t.get("done", False):
                total_tasks += 1
                if t.get("date", "") < today_str:
                    overdue_count += 1
                if t.get("reminded", False):
                    has_reminders = True

    # Формируем список менеджеров для фильтра и селектов на основе реальных имен
    manager_names_list = [u_info["name"] for u_info in users.values()]

    filter_html = f"""
    <div class="card shadow-sm border-0 mb-3 p-3 bg-white flex-shrink-0">
        <form method="GET" action="/" class="row g-2 align-items-center">
            <div class="col-md-5">
                <div class="input-group">
                    <span class="input-group-text bg-light">🔍 Поиск:</span>
                    <input type="text" name="q" class="form-control" value="{search_query}" placeholder="Компания, ФИО директора, контакт или телефон...">
                </div>
            </div>
            <div class="col-md-4">
                <div class="input-group">
                    <span class="input-group-text bg-light">👤 Менеджер:</span>
                    <select name="manager_filter" class="form-select">
    """
    
    if user_data["role"] in ["director", "rop"]:
        filter_html += f'<option value="all" {"selected" if selected_manager=="all" else ""}>Все менеджеры</option>'
        for m_name in manager_names_list:
            sel = "selected" if selected_manager == m_name else ""
            filter_html += f'<option value="{m_name}" {sel}>{m_name}</option>'
    else:
        filter_html += f'<option value="{user_data["name"]}" {"selected" if selected_manager==user_data["name"] else ""}>Только мои сделки</option>'
        filter_html += f'<option value="all" {"selected" if selected_manager=="all" else ""}>Все клиенты компании</option>'

    filter_html += f"""
                    </select>
                </div>
            </div>
            <div class="col-md-3 d-flex gap-2">
                <button type="submit" class="btn btn-primary btn-sm fw-bold w-50">Найти</button>
                <a href="/" class="btn btn-outline-secondary btn-sm w-50">Сбросить</a>
            </div>
        </form>
    </div>
    """
                    
    kanban_content = filter_html + '<div class="kanban-outer"><div class="kanban">'
    for s_key, s_name, s_color in STAGES:
        color_style = f"background-color: {s_color};"
        if s_key == 'stage_2': color_style += " color: #000;"
        
        kanban_content += f"""
        <div class="k-col" data-stage="{s_key}">
            <div class="k-header" style="{color_style}">{s_name}</div>
            <div class="k-body" id="col-{s_key}" ondragover="allowDrop(event)" ondragleave="removeDragOver(event)" ondrop="dropDeal(event, '{s_key}')">
        """
        for d in db["deals"]:
            if d.get("stage") == s_key:
                deal_mgr = d.get("manager", "")
                if user_data["role"] not in ["director", "rop"]:
                    if selected_manager != "all" and deal_mgr != user_data["name"]:
                        continue
                else:
                    if selected_manager != "all" and deal_mgr != selected_manager:
                        continue

                if search_query:
                    c_title = d.get("client", "").lower()
                    c_dir = d.get("director", "").lower()
                    c_pers = d.get("contact_person", "").lower()
                    c_ph = "".join(d.get("phones", [])) + d.get("contact_phone", "")
                    match = (search_query in c_title) or (search_query in c_dir) or (search_query in c_pers) or (search_query in c_ph)
                    if not match:
                        continue

                region_text = d.get('region') or 'Регион не указан'
                dir_text = d.get('director') or 'Не указан'
                contact_p_text = d.get('contact_person') or '—'
                phone_text = d.get('phones')[0] if d.get('phones') else 'Нет телефона'
                sum_val = d.get('total_sum', 0)
                sum_str = "{:,}".format(sum_val).replace(",", " ") if d.get('stage') in CONTRACT_STAGES else "—"
                manager_text = deal_mgr or 'Не назначен'
                
                tasks_badge = ""
                for t in d.get("tasks", []):
                    if not t.get("done"):
                        if t.get("date") < today_str:
                            tasks_badge += f'<div class="mt-1"><span class="badge bg-danger">⚠️ Просрочено: {t.get("date")}</span></div>'
                        else:
                            tasks_badge += f'<div class="mt-1"><span class="badge bg-warning text-dark">⏰ {t.get("date")}</span></div>'
                        if t.get("reminded"):
                            tasks_badge += '<div class="mt-1"><span class="badge bg-danger text-white blink-remind">⚡ РОП ТРЕБУЕТ ВЫПОЛНИТЬ!</span></div>'

                kanban_content += f"""
                <div class="deal-card" id="card-{d['id']}" draggable="true" ondragstart="dragDeal(event, '{d['id']}')" data-bs-toggle="modal" data-bs-target="#cardModal{d['id']}">
                    <div class="fw-bold text-primary mb-1" style="font-size: 13px;">{d['title']}</div>
                    <div class="text-muted text-truncate">📍 {region_text}</div>
                    <div class="text-secondary text-truncate">👤 Директор: {dir_text}</div>
                    <div class="text-secondary text-truncate">🤝 Контакт: {contact_p_text}</div>
                    <div class="text-dark text-truncate">📞 {phone_text}</div>
                    {tasks_badge}
                    <div class="mt-2 pt-1 border-top d-flex justify-content-between text-muted" style="font-size: 11px;">
                        <span>Сумма: {sum_str} ₸</span>
                        <span class="badge bg-light text-dark border">{manager_text}</span>
                    </div>
                </div>

                <!-- Модалка сделки -->
                <div class="modal fade" id="cardModal{d['id']}" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <form method="POST" action="/update/{d['id']}">
                                <div class="modal-header bg-primary text-white">
                                    <h5 class="modal-title">Карточка клиента: {d['client']}</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row g-3">
                                        <div class="col-md-6"><label class="form-label fw-bold">ТОО / КХ:</label><input type="text" name="client" class="form-control" value="{d['client']}" required></div>
                                        <div class="col-md-6"><label class="form-label fw-bold">Расположение:</label><input type="text" name="region" class="form-control" value="{d.get('region', '')}"></div>
                                        <div class="col-md-6"><label class="form-label fw-bold">ФИО Директора:</label><input type="text" name="director" class="form-control" value="{d.get('director', '')}"></div>
                                        <div class="col-md-6"><label class="form-label fw-bold">Email:</label><input type="email" name="email" class="form-control" value="{d.get('email', '')}"></div>
                                        <div class="col-md-6"><label class="form-label fw-bold">Контактное лицо (ЛПР/Представитель):</label><input type="text" name="contact_person" class="form-control" value="{d.get('contact_person', '')}"></div>
                                        <div class="col-md-6"><label class="form-label fw-bold">Телефон контактного лица:</label><input type="text" name="contact_phone" class="form-control" value="{d.get('contact_phone', '')}"></div>
                                        <div class="col-md-12">
                                            <label class="form-label fw-bold">Телефоны ТОО/КХ:</label>
                                            <div id="phones-container-{d['id']}">
                """
                for ph in d.get("phones", []):
                    kanban_content += f'<div class="input-group mb-2"><input type="text" name="phones" class="form-control" value="{ph}"><button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">Удалить</button></div>'
                
                sum_input = f'<input type="number" name="total_sum" class="form-control border-success fw-bold" value="{d.get("total_sum", 0)}">' if d['stage'] in CONTRACT_STAGES else f'<input type="number" name="total_sum" class="form-control bg-light" value="{d.get("total_sum", 0)}" readonly>'
                
                kanban_content += f"""
                                            </div>
                                            <button type="button" class="btn btn-outline-secondary btn-sm mt-1" onclick="addPhoneField('phones-container-{d['id']}')">+ Телефон</button>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Этап воронки:</label>
                                            <select name="stage" class="form-select">
                """
                for sk, sn, sc in STAGES:
                    sel = "selected" if d['stage'] == sk else ""
                    kanban_content += f'<option value="{sk}" {sel}>{sn}</option>'
                
                kanban_content += f"""
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Ответственный менеджер:</label>
                """
                if user_data["role"] in ["director", "rop"]:
                    kanban_content += f"""
                    <select name="manager" class="form-select">
                        <option value="Не назначен" {'selected' if d.get('manager')=='Не назначен' else ''}>Не назначен</option>
                    """
                    for m_name in manager_names_list:
                        sel_m = 'selected' if d.get('manager') == m_name else ''
                        kanban_content += f'<option value="{m_name}" {sel_m}>{m_name}</option>'
                    kanban_content += '</select>'
                else:
                    kanban_content += f'<input type="text" class="form-control bg-light" value="{d.get("manager", "")}" readonly><input type="hidden" name="manager" value="{d.get("manager", "")}">'

                kanban_content += f"""
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Сумма сделки (₸):</label>
                                            {sum_input}
                                        </div>
                                        <div class="col-12 bg-light p-3 border rounded">
                                            <h6 class="fw-bold text-dark m-0 mb-2">⏰ Новая задача:</h6>
                                            <div class="row g-2">
                                                <div class="col-md-4"><input type="date" name="task_date" class="form-control form-control-sm"></div>
                                                <div class="col-md-4">
                                                    <select name="task_type" class="form-select form-select-sm">
                                                        <option value="Звонок">📞 Звонок</option>
                                                        <option value="Встреча">🤝 Встреча</option>
                                                        <option value="Отправить КП">📄 Отправить КП</option>
                                                    </select>
                                                </div>
                                                <div class="col-md-4"><input type="text" name="task_text" class="form-control form-control-sm" placeholder="Что сделать..."></div>
                                            </div>
                                        </div>
                                        <div class="col-12">
                                            <label class="form-label fw-bold text-success">+ Добавить комментарий:</label>
                                            <textarea name="new_comment" class="form-control" rows="2" placeholder="Введите примечание / детали диалога..."></textarea>
                                        </div>
                                        <div class="col-12">
                                            <label class="form-label fw-bold text-secondary">📜 История и комментарии:</label>
                                            <div class="history-box">
                """
                for h in reversed(d.get("history", [])):
                    kanban_content += f'<div class="mb-1 border-bottom pb-1"><span class="text-primary fw-bold">[{h.get("date")}] {h.get("author")}:</span> <span>{h.get("text")}</span></div>'
                
                kanban_content += """
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer"><button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button><button type="submit" class="btn btn-primary">Сохранить</button></div>
                            </form>
                        </div>
                    </div>
                </div>
                """
        kanban_content += '</div></div>'
    kanban_content += '</div>'

    # Модалка задач
    kanban_content += '<div class="modal fade" id="tasksListModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-header bg-warning text-dark"><h5 class="modal-title fw-bold">🔔 Панель задач и контроля</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body"><div class="list-group">'
    for d in db["deals"]:
        for t in d.get("tasks", []):
            if not t.get("done", False):
                is_overdue = t.get("date") < today_str
                badge_class = "list-group-item-danger" if is_overdue else ""
                date_badge = f'<span class="badge bg-danger">⚠️ Просрочено ({t.get("date")})</span>' if is_overdue else f'<span class="badge bg-primary">{t.get("date")}</span>'
                remind_badge = '<span class="badge bg-danger text-white blink-remind ms-1">⚡ РОП НАПОМИНАЕТ!</span>' if t.get("reminded") else ''
                remind_btn = f'<form method="POST" action="/remind_task/{d["id"]}/{t["id"]}"><button type="submit" class="btn btn-danger btn-sm fw-bold">⚡ Напомнить</button></form>' if user_data["role"] in ["director", "rop"] and is_overdue else ''
                
                kanban_content += f'''
                <div class="list-group-item d-flex justify-content-between align-items-center {badge_class}">
                    <div>
                        {date_badge} {remind_badge}
                        <span class="badge bg-dark">{t.get("type")}</span>
                        <strong class="ms-2">{d['client']}</strong>
                        <div class="small mt-1">{t.get("text")}</div>
                        <div class="small text-muted mt-1">Ответственный: <b>{d.get('manager')}</b></div>
                    </div>
                    <div class="d-flex gap-2">
                        <form method="POST" action="/complete_task/{d['id']}/{t['id']}"><button type="submit" class="btn btn-success btn-sm fw-bold">✓ Выполнил</button></form>
                        {remind_btn}
                    </div>
                </div>
                '''
    kanban_content += '</div></div></div></div></div>'

    # Модалка добавления сделки
    stages_opts = "".join([f'<option value="{sk}">{sn}</option>' for sk, sn, sc in STAGES])
    
    manager_options_add = f'<option value="{user_data["name"]}">{user_data["name"]}</option>'
    for m_name in manager_names_list:
        if m_name != user_data["name"]:
            manager_options_add += f'<option value="{m_name}">{m_name}</option>'

    kanban_content += f"""
    <div class="modal fade" id="addModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form method="POST" action="/add">
                    <div class="modal-header bg-success text-white"><h5 class="modal-title fw-bold">➕ Новая сделка</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div>
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-6"><label class="form-label fw-bold">ТОО / КХ:</label><input type="text" name="client" class="form-control" required placeholder="ТОО Агро"></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Этап:</label><select name="stage" class="form-select">{stages_opts}</select></div>
                            <div class="col-md-6">
                                <label class="form-label fw-bold">Ответственный:</label>
                                <select name="manager" class="form-select">
                                    {manager_options_add}
                                </select>
                            </div>
                            <div class="col-md-6"><label class="form-label fw-bold">Расположение:</label><input type="text" name="region" class="form-control" placeholder="Костанай"></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Директор:</label><input type="text" name="director" class="form-control" placeholder="Иванов И.И."></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Email:</label><input type="email" name="email" class="form-control"></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Контактное лицо (ЛПР):</label><input type="text" name="contact_person" class="form-control" placeholder="Бухгалтер Светлана"></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Телефон контактного лица:</label><input type="text" name="contact_phone" class="form-control" placeholder="+7 701..."></div>
                            <div class="col-12">
                                <label class="form-label fw-bold">Телефон ТОО/КХ:</label>
                                <div id="new-phones-container"><div class="input-group mb-2"><input type="text" name="phones" class="form-control" placeholder="+7..."></div></div>
                                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="addPhoneField('new-phones-container')">+ Телефон</button>
                            </div>
                            <div class="col-12">
                                <label class="form-label fw-bold">Первичный комментарий:</label>
                                <textarea name="comment" class="form-control" rows="2" placeholder="Опишите первые детали обращения..."></textarea>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer"><button type="submit" class="btn btn-success">Создать</button></div>
                </form>
            </div>
        </div>
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, page_title="Воронка продаж", active_page="kanban", current_user_data=user_data, total_tasks_count=total_tasks, overdue_count=overdue_count, has_reminders=has_reminders, content=kanban_content)

@app.route("/tz")
def tz_page():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    manager_names_list = [u_info["name"] for u_info in users.values()]
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    tz_content = """
    <div class="container-fluid p-3">
        <div class="card shadow-sm border-0">
            <div class="card-body">
                <table class="table table-hover align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th>Название ТЗ</th>
                            <th>Автор</th>
                            <th>Ответственный</th>
                            <th>Наблюдатель</th>
                            <th>Срочность</th>
                            <th>Срок</th>
                            <th>Статус</th>
                            <th>Действие</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    if db.get("tz_list"):
        for tz in db["tz_list"]:
            is_overdue = not tz.get("done") and tz.get("due_date", "") < today_str
            urgency_badge = ""
            if tz.get("urgency") == "горячая":
                urgency_badge = '<span class="badge bg-danger">🔴 Горячая</span>'
            elif tz.get("urgency") == "теплая":
                urgency_badge = '<span class="badge bg-warning text-dark">🟡 Теплая</span>'
            else:
                urgency_badge = '<span class="badge bg-info text-dark">🔵 Холодная</span>'
                
            remind_alert = '<br><span class="badge bg-danger blink-remind mt-1">⚡ РОП НАПОМИНАЕТ!</span>' if tz.get("reminded") else ''
            status_badge = '<span class="badge bg-success">✓ Выполнено</span>' if tz.get("done") else ('<span class="badge bg-danger">⚠️ Просрочено</span>' if is_overdue else '<span class="badge bg-primary">В работе</span>')
            
            can_open = (user_data["name"] == tz.get("author") or user_data["name"] == tz.get("responsible") or user_data["name"] == tz.get("observer") or user_data["role"] in ["director", "rop"])
            
            if can_open:
                title_cell = f'<a href="#" data-bs-toggle="modal" data-bs-target="#tzModal{tz["id"]}" class="fw-bold text-primary text-decoration-none">{tz["title"]}</a>'
            else:
                title_cell = f'<span class="fw-bold text-secondary">{tz["title"]} 🔒</span>'

            action_btn = ""
            if not tz.get("done"):
                if user_data["name"] == tz.get("responsible") or user_data["role"] in ["director", "rop"]:
                    action_btn += f'''
                    <form method="POST" action="/tz/complete/{tz['id']}" class="d-inline">
                        <button type="submit" class="btn btn-success btn-sm fw-bold">✓ Выполнил</button>
                    </form>
                    '''
                if is_overdue and (user_data["role"] in ["director", "rop"] or user_data["name"] == tz.get("observer")):
                    action_btn += f'''
                    <form method="POST" action="/tz/remind/{tz['id']}" class="d-inline ms-1">
                        <button type="submit" class="btn btn-danger btn-sm fw-bold">⚡ Напомнить</button>
                    </form>
                    '''

            tz_content += f"""
            <tr>
                <td>{title_cell}</td>
                <td><span class="badge bg-secondary">{tz['author']}</span></td>
                <td><span class="badge bg-dark">{tz['responsible']}</span>{remind_alert}</td>
                <td><span class="badge bg-light text-dark border">{tz['observer']}</span></td>
                <td>{urgency_badge}</td>
                <td class="small">{tz.get('due_date', '—')}</td>
                <td>{status_badge}</td>
                <td>{action_btn}</td>
            </tr>
            """

            history_html = ""
            for h in reversed(tz.get("history", [])):
                history_html += f'<div class="mb-1 border-bottom pb-1"><span class="text-primary fw-bold">[{h.get("date")}] {h.get("author")}:</span> <span>{h.get("text")}</span></div>'

            is_author = (user_data["name"] == tz.get("author") or user_data["role"] in ["director", "rop"])
            disabled_attr = "" if is_author else "disabled"

            file_section = ""
            if tz.get("filename"):
                file_section = f'<div class="alert alert-secondary py-2 mt-2">📎 Прикрепленный файл: <a href="/uploads/{tz["filename"]}" target="_blank" class="fw-bold text-decoration-none">📥 Скачать файл</a></div>'

            tz_content += f"""
            <div class="modal fade" id="tzModal{tz['id']}" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <form method="POST" action="/tz/update/{tz['id']}" enctype="multipart/form-data">
                            <div class="modal-header bg-primary text-white">
                                <h5 class="modal-title fw-bold">📐 ТЗ: {tz['title']}</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <div class="row g-3">
                                    <div class="col-md-12">
                                        <label class="form-label fw-bold">Название задания:</label>
                                        <input type="text" name="title" class="form-control" value="{tz['title']}" {disabled_attr} required>
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label fw-bold">Описание / Параметры:</label>
                                        <textarea name="description" class="form-control" rows="3" {disabled_attr} required>{tz['description']}</textarea>
                                    </div>
                                    <div class="col-12">
                                        {file_section}
                                        {f'<label class="form-label fw-bold">Заменить / прикрепить новый файл (чертеж/КП):</label><input type="file" name="file" class="form-control">' if is_author else ''}
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label fw-bold">Ответственный:</label>
                                        <input type="text" class="form-control bg-light" value="{tz['responsible']}" readonly>
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label fw-bold">Наблюдатель:</label>
                                        <input type="text" class="form-control bg-light" value="{tz['observer']}" readonly>
                                    </div>
                                    <div class="col-md-4">
                                        <label class="form-label fw-bold">Срочность:</label>
                                        <input type="text" class="form-control bg-light" value="{tz['urgency']}" readonly>
                                    </div>
                                    <div class="col-12">
                                        <label class="form-label fw-bold text-secondary">📜 История изменений ТЗ:</label>
                                        <div class="history-box">{history_html if history_html else 'Нет изменений'}</div>
                                    </div>
                                </div>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Закрыть</button>
                                {f'<button type="submit" class="btn btn-primary btn-sm fw-bold">Сохранить изменения</button>' if is_author else ''}
                            </div>
                        </form>
                    </div>
                </div>
            </div>
            """
    else:
        tz_content += '<tr><td colspan="8" class="text-center text-muted py-4">Технические задания пока не создавались.</td></tr>'
        
    resp_opts = "".join([f'<option value="{m}">{m}</option>' for m in manager_names_list])
    obs_opts = "".join([f'<option value="{m}">{m}</option>' for m in manager_names_list])

    tz_content += f"""
        <!-- Модалка создания ТЗ -->
        <div class="modal fade" id="addTzModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <form method="POST" action="/tz/add" enctype="multipart/form-data">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title fw-bold">📐 Новое техническое задание</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row g-3">
                                <div class="col-md-12">
                                    <label class="form-label fw-bold">Название задания:</label>
                                    <input type="text" name="title" class="form-control" required placeholder="Например: Отправить чертежи на фундамент / Согласовать сверхскидку">
                                </div>
                                <div class="col-12">
                                    <label class="form-label fw-bold">Описание задания / Параметры:</label>
                                    <textarea name="description" class="form-control" rows="3" required placeholder="Детальное описание того, что необходимо сделать..."></textarea>
                                </div>
                                <div class="col-12">
                                    <label class="form-label fw-bold">Прикрепить файл (чертеж, PDF, КП):</label>
                                    <input type="file" name="file" class="form-control">
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fw-bold">Ответственный:</label>
                                    <select name="responsible" class="form-select">
                                        {resp_opts}
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fw-bold">Наблюдатель:</label>
                                    <select name="observer" class="form-select">
                                        {obs_opts}
                                    </select>
                                </div>
                                <div class="col-md-4">
                                    <label class="form-label fw-bold">Срочность:</label>
                                    <select name="urgency" class="form-select">
                                        <option value="горячая">🔴 Горячая (Сегодня)</option>
                                        <option value="теплая">🟡 Теплая (2-3 дня)</option>
                                        <option value="холодная">🔵 Холодная (По возможности)</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Отмена</button>
                            <button type="submit" class="btn btn-primary btn-sm fw-bold">Поставить ТЗ</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE, page_title="Технические задания", active_page="tz", current_user_data=user_data, content=tz_content)

@app.route("/uploads/<path:filename>")
def downloaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/tz/add", methods=["POST"])
def add_tz():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    if "tz_list" not in db: db["tz_list"] = []
    
    urgency = request.form.get("urgency", "теплая")
    today = datetime.now()
    if urgency == "горячая":
        due_date = today.strftime("%Y-%m-%d")
    elif urgency == "теплая":
        due_date = (today + timedelta(days=2)).strftime("%Y-%m-%d")
    else:
        due_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
    
    filename_str = ""
    file = request.files.get("file")
    if file and file.filename:
        filename_str = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_str))

    now_str = today.strftime("%d.%m.%Y %H:%M")
    db["tz_list"].append({
        "id": f"tz_{len(db['tz_list'])+1}",
        "title": request.form.get("title"),
        "description": request.form.get("description"),
        "filename": filename_str,
        "author": user_data["name"],
        "responsible": request.form.get("responsible"),
        "observer": request.form.get("observer"),
        "urgency": urgency,
        "due_date": due_date,
        "done": False,
        "reminded": False,
        "history": [{"date": now_str, "author": user_data["name"], "text": "Создано техническое задание" + (" с прикрепленным файлом" if filename_str else "")}],
        "created_at": now_str
    })
    save_db(db)
    return redirect(url_for("tz_page"))

@app.route("/tz/update/<tz_id>", methods=["POST"])
def update_tz(tz_id):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    for tz in db.get("tz_list", []):
        if tz["id"] == tz_id:
            if user_data["name"] != tz.get("author") and user_data["role"] not in ["director", "rop"]:
                return redirect(url_for("tz_page"))
                
            new_title = request.form.get("title")
            new_desc = request.form.get("description")
            
            changes = []
            if tz["title"] != new_title:
                changes.append(f"Изменил название с '{tz['title']}' на '{new_title}'")
                tz["title"] = new_title
            if tz["description"] != new_desc:
                changes.append("Обновил описание ТЗ")
                tz["description"] = new_desc
                
            file = request.files.get("file")
            if file and file.filename:
                filename_str = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_str))
                tz["filename"] = filename_str
                changes.append(f"Загрузил новый файл: {file.filename}")

            if changes:
                if "history" not in tz: tz["history"] = []
                for change in changes:
                    tz["history"].append({"date": now_str, "author": user_data["name"], "text": change})
            break
            
    save_db(db)
    return redirect(url_for("tz_page"))

@app.route("/tz/remind/<tz_id>", methods=["POST"])
def remind_tz(tz_id):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    for tz in db.get("tz_list", []):
        if tz["id"] == tz_id:
            tz["reminded"] = True
            if "history" not in tz: tz["history"] = []
            tz["history"].append({"date": now_str, "author": user_data["name"], "text": "⚡ РОП напомнил ответственному по ТЗ!"})
            break
    save_db(db)
    return redirect(url_for("tz_page"))

@app.route("/tz/complete/<tz_id>", methods=["POST"])
def complete_tz(tz_id):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    for tz in db.get("tz_list", []):
        if tz["id"] == tz_id:
            tz["done"] = True
            tz["reminded"] = False
            if "history" not in tz: tz["history"] = []
            tz["history"].append({"date": now_str, "author": user_data["name"], "text": "✓ ТЗ выполнено"})
            break
    save_db(db)
    return redirect(url_for("tz_page"))

@app.route("/analytics")
def analytics_page():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    if user_data["role"] not in ["director", "rop"]:
        return "<h3 style='color:red; text-align:center; margin-top:50px;'>⛔ Доступ запрещен! Доступно только РОПу и Директору.</h3><p style='text-align:center;'><a href='/'>Вернуться в CRM</a></p>"
    
    total_deals = len(db["deals"])
    total_contract_sum = sum(d.get("total_sum", 0) for d in db["deals"])
    total_tz = len(db.get("tz_list", []))
    sum_formatted = "{:,}".format(total_contract_sum).replace(",", " ")
    
    analytics_content = f"""
    <div class="container-fluid p-4">
        <div class="row g-3">
            <div class="col-md-4"><div class="card shadow-sm border-0 bg-primary text-white p-3"><h5>📊 Всего сделок в работе</h5><h3>{total_deals}</h3></div></div>
            <div class="col-md-4"><div class="card shadow-sm border-0 bg-success text-white p-3"><h5>💰 Сумма по договорам</h5><h3>{sum_formatted} ₸</h3></div></div>
            <div class="col-md-4"><div class="card shadow-sm border-0 bg-warning text-dark p-3"><h5>📐 Активных ТЗ</h5><h3>{total_tz}</h3></div></div>
        </div>
        <div class="card shadow-sm border-0 mt-4 p-4">
            <h5 class="fw-bold text-secondary">📈 Управленческий срез по воронке</h5>
            <p class="text-muted">Контроль показателей эффективности и движения сделок по этапам.</p>
        </div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE, page_title="Аналитика", active_page="analytics", current_user_data=user_data, content=analytics_content)

@app.route("/move_deal", methods=["POST"])
def move_deal():
    if "user" not in session: return jsonify({"success": False})
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    data = request.get_json()
    deal_id = data.get("id")
    target_stage = data.get("stage")
    
    for d in db["deals"]:
        if d["id"] == deal_id:
            old_stage = d["stage"]
            if old_stage != target_stage:
                stage_name = target_stage
                for sk, sn, sc in STAGES:
                    if sk == target_stage: stage_name = sn
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
                d["stage"] = target_stage
                d["history"].append({"date": now_str, "author": user_data["name"], "text": f"Перетащил карточку на этап: {stage_name}"})
                save_db(db)
                return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    client_name = request.form.get("client")
    selected_stage = request.form.get("stage", "stage_1")
    selected_manager = request.form.get("manager", user_data["name"])
    director = request.form.get("director", "").strip()
    contact_person = request.form.get("contact_person", "").strip()
    contact_phone = request.form.get("contact_phone", "").strip()
    phones = [p.strip() for p in request.form.getlist("phones") if p.strip()]
    region = request.form.get("region", "").strip()
    email = request.form.get("email", "").strip()
    comment = request.form.get("comment", "").strip()
    
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    history_entries = [{"date": now_str, "author": user_data["name"], "text": "Создана новая заявка"}]
    if comment:
        history_entries.append({"date": now_str, "author": user_data["name"], "text": f"💬 Первичный комментарий: {comment}"})

    db["deals"].append({
        "id": str(len(db["deals"]) + 1),
        "title": client_name,
        "client": client_name,
        "director": director,
        "contact_person": contact_person,
        "contact_phone": contact_phone,
        "phones": phones,
        "email": email,
        "region": region,
        "stage": selected_stage,
        "manager": selected_manager,
        "total_sum": 0,
        "history": history_entries,
        "tasks": []
    })
    save_db(db)
    return redirect(url_for("index"))

@app.route("/update/<id>", methods=["POST"])
def update(id):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    current_user_data = users[uname]
    
    for d in db["deals"]:
        if d["id"] == id:
            client_name = request.form.get("client")
            new_stage = request.form.get("stage")
            new_comment = request.form.get("new_comment", "").strip()
            
            new_director = request.form.get("director", "").strip()
            new_contact_person = request.form.get("contact_person", "").strip()
            new_contact_phone = request.form.get("contact_phone", "").strip()
            new_phones = [p.strip() for p in request.form.getlist("phones") if p.strip()]
            new_region = request.form.get("region", "").strip()
            new_email = request.form.get("email", "").strip()
            
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            
            if d.get("contact_person") != new_contact_person:
                d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"Обновил контактное лицо: {new_contact_person}"})
            
            old_phones = d.get("phones", [])
            removed_phones = [p for p in old_phones if p not in new_phones]
            if removed_phones:
                d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"🗑️ Удалил номера телефонов: {', '.join(removed_phones)}"})
            
            added_phones = [p for p in new_phones if p not in old_phones]
            if added_phones:
                d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"➕ Добавил номера телефонов: {', '.join(added_phones)}"})

            d["director"] = new_director
            d["contact_person"] = new_contact_person
            d["contact_phone"] = new_contact_phone
            d["phones"] = new_phones
            d["region"] = new_region
            d["email"] = new_email
            
            if new_stage in CONTRACT_STAGES:
                new_sum = int(request.form.get("total_sum") or 0)
                if d["total_sum"] != new_sum:
                    d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"Изменил сумму на: {new_sum:,} ₸"})
                    d["total_sum"] = new_sum

            task_date = request.form.get("task_date")
            task_type = request.form.get("task_type")
            task_text = request.form.get("task_text", "").strip()
            
            if task_date and task_text:
                if "tasks" not in d: d["tasks"] = []
                task_id = f"t_{len(d['tasks'])+1}_{int(datetime.now().timestamp())}"
                d["tasks"].append({"id": task_id, "date": task_date, "type": task_type, "text": task_text, "done": False, "reminded": False})
                d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"Поставил задачу ({task_type} на {task_date}): {task_text}"})

            if current_user_data["role"] in ["director", "rop"]:
                requested_manager = request.form.get("manager")
                if requested_manager and d["manager"] != requested_manager:
                    d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"Изменил ответственного на: {requested_manager}"})
                    d["manager"] = requested_manager
            
            if d["stage"] != new_stage:
                stage_name = new_stage
                for sk, sn, sc in STAGES:
                    if sk == new_stage: stage_name = sn
                d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"Сменил этап на: {stage_name}"})
                d["stage"] = new_stage
                
            if new_comment:
                d["history"].append({"date": now_str, "author": current_user_data["name"], "text": f"💬 {new_comment}"})
                
            d["title"] = client_name
            d["client"] = client_name
            break
            
    save_db(db)
    return redirect(url_for("index"))

@app.route("/complete_task/<deal_id>/<task_id>", methods=["POST"])
def complete_task(deal_id, task_id):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    today_str = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    for d in db["deals"]:
        if d["id"] == deal_id:
            for t in d.get("tasks", []):
                if t.get("id") == task_id:
                    t["done"] = True
                    task_date = t.get("date", "")
                    if task_date < today_str:
                        history_text = f"✓ Выполнил задачу с просрочкой (план: {task_date}): [{t['type']}] {t['text']}"
                    else:
                        history_text = f"✓ Выполнил задачу вовремя: [{t['type']}] {t['text']}"
                    d["history"].append({"date": now_str, "author": user_data["name"], "text": history_text})
                    break
    save_db(db)
    return redirect(url_for("index"))

@app.route("/remind_task/<deal_id>/<task_id>", methods=["POST"])
def remind_task(deal_id, task_id):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    for d in db["deals"]:
        if d["id"] == deal_id:
            for t in d.get("tasks", []):
                if t.get("id") == task_id:
                    t["reminded"] = True
                    d["history"].append({"date": datetime.now().strftime("%d.%m.%Y %H:%M"), "author": user_data["name"], "text": "⚡ РОП напомнил менеджеру о просроченной задаче!"})
                    break
    save_db(db)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
