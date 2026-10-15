from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "angar_crm_secret_2026"

DB_FILE = "crm_db.json"

USERS = {
    "director": {"pass": "dir123", "name": "Уралбаев Ж.А. (Директор)", "role": "director"},
    "rop": {"pass": "rop123", "name": "Лемперт А.С. (РОП)", "role": "rop"},
    "manager1": {"pass": "man123", "name": "Менеджер 1", "role": "manager"},
    "manager2": {"pass": "man223", "name": "Менеджер 2", "role": "manager"}
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

def load_db():
    default_data = {
        "deals": [
            {
                "id": "1",
                "title": 'ТОО "МИРАМ"',
                "client": 'ТОО "МИРАМ"',
                "director": "Иванов И.И.",
                "phones": ["+7 705 626 54 24"],
                "contact_person": "Бухгалтер Светлана",
                "contact_phone": "+7 701 999 88 77",
                "email": "miram@mail.kz",
                "region": "Костанайская область, п. Заречный",
                "stage": "stage_5",
                "manager": "Менеджер 1",
                "total_sum": 0,
                "history": [{"date": "15.10.2026 12:00", "author": "РОП", "text": "Создана сделка, скинул КП"}],
                "tasks": []
            }
        ],
        "tz_list": [
            {
                "id": "tz_1",
                "client": 'ТОО "МИРАМ"',
                "parameters": "Арочный ангар 20х50х8м, утепленный, с двумя воротными проемами",
                "author": "Менеджер 1",
                "responsible": "Инженер ПТО",
                "rop": "Лемперт А.С. (РОП)",
                "director": "Уралбаев Ж.А. (Директор)",
                "status": "В работе",
                "date": "15.10.2026"
            }
        ]
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
            if "tz_list" not in data:
                data["tz_list"] = []
            return data
    except:
        save_db(default_data)
        return default_data

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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
        .wrapper { display: flex; width: 100%; height: 100vh; }
        .sidebar { width: 240px; background: #212529; color: #fff; display: flex; flex-direction: column; flex-shrink: 0; }
        .sidebar .brand { padding: 15px; font-size: 16px; font-weight: bold; background: #1a1e21; border-bottom: 1px solid #373b3e; text-align: center; }
        .sidebar .menu { padding: 15px 10px; display: flex; flex-direction: column; gap: 8px; flex-grow: 1; }
        .sidebar .menu a { color: #adb5bd; text-decoration: none; padding: 10px 12px; border-radius: 4px; font-size: 13px; transition: 0.2s; }
        .sidebar .menu a:hover, .sidebar .menu a.active { background: #0d6efd; color: #fff; }
        .main-content { flex-grow: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        .top-bar { background: #ffffff; border-bottom: 1px solid #dee2e6; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; height: 60px; flex-shrink: 0; }
        .content-body { flex-grow: 1; overflow-y: auto; padding: 15px; background: #f8f9fa; }
        .kanban { display: flex; overflow-x: auto; gap: 12px; height: 100%; padding-bottom: 10px; }
        .k-col { min-width: 280px; max-width: 280px; background: #e9ecef; border-radius: 6px; display: flex; flex-direction: column; max-height: 100%; }
        .k-header { padding: 10px; font-weight: bold; font-size: 13px; color: white; border-top-left-radius: 6px; border-top-right-radius: 6px; text-align: center; }
        .k-body { padding: 8px; overflow-y: auto; flex-grow: 1; min-height: 200px; }
        .deal-card { background: #ffffff; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 12px; border: 1px solid #ced4da; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab; transition: 0.15s; }
        .deal-card:active { cursor: grabbing; opacity: 0.7; }
        .deal-card:hover { border-color: #0d6efd; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
        .history-box { background: #f1f3f5; border-radius: 4px; padding: 8px; max-height: 130px; overflow-y: auto; font-size: 11px; }
        .drag-over { background-color: #d0e1fd !important; border: 2px dashed #0d6efd; }
    </style>
</head>
<body>

<div class="wrapper">
    <!-- Левая панель навигации -->
    <div class="sidebar">
        <div class="brand">🏗️ Ангар CRM</div>
        <div class="menu">
            <a href="/" class="{% if active_page == 'kanban' %}active{% endif %}">📊 Канбан CRM</a>
            <a href="/tz" class="{% if active_page == 'tz' %}active{% endif %}">📐 Технические задания</a>
            {% if user.role in ['director', 'rop'] %}
            <a href="/analytics" class="{% if active_page == 'analytics' %}active{% endif %}">📈 Воронка продаж (Отчеты)</a>
            {% endif %}
        </div>
        <div class="p-3 bg-dark border-top border-secondary text-muted small">
            <div>👤 {{ user.name }}</div>
            <a href="/logout" class="text-danger text-decoration-none mt-1 d-inline-block">🚪 Выйти</a>
        </div>
    </div>

    <!-- Основная рабочая область -->
    <div class="main-content">
        <div class="top-bar">
            <div class="d-flex align-items-center gap-3">
                {% if active_page == 'kanban' %}
                <h5 class="m-0 fw-bold text-secondary">🗂️ Воронка продаж</h5>
                <button class="btn btn-success btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить сделку</button>
                {% elif active_page == 'tz' %}
                <h5 class="m-0 fw-bold text-secondary">📐 Технические задания на расчет ангаров</h5>
                <button class="btn btn-primary btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addTzModal">+ Создать ТЗ</button>
                {% else %}
                <h5 class="m-0 fw-bold text-secondary">📈 Управленческая воронка и аналитика</h5>
                {% endif %}
            </div>
            <div class="d-flex align-items-center gap-3">
                {% if active_page == 'kanban' %}
                <button class="btn btn-warning btn-sm fw-bold text-dark" data-bs-toggle="modal" data-bs-target="#tasksListModal">
                    🔔 Задачи <span class="badge bg-primary ms-1">{{ total_tasks_count }}</span>
                    {% if overdue_count > 0 %}
                    <span class="badge bg-danger ms-1">⚠️ Просрочено: {{ overdue_count }}</span>
                    {% endif %}
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
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u in USERS and USERS[u]["pass"] == p:
            session["user"] = u
            return redirect(url_for("index"))
        error = "Неверный логин или пароль"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    total_tasks = 0
    overdue_count = 0
    
    for d in db["deals"]:
        for t in d.get("tasks", []):
            if not t.get("done", False):
                total_tasks += 1
                if t.get("date", "") < today_str:
                    overdue_count += 1
                    
    # Генерация карточек и модалок для канбана
    kanban_content = """
    <div class="kanban">
    """
    
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
                region_text = d.get('region') or 'Регион не указан'
                dir_text = d.get('director') or 'Не указан'
                phone_text = d.get('phones')[0] if d.get('phones') else 'Нет телефона'
                sum_val = d.get('total_sum', 0)
                sum_str = "{:,}".format(sum_val).replace(",", " ") if sum_val > 0 else "—"
                manager_text = d.get('manager') or 'Не назначен'
                
                tasks_badge = ""
                for t in d.get("tasks", []):
                    if not t.get("done"):
                        if t.get("date") < today_str:
                            tasks_badge += f'<div class="mt-1"><span class="badge bg-danger">⚠️ Просрочено: {t.get("date")}</span></div>'
                        else:
                            tasks_badge += f'<div class="mt-1"><span class="badge bg-warning text-dark">⏰ {t.get("date")}</span></div>'

                kanban_content += f"""
                <div class="deal-card" id="card-{d['id']}" draggable="true" ondragstart="dragDeal(event, '{d['id']}')" data-bs-toggle="modal" data-bs-target="#cardModal{d['id']}">
                    <div class="fw-bold text-primary mb-1" style="font-size: 13px;">{d['title']}</div>
                    <div class="text-muted text-truncate">📍 {region_text}</div>
                    <div class="text-secondary text-truncate">👤 Директор: {dir_text}</div>
                    <div class="text-dark text-truncate">📞 {phone_text}</div>
                    {tasks_badge}
                    <div class="mt-2 pt-1 border-top d-flex justify-content-between text-muted" style="font-size: 11px;">
                        <span>Сумма: {sum_str} ₸</span>
                        <span class="badge bg-light text-dark border">{manager_text}</span>
                    </div>
                </div>

                <!-- Модалка карточки -->
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
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">ТОО / КХ:</label>
                                            <input type="text" name="client" class="form-control" value="{d['client']}" required>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Расположение:</label>
                                            <input type="text" name="region" class="form-control" value="{d.get('region', '')}">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">ФИО Директора:</label>
                                            <input type="text" name="director" class="form-control" value="{d.get('director', '')}">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Email:</label>
                                            <input type="email" name="email" class="form-control" value="{d.get('email', '')}">
                                        </div>
                                        <div class="col-md-12">
                                            <label class="form-label fw-bold">Телефоны:</label>
                                            <div id="phones-container-{d['id']}">
                """
                for ph in d.get("phones", []):
                    kanban_content += f"""
                    <div class="input-group mb-2">
                        <input type="text" name="phones" class="form-control" value="{ph}">
                        <button type="button" class="btn btn-outline-danger" onclick="this.parentElement.remove()">Удалить</button>
                    </div>
                    """
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
                if user["role"] in ["director", "rop"]:
                    kanban_content += f"""
                    <select name="manager" class="form-select">
                        <option value="Не назначен" {'selected' if d.get('manager')=='Не назначен' else ''}>Не назначен</option>
                        <option value="Менеджер 1" {'selected' if d.get('manager')=='Менеджер 1' else ''}>Менеджер 1</option>
                        <option value="Менеджер 2" {'selected' if d.get('manager')=='Менеджер 2' else ''}>Менеджер 2</option>
                        <option value="Уралбаев Ж.А. (Директор)" {'selected' if d.get('manager')=='Уралбаев Ж.А. (Директор)' else ''}>Уралбаев Ж.А. (Директор)</option>
                        <option value="Лемперт А.С. (РОП)" {'selected' if d.get('manager')=='Лемперт А.С. (РОП)' else ''}>Лемперт А.С. (РОП)</option>
                    </select>
                    """
                else:
                    kanban_content += f"""
                    <input type="text" class="form-control bg-light" value="{d.get('manager', '')}" readonly>
                    <input type="hidden" name="manager" value="{d.get('manager', '')}">
                    """

                kanban_content += f"""
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Сумма сделки (₸):</label>
                                            <input type="number" name="total_sum" class="form-control" value="{d.get('total_sum', 0)}">
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
                                            <label class="form-label fw-bold text-success">+ Комментарий:</label>
                                            <textarea name="new_comment" class="form-control" rows="2"></textarea>
                                        </div>
                                        <div class="col-12">
                                            <label class="form-label fw-bold text-secondary">📜 История:</label>
                                            <div class="history-box">
                """
                for h in reversed(d.get("history", [])):
                    kanban_content += f"""
                    <div class="mb-1 border-bottom pb-1">
                        <span class="text-primary fw-bold">[{h.get('date')}] {h.get('author')}:</span> 
                        <span>{h.get('text')}</span>
                    </div>
                    """
                kanban_content += f"""
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                                    <button type="submit" class="btn btn-primary">Сохранить</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
                """
        
        kanban_content += """
            </div>
        </div>
        """
    
    kanban_content += "</div>"
    
    # Модалка задач
    kanban_content += """
    <div class="modal fade" id="tasksListModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-warning text-dark">
                    <h5 class="modal-title fw-bold">🔔 Панель задач и контроля</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="list-group">
    """
    for d in db["deals"]:
        for t in d.get("tasks", []):
            if not t.get("done", False):
                is_overdue = t.get("date") < today_str
                badge_class = "list-group-item-danger" if is_overdue else ""
                date_badge = f'<span class="badge bg-danger">⚠️ Просрочено ({t.get("date")})</span>' if is_overdue else f'<span class="badge bg-primary">{t.get("date")}</span>'
                
                remind_btn = ""
                if user["role"] in ["director", "rop"] and is_overdue:
                    remind_btn = f'''
                    <form method="POST" action="/remind_task/{d['id']}/{t['id']}">
                        <button type="submit" class="btn btn-danger btn-sm fw-bold">⚡ Напомнить</button>
                    </form>
                    '''
                
                kanban_content += f'''
                <div class="list-group-item d-flex justify-content-between align-items-center {badge_class}">
                    <div>
                        {date_badge}
                        <span class="badge bg-dark">{t.get("type")}</span>
                        <strong class="ms-2">{d['client']}</strong>
                        <div class="small mt-1">{t.get("text")}</div>
                        <div class="small text-muted mt-1">Ответственный: <b>{d.get('manager')}</b></div>
                    </div>
                    <div class="d-flex gap-2">
                        <form method="POST" action="/complete_task/{d['id']}/{t['id']}">
                            <button type="submit" class="btn btn-success btn-sm fw-bold">✓ Выполнил</button>
                        </form>
                        {remind_btn}
                    </div>
                </div>
                '''
    kanban_content += """
                    </div>
                </div>
            </div>
        </div>
    </div>
    """

    # Модалка добавления сделки
    stages_options = "".join([f'<option value="{sk}">{sn}</option>' for sk, sn, sc in STAGES])
    kanban_content += f"""
    <div class="modal fade" id="addModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <form method="POST" action="/add">
                    <div class="modal-header bg-success text-white">
                        <h5 class="modal-title fw-bold">➕ Новая сделка</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row g-3">
                            <div class="col-md-6"><label class="form-label fw-bold">ТОО / КХ:</label><input type="text" name="client" class="form-control" required placeholder="ТОО Агро"></div>
                            <div class="col-md-6">
                                <label class="form-label fw-bold">Этап:</label>
                                <select name="stage" class="form-select">{stages_options}</select>
                            </div>
                            <div class="col-md-6">
                                <label class="form-label fw-bold">Ответственный:</label>
                                <select name="manager" class="form-select">
                                    <option value="{user['name']}">{user['name']}</option>
                                    <option value="Менеджер 1">Менеджер 1</option>
                                    <option value="Менеджер 2">Менеджер 2</option>
                                    <option value="Уралбаев Ж.А. (Директор)">Уралбаев Ж.А. (Директор)</option>
                                    <option value="Лемперт А.С. (РОП)">Лемперт А.С. (РОП)</option>
                                </select>
                            </div>
                            <div class="col-md-6"><label class="form-label fw-bold">Расположение:</label><input type="text" name="region" class="form-control"></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Директор:</label><input type="text" name="director" class="form-control"></div>
                            <div class="col-md-6"><label class="form-label fw-bold">Email:</label><input type="email" name="email" class="form-control"></div>
                            <div class="col-12">
                                <label class="form-label fw-bold">Телефон:</label>
                                <div id="new-phones-container"><div class="input-group mb-2"><input type="text" name="phones" class="form-control" placeholder="+7..."></div></div>
                                <button type="button" class="btn btn-outline-secondary btn-sm" onclick="addPhoneField('new-phones-container')">+ Телефон</button>
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer"><button type="submit" class="btn btn-success">Создать</button></div>
                </form>
            </div>
        </div>
    </div>
    """
    
    return render_template_string(BASE_TEMPLATE, page_title="Воронка продаж", active_page="kanban", user=user, total_tasks_count=total_tasks, overdue_count=overdue_count, content=kanban_content)

@app.route("/tz")
def tz_page():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    
    tz_content = """
    <div class="container-fluid p-3">
        <div class="card shadow-sm border-0">
            <div class="card-body">
                <table class="table table-hover align-middle">
                    <thead class="table-dark">
                        <tr>
                            <th>Клиент / ТОО</th>
                            <th>Параметры ангара (ТЗ)</th>
                            <th>Менеджер</th>
                            <th>Инженер (Ответственный)</th>
                            <th>Наблюдатели</th>
                            <th>Статус</th>
                            <th>Дата</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    if db.get("tz_list"):
        for tz in db["tz_list"]:
            tz_content += f"""
            <tr>
                <td class="fw-bold text-primary">{tz['client']}</td>
                <td>{tz['parameters']}</td>
                <td><span class="badge bg-secondary">{tz['author']}</span></td>
                <td><span class="badge bg-info text-dark">{tz['responsible']}</span></td>
                <td class="small text-muted">РОП: {tz['rop']}<br>Директор: {tz['director']}</td>
                <td><span class="badge bg-warning text-dark">{tz['status']}</span></td>
                <td class="small">{tz['date']}</td>
            </tr>
            """
    else:
        tz_content += '<tr><td colspan="7" class="text-center text-muted py-4">Технические задания пока не создавались.</td></tr>'
        
    tz_content += """
                    </tbody>
                </table>
            </div>
        </div>

        <div class="modal fade" id="addTzModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <form method="POST" action="/tz/add">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title fw-bold">📐 Новое техническое задание на расчет ангара</h5>
                            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <label class="form-label fw-bold">Клиент / ТОО:</label>
                                    <input type="text" name="client" class="form-control" required placeholder="ТОО Агро">
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label fw-bold">Ответственный за расчет (Инженер ПТО):</label>
                                    <select name="responsible" class="form-select">
                                        <option value="Инженер ПТО (Иван)">Инженер ПТО (Иван)</option>
                                        <option value="Главный конструктор">Главный конструктор</option>
                                    </select>
                                </div>
                                <div class="col-12">
                                    <label class="form-label fw-bold">Параметры ангара (размеры, утепление, тип каркаса):</label>
                                    <textarea name="parameters" class="form-control" rows="3" required placeholder="Например: Прямостенный ангар 24х60х7м..."></textarea>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label text-muted small">Наблюдатель (РОП):</label>
                                    <input type="text" class="form-control form-control-sm bg-light" value="Лемперт А.С. (РОП)" readonly>
                                </div>
                                <div class="col-md-6">
                                    <label class="form-label text-muted small">Наблюдатель (Директор):</label>
                                    <input type="text" class="form-control form-control-sm bg-light" value="Уралбаев Ж.А. (Директор)" readonly>
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Отмена</button>
                            <button type="submit" class="btn btn-primary btn-sm fw-bold">Отправить в ПТО</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE, page_title="Технические задания", active_page="tz", user=user, content=tz_content)

@app.route("/tz/add", methods=["POST"])
def add_tz():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    if "tz_list" not in db: db["tz_list"] = []
    
    db["tz_list"].append({
        "id": f"tz_{len(db['tz_list'])+1}",
        "client": request.form.get("client"),
        "parameters": request.form.get("parameters"),
        "author": user["name"],
        "responsible": request.form.get("responsible"),
        "rop": "Лемперт А.С. (РОП)",
        "director": "Уралбаев Ж.А. (Директор)",
        "status": "В работе",
        "date": datetime.now().strftime("%d.%m.%Y %H:%M")
    })
    save_db(db)
    return redirect(url_for("tz_page"))

@app.route("/analytics")
def analytics_page():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    if user["role"] not in ["director", "rop"]:
        return "<h3 style='color:red; text-align:center; margin-top:50px;'>⛔ Доступ запрещен! Эта страница доступна только РОПу и Директору.</h3><p style='text-align:center;'><a href='/'>Вернуться в CRM</a></p>"
    
    db = load_db()
    total_deals = len(db["deals"])
    total_contract_sum = sum(d.get("total_sum", 0) for d in db["deals"])
    total_tz = len(db.get("tz_list", []))
    sum_formatted = "{:,}".format(total_contract_sum).replace(",", " ")
    
    analytics_content = f"""
    <div class="container-fluid p-4">
        <div class="row g-3">
            <div class="col-md-4">
                <div class="card shadow-sm border-0 bg-primary text-white p-3">
                    <h5>📊 Всего сделок в работе</h5>
                    <h3>{total_deals}</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card shadow-sm border-0 bg-success text-white p-3">
                    <h5>💰 Сумма по договорам</h5>
                    <h3>{sum_formatted} ₸</h3>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card shadow-sm border-0 bg-warning text-dark p-3">
                    <h5>📐 Активных ТЗ в ПТО</h5>
                    <h3>{total_tz}</h3>
                </div>
            </div>
        </div>
        <div class="card shadow-sm border-0 mt-4 p-4">
            <h5 class="fw-bold text-secondary">📈 Управленческий срез по воронке</h5>
            <p class="text-muted">Контроль конверсии и финансовых потоков строительства ангаров по регионам и менеджерам.</p>
        </div>
    </div>
    """
    return render_template_string(BASE_TEMPLATE, page_title="Аналитика", active_page="analytics", user=user, content=analytics_content)

@app.route("/move_deal", methods=["POST"])
def move_deal():
    if "user" not in session: return jsonify({"success": False})
    user = USERS[session["user"]]
    data = request.get_json()
    deal_id = data.get("id")
    target_stage = data.get("stage")
    
    db = load_db()
    for d in db["deals"]:
        if d["id"] == deal_id:
            old_stage = d["stage"]
            if old_stage != target_stage:
                stage_name = target_stage
                for sk, sn, sc in STAGES:
                    if sk == target_stage: stage_name = sn
                
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
                d["stage"] = target_stage
                d["history"].append({"date": now_str, "author": user["name"], "text": f"Перетащил карточку на этап: {stage_name}"})
                save_db(db)
                return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    
    client_name = request.form.get("client")
    selected_stage = request.form.get("stage", "stage_1")
    selected_manager = request.form.get("manager", user["name"])
    director = request.form.get("director", "").strip()
    phones = [p.strip() for p in request.form.getlist("phones") if p.strip()]
    region = request.form.get("region", "").strip()
    email = request.form.get("email", "").strip()
    
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    db["deals"].append({
        "id": str(len(db["deals"]) + 1),
        "title": client_name,
        "client": client_name,
        "director": director,
        "phones": phones,
        "email": email,
        "region": region,
        "stage": selected_stage,
        "manager": selected_manager,
        "total_sum": 0,
        "history": [{"date": now_str, "author": user["name"], "text": f"Создана новая заявка"}],
        "tasks": []
    })
    save_db(db)
    return redirect(url_for("index"))

@app.route("/update/<id>", methods=["POST"])
def update(id):
    if "user" not in session: return redirect(url_for("login"))
    current_user = USERS[session["user"]]
    db = load_db()
    
    for d in db["deals"]:
        if d["id"] == id:
            client_name = request.form.get("client")
            new_stage = request.form.get("stage")
            new_sum = int(request.form.get("total_sum") or 0)
            new_comment = request.form.get("new_comment", "").strip()
            
            d["director"] = request.form.get("director", "").strip()
            d["phones"] = [p.strip() for p in request.form.getlist("phones") if p.strip()]
            d["region"] = request.form.get("region", "").strip()
            d["email"] = request.form.get("email", "").strip()
            
            task_date = request.form.get("task_date")
            task_type = request.form.get("task_type")
            task_text = request.form.get("task_text", "").strip()
            
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            if task_date and task_text:
                if "tasks" not in d: d["tasks"] = []
                task_id = f"t_{len(d['tasks'])+1}_{int(datetime.now().timestamp())}"
                d["tasks"].append({"id": task_id, "date": task_date, "type": task_type, "text": task_text, "done": False, "reminded": False})
                d["history"].append({"date": now_str, "author": current_user["name"], "text": f"Поставил задачу ({task_type} на {task_date}): {task_text}"})

            if current_user["role"] in ["director", "rop"]:
                requested_manager = request.form.get("manager")
                if requested_manager: d["manager"] = requested_manager
            
            if d["stage"] != new_stage:
                stage_name = new_stage
                for sk, sn, sc in STAGES:
                    if sk == new_stage: stage_name = sn
                d["history"].append({"date": now_str, "author": current_user["name"], "text": f"Сменил этап на: {stage_name}"})
                d["stage"] = new_stage
                
            if d["total_sum"] != new_sum:
                d["history"].append({"date": now_str, "author": current_user["name"], "text": f"Изменил сумму на: {new_sum:,} ₸"})
                d["total_sum"] = new_sum
                
            if new_comment:
                d["history"].append({"date": now_str, "author": current_user["name"], "text": new_comment})
                
            d["title"] = client_name
            d["client"] = client_name
            break
            
    save_db(db)
    return redirect(url_for("index"))

@app.route("/complete_task/<deal_id>/<task_id>", methods=["POST"])
def complete_task(deal_id, task_id):
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
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
                    d["history"].append({"date": now_str, "author": user["name"], "text": history_text})
                    break
    save_db(db)
    return redirect(url_for("index"))

@app.route("/remind_task/<deal_id>/<task_id>", methods=["POST"])
def remind_task(deal_id, task_id):
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    for d in db["deals"]:
        if d["id"] == deal_id:
            for t in d.get("tasks", []):
                if t.get("id") == task_id:
                    t["reminded"] = True
                    d["history"].append({"date": datetime.now().strftime("%d.%m.%Y %H:%M"), "author": user["name"], "text": "⚡ РОП напомнил менеджеру о просроченной задаче!"})
                    break
    save_db(db)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
