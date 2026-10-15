from flask import Flask, render_template_string, request, redirect, url_for, session
import json
import os

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
    ("contact", "2. Контакт"),
    ("calc", "3. Расчет"),
    ("kp", "4. КП"),
    ("contract", "5. Договор"),
    ("production", "6. Производство"),
    ("paid", "7. Оплачено"),
    ("closed_lost", "8. Закрыто")
]

def load_db():
    if not os.path.exists(DB_FILE):
        data = {
            "deals": [
                {
                    "id": "1",
                    "title": "Ангар 20х50 для КФХ",
                    "client": "ИП Иванов",
                    "stage": "new",
                    "manager": "Менеджер 1",
                    "total_sum": 15000000
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
            return {"deals": []}

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
<body class="bg-dark d-flex align-items-center justify-content-center vh-100">
<form method="POST" class="card p-4 shadow" style="width: 320px;">
    <h3 class="mb-3 text-center">Ангар CRM</h3>
    {% if error %}<div class="alert alert-danger py-1">{{ error }}</div>{% endif %}
    <div class="mb-3"><label>Логин:</label><input type="text" name="username" class="form-control" required autofocus></div>
    <div class="mb-3"><label>Пароль:</label><input type="password" name="password" class="form-control" required></div>
    <button type="submit" class="btn btn-primary w-100">Войти</button>
</form>
</body>
</html>
"""

CRM_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Ангар CRM - Воронка</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f4f6f9; font-family: sans-serif; }
        .kanban { display: flex; overflow-x: auto; gap: 10px; padding-bottom: 20px; }
        .k-col { min-width: 250px; background: #e2e8f0; border-radius: 6px; padding: 10px; max-height: 80vh; overflow-y: auto; }
        .deal-card { background: white; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 13px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
    </style>
</head>
<body>
<nav class="navbar navbar-dark bg-dark px-3 py-2 d-flex justify-content-between">
    <span class="navbar-brand fw-bold">Ангар CRM | РОП: Лемперт А.С.</span>
    <div class="text-white">
        <span>{{ user.name }}</span> | <a href="/logout" class="text-warning text-decoration-none">Выйти</a>
    </div>
</nav>

<div class="container-fluid mt-3">
    <div class="mb-3">
        <button class="btn btn-success btn-sm" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить сделку</button>
    </div>

    <div class="kanban">
    {% for s_key, s_name in stages %}
        <div class="k-col">
            <h6 class="fw-bold text-secondary">{{ s_name }}</h6>
            {% for d in deals %}
                {% if d.stage == s_key %}
                <div class="deal-card border-start border-3 border-primary">
                    <div class="fw-bold text-primary">{{ d.title }}</div>
                    <div>Клиент: {{ d.client }}</div>
                    <div>Сумма: {{ d.total_sum }} ₸</div>
                    <div class="text-muted small mt-1">Отв: {{ d.manager or 'Не назначен' }}</div>
                    <button class="btn btn-outline-primary btn-sm w-100 mt-2 py-0" data-bs-toggle="modal" data-bs-target="#m{{ d.id }}">Изменить</button>
                </div>

                <!-- Модальное окно редактирования -->
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
                            <div class="mb-2"><label>Сумма (₸):</label><input type="number" name="total_sum" class="form-control" value="{{ d.total_sum }}"></div>
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

<!-- Модальное окно добавления -->
<div class="modal fade" id="addModal" tabindex="-1"><div class="modal-dialog"><div class="modal-content">
    <form method="POST" action="/add">
        <div class="modal-header"><h5>Новая сделка</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
            <div class="mb-2"><label>Объект / Ангар:</label><input type="text" name="title" class="form-control" required placeholder="Ангар 15х30"></div>
            <div class="mb-2"><label>Клиент / Компания:</label><input type="text" name="client" class="form-control" required placeholder="ТОО Агро"></div>
            <div class="mb-2"><label>Сумма (₸):</label><input type="number" name="total_sum" class="form-control" value="0"></div>
        </div>
        <div class="modal-footer"><button type="submit" class="btn btn-success">Создать</button></div>
    </form>
</div></div></div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
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
    return render_template_string(CRM_HTML, user=user, stages=STAGES, deals=db["deals"])

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    db["deals"].append({
        "id": str(len(db["deals"]) + 1),
        "title": request.form.get("title"),
        "client": request.form.get("client"),
        "stage": "new",
        "manager": user["name"] if user["role"] == "manager" else "Не назначен",
        "total_sum": int(request.form.get("total_sum") or 0)
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
