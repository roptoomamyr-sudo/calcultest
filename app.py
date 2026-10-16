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

DEFAULT_USERS = {
    "director": {"pass": "dir123", "name": "Уралбаев Жанайдар Абишевич", "role": "director", "position": "Генеральный директор", "phone": "+7 771 054 77 66", "whatsapp": "+7 771 054 77 66", "email": "too.mamyr@mail.ru", "avatar": ""},
    "rop": {"pass": "rop123", "name": "Лемперт Александр Сергеевич", "role": "rop", "position": "Руководитель отдела продаж (РОП)", "phone": "+7 747 689 96 80", "whatsapp": "+7 747 689 96 80", "email": "too.mamyr@mail.ru", "avatar": ""},
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

CONTRACT_STAGES = ["stage_11", "stage_12", "stage_13", "stage_14", "stage_15"]

def load_db():
    default_data = {
        "deals": [],
        "tz_list": [],
        "users": DEFAULT_USERS,
        "chats": [],
        "kp_registry": []
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
            if "users" not in data: data["users"] = DEFAULT_USERS
            if "tz_list" not in data: data["tz_list"] = []
            if "chats" not in data: data["chats"] = []
            if "kp_registry" not in data: data["kp_registry"] = []
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
        body { background: #f8f9fa; font-family: Arial, sans-serif; overflow: hidden; height: 100vh; }
        .wrapper { display: flex; width: 100%; height: 100vh; overflow: hidden; }
        .sidebar { width: 60px; background: #212529; color: #fff; display: flex; flex-direction: column; flex-shrink: 0; transition: width 0.25s ease-in-out; overflow: hidden; white-space: nowrap; z-index: 1000; }
        .sidebar:hover { width: 250px; }
        .sidebar .brand { padding: 15px; font-size: 16px; font-weight: bold; background: #1a1e21; border-bottom: 1px solid #373b3e; text-align: left; }
        .sidebar .menu { padding: 15px 5px; display: flex; flex-direction: column; gap: 8px; flex-grow: 1; overflow-y: auto; }
        .sidebar .menu a { color: #adb5bd; text-decoration: none; padding: 10px 12px; border-radius: 4px; font-size: 13px; display: flex; align-items: center; gap: 12px; transition: 0.2s; }
        .sidebar .menu a:hover, .sidebar .menu a.active { background: #0d6efd; color: #fff; }
        .sidebar .menu a i { font-size: 16px; min-width: 24px; text-align: center; font-style: normal; }
        
        .main-content { flex-grow: 1; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        .top-bar { background: #ffffff; border-bottom: 1px solid #dee2e6; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; height: 60px; flex-shrink: 0; }
        .content-body { flex-grow: 1; display: flex; flex-direction: column; overflow-y: auto; padding: 15px; background: #f8f9fa; }
        
        .kanban-outer { flex-grow: 1; overflow-x: auto; overflow-y: hidden; white-space: nowrap; padding-bottom: 10px; }
        .kanban { display: inline-flex; gap: 12px; height: 100%; align-items: flex-start; }
        .kanban-outer::-webkit-scrollbar { height: 12px; }
        .kanban-outer::-webkit-scrollbar-track { background: #dee2e6; border-radius: 6px; }
        .kanban-outer::-webkit-scrollbar-thumb { background: #0d6efd; border-radius: 6px; }

        .k-col { width: 280px; min-width: 280px; max-width: 280px; background: #e9ecef; border-radius: 6px; display: flex; flex-direction: column; max-height: 100%; white-space: normal; }
        .k-header { padding: 10px; font-weight: bold; font-size: 13px; color: white; border-top-left-radius: 6px; border-top-right-radius: 6px; text-align: center; flex-shrink: 0; }
        .k-body { padding: 8px; overflow-y: auto; flex-grow: 1; min-height: 150px; }
        
        .deal-card { background: #ffffff; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 12px; border: 1px solid #ced4da; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab; transition: 0.15s; }
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
            <a href="/generator" class="{% if active_page == 'generator' %}active{% endif %}"><i>📄</i> <span>Генератор КП</span></a>
            {% if current_user_data.role in ['director', 'rop'] %}
            <a href="/registry" class="{% if active_page == 'registry' %}active{% endif %}"><i>📋</i> <span>Реестр КП</span></a>
            <a href="/analytics" class="{% if active_page == 'analytics' %}active{% endif %}"><i>📈</i> <span>Воронка (Отчеты)</span></a>
            {% endif %}
            <a href="/chat" class="{% if active_page == 'chat' %}active{% endif %}"><i>💬</i> <span>Чат сотрудников</span></a>
        </div>
        
        <div class="p-2 bg-dark border-top border-secondary text-muted small flex-shrink-0">
            <a href="/profile" class="text-white text-decoration-none d-flex align-items-center gap-2 p-2 rounded {% if active_page == 'profile' %}bg-primary text-white{% endif %}">
                <i>👤</i> <span class="text-truncate"><b>{{ current_user_data.name }}</b></span>
            </a>
            <a href="/logout" class="text-danger text-decoration-none d-flex align-items-center gap-2 p-2 mt-1">
                <i>🚪</i> <span>Выйти</span>
            </a>
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
                {% elif active_page == 'generator' %}
                <h5 class="m-0 fw-bold text-secondary">📄 Генератор коммерческих предложений M-CONSTRUCTION</h5>
                {% elif active_page == 'registry' %}
                <h5 class="m-0 fw-bold text-secondary">📋 Общий реестр коммерческих предложений</h5>
                {% elif active_page == 'chat' %}
                <h5 class="m-0 fw-bold text-secondary">💬 Внутренний чат сотрудников</h5>
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

@app.route("/generator")
def generator_page():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    manager_display = f"{user_data.get('position', 'Сотрудник')}: {user_data['name']} ({user_data.get('phone', '+7 700 000 00 00')})"
    user_name_val = user_data['name']
    user_pos_val = user_data.get('position', 'Менеджер')
    user_phone_val = user_data.get('phone', '-')

    # Обычная строка без f-, чтобы JS-код с фигурными скобками не вызывал ошибку у Python
    gen_html = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
    <style>
        .gen-container { max-width: 900px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .section-title { font-size: 13px; font-weight: bold; color: #2b6cb0; margin: 18px 0 8px 0; text-transform: uppercase; letter-spacing: 0.5px; font-family: 'Arial', sans-serif; }
        .form-row { display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 12px; }
        .form-group { flex: 1; min-width: 180px; }
        label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #4a5568; font-family: 'Arial', sans-serif; }
        input, select { width: 100%; padding: 9px 11px; font-size: 14px; border: 1px solid #cbd5e0; border-radius: 6px; font-family: 'Arial', sans-serif; }
        .btn-generate { width: 100%; padding: 14px; background: #2b6cb0; color: #fff; font-size: 16px; font-weight: bold; border: none; border-radius: 8px; cursor: pointer; margin-top: 20px; transition: 0.2s; font-family: 'Arial', sans-serif; }
        .btn-generate:hover { background: #2c5282; }
        
        #pdfTemplateWrapper { position: absolute; left: -9999px; top: 0; width: 210mm; }
        .pdf-page { width: 210mm; height: 296mm; padding: 8mm 12mm 15mm 12mm; background: #fff; font-size: 11pt; color: #000; box-sizing: border-box; position: relative; font-family: 'Calibri', 'Arial', sans-serif; overflow: hidden; page-break-after: always; page-break-inside: avoid; }
        .pdf-header { display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #b8860b; padding-bottom: 4px; margin-bottom: 6px; }
        .pdf-header-text { font-size: 9pt; line-height: 1.15; }
        .kp-title { font-size: 14pt; font-weight: bold; color: #b8860b; text-align: center; margin: 4px 0 6px 0; text-transform: uppercase; }
        .kp-meta { font-size: 10.5pt; margin-bottom: 6px; line-height: 1.25; }
        .kp-table { width: 100%; border-collapse: collapse; margin-bottom: 6px; }
        .kp-table th, .kp-table td { border: 1px solid #000; padding: 4px 6px; font-size: 10.5pt; vertical-align: top; line-height: 1.15; }
        .kp-table th { background: #000; color: #fff; text-align: center; font-weight: bold; text-transform: uppercase; font-size: 9.5pt; }
        .total-row { background: #b8860b; color: #fff; font-weight: bold; font-size: 11pt; }
        .total-row-discount { background: #8b6508; color: #fff; font-weight: bold; font-size: 11pt; }
        .conditions-box { font-size: 9.5pt; line-height: 1.15; margin-top: 6px; }
        .conditions-box h4 { margin: 3px 0 1px 0; font-size: 10pt; text-decoration: underline; }
        .footer-line { position: absolute; bottom: 6mm; left: 12mm; right: 12mm; font-size: 8.5pt; border-top: 1px solid #ccc; padding-top: 4px; text-align: center; color: #222; line-height: 1.15; }
        .feature-box { background: #fff8e7; border-left: 3px solid #b8860b; padding: 6px 8px; margin-bottom: 6px; font-size: 10pt; line-height: 1.2; }
        .feature-title { font-weight: bold; color: #8b6508; margin-bottom: 1px; font-size: 10.5pt; }
        .photo-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 8px; }
        .photo-card { width: 100%; height: 125px; background: #f0f4f8; border: 1px solid #cbd5e0; display: flex; align-items: center; justify-content: center; color: #4a5568; font-size: 10pt; font-weight: bold; text-align: center; overflow: hidden; position: relative; }
    </style>

    <div class="gen-container">
        <div class="alert alert-info py-2 mb-3">
            👤 Ответственный сотрудник (автоматически): <b id="managerDisplayInfo"></b>
        </div>

        <div class="section-title">1. Данные Заказчика</div>
        <div class="form-row">
            <div class="form-group">
                <label>Заказчик (ТОО / ИП / ФИО):</label>
                <input type="text" id="clientName" placeholder="Например: ТОО «Мамыр»" value="ТОО «Мамыр»">
            </div>
            <div class="form-group">
                <label>Контактный телефон:</label>
                <input type="text" id="clientPhone" placeholder="+7 700 000 00 00" value="+7 700 000 00 00">
            </div>
            <div class="form-group">
                <label>WhatsApp для связи:</label>
                <input type="text" id="clientWa" placeholder="+7 700 000 00 00" value="+7 700 000 00 00">
            </div>
            <div class="form-group">
                <label>Назначение объекта:</label>
                <input type="text" id="purpose" placeholder="Например: Зернохранилище" value="Зернохранилище">
            </div>
        </div>

        <div class="section-title">2. Конструкция и покрытие</div>
        <div class="form-row">
            <div class="form-group">
                <label>Тип здания:</label>
                <select id="buildingType">
                    <option value="arch_pvc">Арочный холодный (Тент ПВХ)</option>
                    <option value="straight_arch_pvc">Прямостенный арочный холодный (Тент ПВХ)</option>
                    <option value="straight_gable_prof">Прямостенный двускатный холодный (Профлист)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Ширина (м):</label>
                <input type="number" id="width" value="18" min="10" max="30">
            </div>
            <div class="form-group">
                <label>Длина (м):</label>
                <input type="number" id="length" value="36" min="10" max="150">
            </div>
            <div class="form-group" id="wallHBox" style="display:none;">
                <label>Высота стены (м):</label>
                <input type="number" id="wallH" value="3" min="3" max="10">
            </div>
        </div>

        <div class="section-title">3. Ворота и вентиляция</div>
        <div class="form-row">
            <div class="form-group">
                <label>Размер ворот:</label>
                <select id="gateSize">
                    <option value="4x4">4.0 х 4.0 м</option>
                    <option value="3x3">3.0 х 3.0 м</option>
                    <option value="5x5">5.0 х 5.0 м</option>
                </select>
            </div>
            <div class="form-group">
                <label>Количество ворот (шт):</label>
                <input type="number" id="gateCount" value="2" min="0" max="10">
            </div>
            <div class="form-group">
                <label>Вентиляционные решетки (комплектов):</label>
                <input type="number" id="ventCount" value="2" min="0" max="10">
            </div>
        </div>

        <div class="section-title">4. Работы, Фундамент, Доставка, Скидка и Сроки</div>
        <div class="form-row">
            <div class="form-group">
                <label>Монтажные работы:</label>
                <select id="montageType">
                    <option value="include">Включены (строительная бригада под ключ)</option>
                    <option value="none">Без монтажа (шеф-монтаж / своими силами)</option>
                </select>
            </div>
            <div class="form-group">
                <label>Фундамент:</label>
                <select id="fundType">
                    <option value="strip">Ленточный ж/б монолитный + Сваи + Отмостка</option>
                    <option value="screw">Винтовые сваи</option>
                    <option value="none">Подготовка Заказчика (0 ₸)</option>
                </select>
            </div>
            <div class="form-group" id="stripParamsBox">
                <label>Лента (Ширина x Высота, м):</label>
                <div style="display:flex; gap:5px;">
                    <input type="number" id="fundW" value="0.4" step="0.05">
                    <input type="number" id="fundH" value="1.2" step="0.1">
                </div>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Расстояние от Костаная (км):</label>
                <input type="number" id="distance" value="350" min="0">
            </div>
            <div class="form-group">
                <label>Количество рейсов (машин):</label>
                <input type="number" id="truckCount" value="3" min="1">
            </div>
            <div class="form-group">
                <label>Скидка (%):</label>
                <input type="number" id="discountPercent" value="0" min="0" max="30">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Срок изготовления:</label>
                <input type="text" id="termManufacture" value="30 дней">
            </div>
            <div class="form-group">
                <label>Срок фундаментных работ:</label>
                <input type="text" id="termFoundation" value="20 дней">
            </div>
            <div class="form-group">
                <label>Срок монтажных работ:</label>
                <input type="text" id="termInstallation" value="30 дней">
            </div>
        </div>

        <div class="section-title">5. Фотографии объекта (для 2-й страницы)</div>
        <div class="form-row">
            <div class="form-group"><label>Фото 1 (Снаружи):</label><input type="file" id="imgInput1" accept="image/*" onchange="previewImage(this, 'pdfImg1')"></div>
            <div class="form-group"><label>Фото 2 (Конструктив):</label><input type="file" id="imgInput2" accept="image/*" onchange="previewImage(this, 'pdfImg2')"></div>
        </div>
        <div class="form-row">
            <div class="form-group"><label>Фото 3 (Интерьер):</label><input type="file" id="imgInput3" accept="image/*" onchange="previewImage(this, 'pdfImg3')"></div>
            <div class="form-group"><label>Фото 4 (Готовый объект):</label><input type="file" id="imgInput4" accept="image/*" onchange="previewImage(this, 'pdfImg4')"></div>
        </div>

        <button class="btn-generate" id="btnGen" onclick="generateAndSaveKP()">📄 Сформировать и скачать КП (PDF)</button>
    </div>

    <div id="pdfTemplateWrapper">
        <div id="pdfContent">
            <div class="pdf-page">
                <div class="pdf-header">
                    <div class="pdf-header-text">
                        <b>ЖАУАПКЕРШІЛІГІ ШЕКТЕУЛІ СЕРІКТЕСТІГІ «Мамыр»</b><br>
                        Қазақстан Республикасы 110000, Қостанай облысы, Қостанай қаласы, Узкоколейная көш. 9<br>
                        Тел: +7 771 054 77 66 | E-mail: too.mamyr@mail.ru
                    </div>
                    <div style="text-align:right;">
                        <strong style="font-size:16px; color:#b8860b;">M-CONSTRUCTION</strong><br>
                        <span style="font-size:8pt; color:#555; font-weight:bold;">ТОО «Мамыр»</span>
                    </div>
                </div>
                <div class="kp-title" id="pdfKpNum">КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ</div>
                <div class="kp-meta">
                    <b>Объект:</b> <span id="pdfObjectTitle">Быстровозводимый ангар</span><br>
                    <b>Назначение:</b> <span id="pdfPurpose">Зернохранилище</span>
                </div>
                <table class="kp-table">
                    <thead>
                        <tr>
                            <th style="width: 48%;">Наименование и подробное описание</th>
                            <th style="width: 12%;">Кол-во</th>
                            <th style="width: 20%;">Сумма (₸)</th>
                            <th style="width: 20%;">Примечание</th>
                        </tr>
                    </thead>
                    <tbody id="pdfTableBody"></tbody>
                </table>
                <div class="conditions-box">
                    <h4>Коммерческие условия:</h4>
                    - Цены указаны в тенге с НДС 16%.<br>
                    - 50% предоплата на закуп материалов.<br>
                    - 25% перед отгрузкой готового комплекта ангара.<br>
                    - 25% после подписания АВР и накладной.
                    <h4>Сроки реализации:</h4>
                    - Изготовление МК: <span id="pdfTermMan">30 дней</span> | Фундамент: <span id="pdfTermFound">20 дней</span> | Монтаж: <span id="pdfTermInst">30 дней</span>
                </div>
                <div class="footer-line">
                    <b>ТОО «Мамыр»</b> | Республика Казахстан, 110000, г. Костанай, ул. Узкоколейная, д. 9 | БИН 011240003418<br>
                    Лицензия СМР II категория ГС-2 № 03293 от 15.10.2020 г. | Тел: +7 771 054 77 66
                </div>
            </div>
            <div class="pdf-page">
                <div class="pdf-header">
                    <div class="pdf-header-text"><b>ЖАУАПКЕРШІЛІГІ ШЕКТЕУЛІ СЕРІКТЕСТІГІ «Мамыр»</b></div>
                    <div style="text-align:right;"><strong style="color:#b8860b;">M-CONSTRUCTION</strong></div>
                </div>
                <div class="kp-title" style="margin-bottom:10px;">ТЕХНИЧЕСКИЕ РЕШЕНИЯ И ПРЕИМУЩЕСТВА</div>
                <div class="feature-box"><div class="feature-title">Строительство под ключ</div>Полный цикл: проект, заводское производство, фундамент и монтаж.</div>
                <div class="feature-box"><div class="feature-title">Болтовые соединения</div>Сборка без сварки на объекте, точность геометрии в любую погоду.</div>
                <div class="photo-grid">
                    <div class="photo-card"><img id="pdfImg1" style="display:none; width:100%; height:100%; object-fit:cover;"><span>Снаружи</span></div>
                    <div class="photo-card"><img id="pdfImg2" style="display:none; width:100%; height:100%; object-fit:cover;"><span>Конструктив</span></div>
                    <div class="photo-card"><img id="pdfImg3" style="display:none; width:100%; height:100%; object-fit:cover;"><span>Интерьер</span></div>
                    <div class="photo-card"><img id="pdfImg4" style="display:none; width:100%; height:100%; object-fit:cover;"><span>Готовый объект</span></div>
                </div>
                <div style="margin-top: 20px; font-size: 10.5pt; font-weight: bold;">С уважением,<br><span id="pdfSignManager"></span></div>
                <div class="footer-line"><b>ТОО «Мамыр»</b> | г. Костанай, ул. Узкоколейная, д. 9 | БИН 011240003418</div>
            </div>
        </div>
    </div>

    <script>
        var VAT = 1.16;
        var managerName = "%s (%s, тел: %s)";
        var rawManagerName = "%s";
        var rawManagerPos = "%s";
        var rawManagerPhone = "%s";

        document.getElementById('managerDisplayInfo').innerText = rawManagerPos + ": " + rawManagerName + " (" + rawManagerPhone + ")";

        document.getElementById('buildingType').addEventListener('change', function() {
            document.getElementById('wallHBox').style.display = (this.value.indexOf('straight') !== -1) ? 'block' : 'none';
        });
        document.getElementById('fundType').addEventListener('change', function() {
            document.getElementById('stripParamsBox').style.display = (this.value === 'strip') ? 'block' : 'none';
        });

        function previewImage(input, targetImgId) {
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.onload = function(e) {
                    var img = document.getElementById(targetImgId);
                    img.src = e.target.result;
                    img.style.display = 'block';
                }
                reader.readAsDataURL(input.files[0]);
            }
        }

        function getNum(id, fallback) {
            var el = document.getElementById(id);
            if (!el) return fallback;
            var v = parseFloat(el.value);
            return isNaN(v) ? fallback : v;
        }

        function generateAndSaveKP() {
            var btn = document.getElementById('btnGen');
            btn.disabled = true;
            btn.innerText = "⏳ Формирование PDF...";

            try {
                var client = document.getElementById('clientName').value || 'Заказчик';
                var phone = document.getElementById('clientPhone').value || '—';
                var whatsapp = document.getElementById('clientWa').value || '—';
                var purpose = document.getElementById('purpose').value || 'Ангар';
                
                var type = document.getElementById('buildingType').value;
                var w = getNum('width', 18);
                var l = getNum('length', 36);
                var wallH = getNum('wallH', 3);
                var area = w * l;

                var gateSize = document.getElementById('gateSize').value;
                var gateCount = getNum('gateCount', 0);
                var ventCount = getNum('ventCount', 0);

                var montageType = document.getElementById('montageType').value;
                var fundType = document.getElementById('fundType').value;
                var fundW = getNum('fundW', 0.4);
                var fundH = getNum('fundH', 1.2);

                var distance = getNum('distance', 0);
                var truckCount = getNum('truckCount', 1);
                var discountPercent = getNum('discountPercent', 0);

                var termMan = document.getElementById('termManufacture').value || '30 дней';
                var termFound = document.getElementById('termFoundation').value || '20 дней';
                var termInst = document.getElementById('termInstallation').value || '30 дней';

                var rateNoVat = 0;
                var isProf = false;
                var coverDesc = "";

                if (type === 'arch_pvc') {
                    rateNoVat = (w <= 13) ? 17000 : (w <= 16) ? 19000 : 22000;
                    coverDesc = "Тент ПВХ 900 гр/м²";
                } else if (type === 'straight_arch_pvc') {
                    rateNoVat = (w <= 13) ? 19000 : 25000;
                    coverDesc = "Тент ПВХ 900 гр/м²";
                } else {
                    isProf = true;
                    rateNoVat = (w <= 13) ? 23000 : 26000;
                    coverDesc = "Профнастил Н-44 0.7 мм оцинкованный";
                }

                var heightMult = 1.0;
                if (type.indexOf('straight') !== -1 && wallH > 3) heightMult += (wallH - 3) * 0.03;

                var constPrice = Math.round(area * rateNoVat * heightMult * VAT);
                var singleGate = (gateSize === '3x3') ? 600000 : (gateSize === '5x5') ? 800000 : 700000;
                var gatePrice = singleGate * gateCount;
                var gateW = (gateSize === '3x3') ? 3 : (gateSize === '5x5') ? 5 : 4;
                var ventPrice = ventCount * 58000 * VAT;

                var fundPrice = 0;
                var fundDesc = "";
                var fundNote = "—";

                if (fundType === 'strip') {
                    var P = 2 * (w + l);
                    var netP = Math.max(0, P - (gateW * gateCount));
                    var totalVol = Math.round((netP * fundW * fundH) + ((Math.floor(l / 3) * 2 + 8) * 0.25) + (P * 1.0 * 0.1));
                    fundPrice = Math.round(totalVol * 135000 * VAT);
                    fundDesc = "Ленточный ж/б монолитный Н-" + fundH + "м, В-" + fundW + "м + сваи + отмостка";
                    fundNote = totalVol + " м³";
                } else if (fundType === 'screw') {
                    var P = 2 * (w + l);
                    var screwRate = (w <= 13) ? 22000 : (w <= 17) ? 26000 : (w <= 22) ? 30000 : 34000;
                    fundPrice = Math.round(P * screwRate * VAT);
                    fundDesc = "Свайно-винтовой фундамент";
                    fundNote = P + " п.м.";
                } else {
                    fundDesc = "Подготовка фундамента Заказчиком";
                }

                var montagePrice = (montageType === 'include') ? Math.round((constPrice + gatePrice) * (isProf ? 0.23 : 0.21)) : 0;
                var deliveryPrice = Math.round(distance * 1000 * VAT * truckCount);

                var totalBase = constPrice + gatePrice + ventPrice + fundPrice + montagePrice + deliveryPrice;
                var discountAmount = Math.round(totalBase * (discountPercent / 100));
                var totalFinal = totalBase - discountAmount;
                var kpNum = Math.floor(100 + Math.random() * 900);

                document.getElementById('pdfKpNum').innerText = "КОММЕРЧЕСКОЕ ПРЕДЛОЖЕНИЕ: " + client.toUpperCase();
                document.getElementById('pdfObjectTitle').innerText = "Быстровозводимый ангар " + w.toFixed(1) + " х " + l.toFixed(1) + " м (" + area + " м²)";
                document.getElementById('pdfPurpose').innerText = purpose;
                document.getElementById('pdfTermMan').innerText = termMan;
                document.getElementById('pdfTermFound').innerText = termFound;
                document.getElementById('pdfTermInst').innerText = termInst;

                var rows = "<tr><td><b>Комплект ангара</b> " + w.toFixed(1) + "х" + l.toFixed(1) + "м. Покрытие: " + coverDesc + "</td><td style='text-align:center;'>1 к-т</td><td style='text-align:right;'>" + constPrice.toLocaleString('ru-RU') + "</td><td>Завод</td></tr>";
                if (gateCount > 0) rows += "<tr><td><b>Ворота распашные</b> " + gateW + "х" + gateW + "м</td><td style='text-align:center;'>" + gateCount + " шт</td><td style='text-align:right;'>" + gatePrice.toLocaleString('ru-RU') + "</td><td>—</td></tr>";
                if (ventCount > 0) rows += "<tr><td><b>Вентиляционные решетки</b></td><td style='text-align:center;'>" + ventCount + " к-та</td><td style='text-align:right;'>" + ventPrice.toLocaleString('ru-RU') + "</td><td>—</td></tr>";
                rows += "<tr><td><b>" + fundDesc + "</b></td><td style='text-align:center;'>—</td><td style='text-align:right;'>" + fundPrice.toLocaleString('ru-RU') + "</td><td>" + fundNote + "</td></tr>";
                rows += "<tr><td><b>Монтажные работы</b></td><td style='text-align:center;'>работа</td><td style='text-align:right;'>" + montagePrice.toLocaleString('ru-RU') + "</td><td>Спецтехника</td></tr>";
                rows += "<tr><td><b>Логистика</b> (" + distance + " км)</td><td style='text-align:center;'>" + truckCount + " маш.</td><td style='text-align:right;'>" + deliveryPrice.toLocaleString('ru-RU') + "</td><td>—</td></tr>";
                rows += "<tr class='total-row'><td colspan='2'>ИТОГО С НДС 16%:</td><td style='text-align:right;'>" + totalBase.toLocaleString('ru-RU') + "</td><td>₸</td></tr>";
                if (discountPercent > 0) rows += "<tr class='total-row-discount'><td colspan='2'>ИТОГО СО СКИДКОЙ (" + discountPercent + "%):</td><td style='text-align:right;'>" + totalFinal.toLocaleString('ru-RU') + "</td><td>₸</td></tr>";

                document.getElementById('pdfTableBody').innerHTML = rows;
                document.getElementById('pdfSignManager').innerText = rawManagerPos + ": " + rawManagerName;

                var element = document.getElementById('pdfContent');
                var opt = {
                    margin: 0,
                    filename: 'КП_' + client + '.pdf',
                    image: { type: 'jpeg', quality: 0.98 },
                    html2canvas: { scale: 2, logging: false },
                    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
                };

                html2pdf().set(opt).from(element).save().then(function() {
                    btn.disabled = false;
                    btn.innerText = "📄 Сформировать и скачать КП (PDF)";
                });

                fetch('/save_kp', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        id: "KP-" + kpNum,
                        date: new Date().toLocaleDateString('ru-RU') + " " + new Date().toLocaleTimeString('ru-RU'),
                        manager: rawManagerName,
                        client: client,
                        phone: phone,
                        whatsapp: whatsapp,
                        object: purpose + ' (' + w.toFixed(1) + 'x' + l.toFixed(1) + 'м)',
                        price: totalFinal.toLocaleString('ru-RU') + ' ₸',
                        status: 'sent'
                    })
                });

            } catch (e) {
                alert("Ошибка: " + e.message);
                btn.disabled = false;
                btn.innerText = "📄 Сформировать и скачать КП (PDF)";
            }
        }
    </script>
    """ % (manager_display, user_name_val, user_pos_val, user_phone_val)
    
    return render_template_string(BASE_TEMPLATE, page_title="Генератор КП", active_page="generator", current_user_data=user_data, content=gen_html)

@app.route("/save_kp", methods=["POST"])
def save_kp():
    if "user" not in session: return jsonify({"success": False})
    data = request.get_json()
    if data:
        db = load_db()
        if "kp_registry" not in db: db["kp_registry"] = []
        db["kp_registry"].append(data)
        save_db(db)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/registry")
def registry_page():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    if user_data["role"] not in ["director", "rop"]:
        return "<h3 style='color:red; text-align:center; margin-top:50px;'>⛔ Доступ запрещен! Реестр доступен только РОПу и Директору.</h3><p style='text-align:center;'><a href='/'>Вернуться в CRM</a></p>"

    raw_deals_json = json.dumps(db.get('kp_registry', []), ensure_ascii=False)

    reg_html = """
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <style>
        .reg-container { max-width: 1400px; margin: 0 auto; background: #fff; padding: 25px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
        .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2b6cb0; padding-bottom: 15px; margin-bottom: 20px; flex-wrap: wrap; gap: 10px; }
        .header h1 { color: #1a365d; font-size: 22px; margin: 0; }
        .toolbar { display: flex; justify-content: space-between; align-items: center; background: #edf2f7; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; flex-wrap: wrap; gap: 15px; }
        .filter-group { display: flex; align-items: center; gap: 15px; flex-wrap: wrap; }
        .filter-item { display: flex; align-items: center; gap: 8px; }
        .filter-item label { font-weight: bold; color: #2d3748; font-size: 14px; }
        .filter-item select, .filter-item input { padding: 8px 12px; border-radius: 6px; border: 1px solid #cbd5e0; font-size: 14px; font-weight: bold; background: #fff; }
        .stats-info { font-size: 14px; color: #4a5568; }
        .stats-info b { color: #2b6cb0; font-size: 16px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #cbd5e0; padding: 10px 12px; text-align: left; font-size: 13px; vertical-align: middle; }
        th { background: #1a365d; color: #fff; font-weight: bold; font-size: 12px; text-transform: uppercase; }
        tr:nth-child(even) { background: #f8fafc; }
        .status-badge { display: inline-block; padding: 6px 12px; border-radius: 6px; font-weight: bold; font-size: 12px; text-align: center; background: #e2e8f0; color: #2d3748; }
        .empty-text { text-align: center; color: #718096; padding: 30px; font-style: italic; }
    </style>

    <div class="reg-container">
        <div class="header">
            <h1>Общий управленческий реестр КП</h1>
            <div class="d-flex gap-2">
                <button onclick="exportToExcel()" class="btn btn-success btn-sm fw-bold">📊 Выгрузить в Excel</button>
                <button onclick="location.reload()" class="btn btn-primary btn-sm fw-bold">Обновить</button>
                <button onclick="clearRegistry()" class="btn btn-danger btn-sm fw-bold">🗑️ Очистить реестр</button>
            </div>
        </div>
        <div class="toolbar">
            <div class="filter-group">
                <div class="filter-item">
                    <label>Сотрудник:</label>
                    <select id="managerFilter" onchange="filterTable()">
                        <option value="ALL">-- Все сотрудники --</option>
                        <option value="Лемперт">Лемперт Александр</option>
                        <option value="Уралбаев">Уралбаев Жанайдар</option>
                        <option value="Менеджер 1">Менеджер 1</option>
                        <option value="Менеджер 2">Менеджер 2</option>
                        <option value="Менеджер 3">Менеджер 3</option>
                    </select>
                </div>
                <div class="filter-item">
                    <label>Заказчик:</label>
                    <input type="text" id="clientSearch" placeholder="Поиск по ТОО..." oninput="filterTable()">
                </div>
            </div>
            <div class="stats-info">Всего КП: <b id="totalCount">0</b> шт. | Сумма: <b id="totalSum">0 ₸</b></div>
        </div>
        <div id="tableContainer"></div>
    </div>

    <script>
        var rawDeals = %s;

        function filterTable() {
            var mFilter = document.getElementById('managerFilter').value;
            var q = document.getElementById('clientSearch').value.toLowerCase().trim();

            var filtered = rawDeals.filter(function(d) {
                var matchM = (mFilter === 'ALL') || (d.manager && d.manager.indexOf(mFilter) !== -1);
                var matchQ = !q || (d.client && d.client.toLowerCase().indexOf(q) !== -1);
                return matchM && matchQ;
            });

            var container = document.getElementById('tableContainer');
            var totalSum = 0;

            filtered.forEach(function(d) {
                if (d.price) {
                    var n = parseInt(String(d.price).replace(/\\D/g, ''));
                    if (!isNaN(n)) totalSum += n;
                }
            });

            document.getElementById('totalCount').innerText = filtered.length;
            document.getElementById('totalSum').innerText = totalSum.toLocaleString('ru-RU') + ' ₸';

            if (filtered.length === 0) {
                container.innerHTML = '<div class="empty-text">Коммерческих предложений не найдено.</div>';
                return;
            }

            var html = '<table><thead><tr><th>№ КП</th><th>Дата / Время</th><th>Менеджер</th><th>Заказчик</th><th>Телефон</th><th>WhatsApp</th><th>Объект</th><th>Сумма</th><th>Статус</th></tr></thead><tbody>';
            filtered.forEach(function(d) {
                html += '<tr>' +
                    '<td><b>' + (d.id || '-') + '</b></td>' +
                    '<td>' + (d.date || '-') + '</td>' +
                    '<td><b>' + (d.manager || '-') + '</b></td>' +
                    '<td>' + (d.client || '-') + '</td>' +
                    '<td>' + (d.phone || '-') + '</td>' +
                    '<td>' + (d.whatsapp || '-') + '</td>' +
                    '<td>' + (d.object || '-') + '</td>' +
                    '<td><b>' + (d.price || '-') + '</b></td>' +
                    '<td><span class="status-badge">Создано КП</span></td>' +
                '</tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }

        function clearRegistry() {
            if (confirm('Очистить весь реестр КП?')) {
                fetch('/clear_registry', {method: 'POST'}).then(() => location.reload());
            }
        }

        function exportToExcel() {
            var ws = XLSX.utils.json_to_sheet(rawDeals);
            var wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "Реестр КП");
            XLSX.writeFile(wb, "Реестр_КП_ТОО_Мамыр.xlsx");
        }

        window.onload = filterTable;
    </script>
    """ % raw_deals_json
    
    return render_template_string(BASE_TEMPLATE, page_title="Реестр КП", active_page="registry", current_user_data=user_data, content=reg_html)

@app.route("/clear_registry", methods=["POST"])
def clear_registry():
    if "user" not in session: return jsonify({"success": False})
    db = load_db()
    db["kp_registry"] = []
    save_db(db)
    return jsonify({"success": True})

@app.route("/chat", methods=["GET", "POST"])
@app.route("/chat/<chat_id>", methods=["GET", "POST"])
def chat_page(chat_id=None):
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "create_chat":
            selected_members = request.form.getlist("members")
            selected_members.append(uname)
            selected_members = list(set(selected_members))
            chat_title = request.form.get("title", "").strip() or ", ".join([users[m]["name"] for m in selected_members if m in users])
            new_chat_id = f"chat_{len(db['chats']) + 1}"
            db["chats"].append({"id": new_chat_id, "title": chat_title, "members": selected_members, "messages": []})
            save_db(db)
            return redirect(url_for("chat_page", chat_id=new_chat_id))
        elif action == "send_message" and chat_id:
            msg_text = request.form.get("message", "").strip()
            if msg_text:
                for c in db["chats"]:
                    if c["id"] == chat_id:
                        c["messages"].append({"author_key": uname, "author_name": user_data["name"], "text": msg_text, "time": datetime.now().strftime("%d.%m %H:%M")})
                        break
                save_db(db)
                return redirect(url_for("chat_page", chat_id=chat_id))

    user_chats = [c for c in db.get("chats", []) if uname in c.get("members", [])]
    active_chat = next((c for c in user_chats if c["id"] == chat_id), None)
    
    chat_list_html = "".join([f'<a href="{url_for("chat_page", chat_id=c["id"])}" class="list-group-item list-group-item-action {"active bg-primary text-white" if active_chat and c["id"] == active_chat["id"] else "bg-white"}"><strong>{c["title"]}</strong></a>' for c in user_chats])
    messages_html = "".join([f'<div class="mb-2 {"text-end" if m.get("author_key") == uname else "text-start"}"><div class="d-inline-block p-2 rounded {"bg-primary text-white" if m.get("author_key") == uname else "bg-light border text-dark"}" style="max-width: 70%;"><div class="fw-bold small">{m.get("author_name")}</div><div>{m.get("text")}</div><div class="small opacity-75 text-end mt-1" style="font-size: 10px;">{m.get("time")}</div></div></div>' for m in active_chat.get("messages", [])]) if active_chat else '<div class="text-center text-muted my-auto">Выберите чат или создайте новый диалог</div>'
    members_checkboxes = "".join([f'<div class="form-check"><input class="form-check-input" type="checkbox" name="members" value="{u_k}" id="usr_{u_k}"><label class="form-check-label" for="usr_{u_k}"><b>{u_v["name"]}</b> <span class="text-muted">({u_v.get("position", "")})</span></label></div>' for u_k, u_v in users.items() if u_k != uname])

    content_html = f"""
    <div class="container-fluid h-100 p-0">
        <div class="row g-0 h-100">
            <div class="col-md-4 border-end bg-white d-flex flex-column h-100">
                <div class="p-3 border-bottom d-flex justify-content-between align-items-center"><h6 class="m-0 fw-bold">💬 Ваши диалоги</h6><button class="btn btn-primary btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#newChatModal">+ Новый чат</button></div>
                <div class="list-group list-group-flush overflow-auto flex-grow-1">{chat_list_html or '<div class="p-3 text-muted text-center">Чатов пока нет</div>'}</div>
            </div>
            <div class="col-md-8 d-flex flex-column h-100 bg-light">
                {f'''<div class="p-3 border-bottom bg-white fw-bold">{active_chat["title"]}</div><div class="p-3 overflow-auto flex-grow-1 d-flex flex-column">{messages_html}</div><div class="p-3 bg-white border-top"><form method="POST"><input type="hidden" name="action" value="send_message"><div class="input-group"><input type="text" name="message" class="form-control" placeholder="Напишите сообщение..." required autofocus><button type="submit" class="btn btn-primary fw-bold">Отправить</button></div></form></div>''' if active_chat else f'<div class="d-flex h-100 align-items-center justify-content-center text-muted">{messages_html}</div>'}
            </div>
        </div>
    </div>
    <div class="modal fade" id="newChatModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content"><form method="POST"><input type="hidden" name="action" value="create_chat"><div class="modal-header bg-primary text-white"><h5 class="modal-title fw-bold">👥 Создать чат</h5><button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button></div><div class="modal-body"><div class="mb-3"><label class="form-label fw-bold">Название чата:</label><input type="text" name="title" class="form-control" placeholder="Обсуждение объекта..."></div><label class="form-label fw-bold">Выберите сотрудников:</label><div class="p-2 border rounded bg-light" style="max-height: 200px; overflow-y: auto;">{members_checkboxes}</div></div><div class="modal-footer"><button type="submit" class="btn btn-primary fw-bold">Создать чат</button></div></form></div></div></div>
    """
    return render_template_string(BASE_TEMPLATE, page_title="Чат сотрудников", active_page="chat", current_user_data=user_data, content=content_html)

@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    uname = session["user"]
    db = load_db()
    users = db.get("users", DEFAULT_USERS)
    user_data = users[uname]
    
    search_query = request.args.get("q", "").strip().lower()
    
