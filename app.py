from flask import Flask, render_template_string, request, redirect, url_for, session
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
    ("new", "1. Новая заявка"),
    ("contact", "2. Установлен контакт"),
    ("tz", "3. Сбор ТЗ"),
    ("calc", "4. Расчет"),
    ("kp", "5. КП"),
    ("negotiation", "6. Переговоры"),
    ("contract", "7. Договор"),
    ("prepay_wait", "8. Ждем предоплату"),
    ("production", "9. В производстве"),
    ("delivery", "10. Доставка"),
    ("mounting", "11. Монтаж"),
    ("final_wait", "12. Выполнен"),
    ("paid", "13. Оплачен"),
    ("closed_lost", "14. Закрыто")
]

def load_db():
    if not os.path.exists(DB_FILE):
        data = {
            "deals": [
                {
                    "id": "1",
                    "title": "Ангар 20х50",
                    "client": "ИП Иванов",
                    "phone": "+77015553322",
                    "stage": "production",
                    "manager": "Менеджер 1",
                    "total_sum": 15000000,
                    "prepay": 5000000,
                    "second_pay": 5000000,
                    "final_pay": 0,
                    "comments": [{"time": "15.10.2026 10:30", "author": "Лемперт А.С. (РОП)", "text": "Запуск в цех"}]
                }
            ],
            "tasks": [
                {
                    "id": "1",
                    "title": "Проверить чертежи",
                    "creator": "Лемперт А.С. (РОП)",
                    "responsible": "Уралбаев Ж.А. (Директор)",
                    "observer": "Лемперт А.С. (РОП)",
                    "deadline": "2026-10-20",
                    "status": "active"
                }
            ]
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"deals": [], "tasks": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

LOGIN_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход в CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark d-flex align-items-center justify-content-center vh-100">
<form method="POST" class="card p-4 shadow" style="width: 320px;">
    <h3 class="mb-3 text-center">Вход в CRM</h3>
    {% if error %}
    <div class="alert alert-danger py-1">{{ error }}</div>
    {% endif %}
    <div class="mb-3">
        <label>Логин:</label>
        <input type="text" name="username" class="form-control" required autofocus>
    </div>
    <div class="mb-3">
        <label>Пароль:</label>
        <input type="password" name="password" class="form-control" required>
    </div>
    <button type="submit" class="btn btn-primary w-100">Войти</button>
</form>
</body>
</html>
"""

INDEX_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Ангар CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background: #f4f6f9; font-family: sans-serif; }
        .kanban { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 20px; }
        .k-col { min-width: 260px; background: #e2e8f0; border-radius: 6px; padding: 10px; max-height: 80vh; overflow-y: auto; }
        .card-deal { background: white; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 13px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
<nav class="navbar navbar-dark bg-dark px-3 py-2 d-flex justify-content-between">
    <a class="navbar-brand fw-bold" href="/"><i class="fa-solid fa-industry"></i> Ангар CRM | РОП: Лемперт А.С.</a>
    <div class="text-white">
        <span>{{ user.name }}</span> | <a href="/logout" class="text-warning text-decoration-none">Выйти</a>
    </div>
</nav>
<div class="container-fluid mt-2">
    <ul class="nav nav-tabs">
        <li class="nav-item"><a class="nav-link active" href="/">Воронка</a></li>
        <li class="nav-item"><a class="nav-link" href="/tasks">Задачи</a></li>
        {% if user.role in ['director', 'rop'] %}
        <li class="nav-item"><a class="nav-link" href="/analytics">Аналитика</a></li>
        {% endif %}
        <li class="nav-item"><a class="nav-link" href="/calculator">Калькулятор и КП</a></li>
    </ul>
</div>

<div class="container-fluid mt-3">
    <div class="mb-3 d-flex gap-2">
        <button class="btn btn-success btn-sm" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить клиента</button>
        <form method="GET">
            <select name="manager_filter" class="form-select form-select-sm" onchange="this.form.submit()">
                <option value="">Все менеджеры</option>
                {% for m in managers %}
                <option value="{{ m }}" {% if f_man == m %}selected{% endif %}>{{ m }}</option>
                {% endfor %}
            </select>
        </form>
    </div>

    <div class="kanban">
    {% for s_key, s_name in stages %}
        <div class="k-col">
            <h6 class="fw-bold text-secondary">{{ s_name }}</h6>
            {% for d in deals %}
                {% if d.stage == s_key %}
                <div class="card-deal border-start border-3 border-primary">
                    <div class="fw-bold text-primary">{{ d.title }}</div>
                    <div>Клиент: {{ d.client }}</div>
                    <div>Сумма: {{ d.total_sum }} ₸</div>
                    <div class="text-muted small mt-1">Отв: {{ d.manager or 'Не назначен' }}</div>
                    <button class="btn btn-outline-primary btn-sm w-100 mt-2 py-0" data-bs-toggle="modal" data-bs-target="#m{{ d.id }}">Открыть</button>
                </div>

                <div class="modal fade" id="m{{ d.id }}" tabindex="-1"><div class="modal-dialog"><div class="modal-content">
                    <form method="POST" action="/update/{{ d.id }}">
                        <div class="modal-header"><h5 class="modal-title">{{ d.title }}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
                        <div class="modal-body">
                            <div class="mb-2"><label>Объект:</label><input type="text" name="title" class="form-control" value="{{ d.title }}"></div>
                            <div class="mb-2"><label>Клиент:</label><input type="text" name="client" class="form-control" value="{{ d.client }}"></div>
                            <div class="mb-2"><label>Этап:</label>
                                <select name="stage" class="form-select">
                                    {% for sk, sv in stages %}<option value="{{ sk }}" {% if d.stage == sk %}selected{% endif %}>{{ sv }}</option>{% endfor %}
                                </select>
                            </div>
                            <div class="mb-2"><label>Сумма:</label><input type="number" name="total_sum" class="form-control" value="{{ d.total_sum }}"></div>
                        </div>
                        <div class="modal-footer"><button type="submit" class="btn btn-primary">Сохранить</button></div>
                    </form>
                </div></div></div>
                {% endif %}
            {% endfor %}
        </div>
    {% endfor %}
    </div>
</div>

<div class="modal fade" id="addModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content">
    <form method="POST" action="/add">
        <div class="modal-header"><h5>Новый клиент</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
            <div class="mb-2"><label>Объект:</label><input type="text" name="title" class="form-control" required></div>
            <div class="mb-2"><label>Клиент:</label><input type="text" name="client" class="form-control" required></div>
            <div class="mb-2"><label>Сумма:</label><input type="number" name="total_sum" class="form-control" value="0"></div>
        </div>
        <div class="modal-footer"><button type="submit" class="btn btn-success">Создать</button></div>
    </form>
</div></div></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

TASKS_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Задачи</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light p-4">
    <nav class="mb-3"><a href="/" class="btn btn-secondary btn-sm">← Назад в воронку</a></nav>
    <h2>Задачи компании</h2>
    <ul>
    {% for t in tasks %}
        <li><b>{{ t.title }}</b> (Ответственный: {{ t.responsible }}, Дедлайн: {{ t.deadline }})</li>
    {% endfor %}
    </ul>
</body>
</html>
"""

ANALYTICS_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Аналитика</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-light p-4">
    <nav class="mb-3"><a href="/" class="btn btn-secondary btn-sm">← Назад</a></nav>
    <h2>Аналитика воронки</h2>
    <p>Всего сделок: {{ total_deals }}</p>
    <p>Общая сумма портфеля: {{ total_sum }} ₸</p>
</body>
</html>
"""

CALCULATOR_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Калькулятор</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
<body class="bg-light p-4">
    <nav class="mb-3"><a href="/" class="btn btn-secondary btn-sm">← Назад</a></nav>
    <h2>Калькулятор ангаров</h2>
    <div class="card p-3" style="max-width: 400px;">
        <label>Ширина (м):</label><input type="number" id="w" class="form-control mb-2" value="15">
        <label>Длина (м):</label><input type="number" id="l" class="form-control mb-2" value="40">
        <button onclick="let w=document.getElementById('w').value, l=document.getElementById('l').value; alert('Площадь: ' + (w*l) + ' кв.м, Стоимость: ' + (w*l*25000) + ' ₸');" class="btn btn-primary">Рассчитать</button>
    </div>
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
    return render_template_string(LOGIN_PAGE, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    f_man = request.args.get("manager_filter", "")
    deals = db["deals"]
    if f_man: deals = [d for d in deals if d.get("manager") == f_man]
    managers = [u["name"] for u in USERS.values() if u["role"] == "manager"]
    return render_template_string(INDEX_PAGE, user=user, stages=STAGES, deals=deals, managers=managers, f_man=f_man)

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    db["deals"].append({
        "id": str(len(db["deals"]) + 1),
        "title": request.form.get("title"),
        "client": request.form.get("client"),
        "phone": "",
        "stage": "new",
        "manager": user["name"] if user["role"] == "manager" else "",
        "total_sum": int(request.form.get("total_sum") or 0),
        "prepay": 0, "second_pay": 0, "final_pay": 0,
        "comments": []
    })
    save_db(db)
    return redirect(url_for("index"))

@app.route("/update/<id>", methods=["POST"])
def update(id):
    if "user" not in session: return redirect(url_for("login"))
    db = load_db()
    for d in db["deals"]:
        if d["id"] == id:
            d["title"] = request.form.get("title")
            d["client"] = request.form.get("client")
            d["stage"] = request.form.get("stage")
            d["total_sum"] = int(request.form.get("total_sum") or 0)
            break
    save_db(db)
    return redirect(url_for("index"))

@app.route("/tasks")
def tasks():
    if "user" not in session: return redirect(url_for("login"))
    db = load_db()
    return render_template_string(TASKS_PAGE, tasks=db["tasks"])

@app.route("/analytics")
def analytics():
    if "user" not in session: return redirect(url_for("login"))
    db = load_db()
    total_deals = len(db["deals"])
    total_sum = sum(d.get("total_sum", 0) for d in db["deals"])
    return render_template_string(ANALYTICS_PAGE, total_deals=total_deals, total_sum=total_sum)

@app.route("/calculator")
def calculator():
    if "user" not in session: return redirect(url_for("login"))
    return render_template_string(CALCULATOR_PAGE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
