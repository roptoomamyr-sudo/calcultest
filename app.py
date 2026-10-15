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
    ("stage_1", "1. Новый клиент", "#6c757d"),
    ("stage_2", "2. Не дозвон", "#dc3545"),
    ("stage_3", "3. Нужно выйти на ЛПР", "#212529"),
    ("stage_4", "4. Скинул презентацию / инфу", "#0dcaf0"),
    ("stage_5", "5. Скинул КП", "#198754"),
    ("stage_6", "6. Нет обратной связи", "#fd7e14"),
    ("stage_7", "7. Веду переговоры", "#0d6efd"),
    ("stage_8", "8. Отложил / Передумал", "#ffc107"),
    ("stage_9", "9. Купил у конкурентов", "#6c2323"),
    ("stage_10", "10. Готов контрактоваться", "#157347"),
    ("stage_11", "11. Сделали договор", "#0f5132"),
    ("stage_12", "12. Внес предоплату", "#6f42c1"),
    ("stage_13", "13. Выполнен (Дебиторка)", "#0d6efd"),
    ("stage_14", "14. Оплачен полностью", "#198754"),
    ("stage_15", "15. Повторный заказ (VIP)", "#ffc107")
]

def load_db():
    default_data = {
        "deals": [
            {
                "id": "1",
                "title": 'ТОО "МИРАМ"',
                "client": 'ТОО "МИРАМ"',
                "phone": "+7 705 626 54 24",
                "region": "Костанайская область",
                "stage": "stage_5",
                "manager": "Лемперт А.С.",
                "total_sum": 25000000,
                "comment": "Ангар 20х120, скинул КП"
            },
            {
                "id": "2",
                "title": 'КХ "АХМЕТОВ"',
                "client": 'КХ "АХМЕТОВ"',
                "phone": "+7 870 561 26 31",
                "region": "Павлодарская область",
                "stage": "stage_2",
                "manager": "Не назначен",
                "total_sum": 0,
                "comment": "Не дозвон"
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

CRM_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>CRM Воронка Ангары (Bitrix24 Style)</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #f8f9fa; font-family: Arial, sans-serif; }
        .top-bar { background: #ffffff; border-bottom: 1px solid #dee2e6; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; }
        .kanban { display: flex; overflow-x: auto; gap: 12px; padding: 15px; height: calc(100vh - 120px); }
        .k-col { min-width: 280px; max-width: 280px; background: #e9ecef; border-radius: 6px; display: flex; flex-direction: column; max-height: 100%; }
        .k-header { padding: 10px; font-weight: bold; font-size: 13px; color: white; border-top-left-radius: 6px; border-top-right-radius: 6px; text-align: center; }
        .k-body { padding: 8px; overflow-y: auto; flex-grow: 1; }
        .deal-card { background: #ffffff; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 12px; border: 1px solid #ced4da; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: pointer; transition: 0.15s; }
        .deal-card:hover { border-color: #0d6efd; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
    </style>
</head>
<body>

<div class="top-bar">
    <div class="d-flex align-items-center gap-3">
        <h5 class="m-0 fw-bold text-secondary">🗂️ CRM Воронка Ангары (Bitrix24)</h5>
        <button class="btn btn-success btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить сделку</button>
    </div>
    <div class="d-flex align-items-center gap-3">
        <span class="badge bg-success">Облачная CRM Активна</span>
        <span class="text-dark small">👤 {{ user.name }}</span>
        <a href="/logout" class="btn btn-outline-danger btn-sm py-0">Выйти</a>
    </div>
</div>

<div class="kanban">
    {% for s_key, s_name, s_color in stages %}
    <div class="k-col">
        <div class="k-header" style="background-color: {{ s_color }};">{{ s_name }}</div>
        <div class="k-body">
            {% for d in deals %}
                {% if d.stage == s_key %}
                <div class="deal-card" data-bs-toggle="modal" data-bs-target="#cardModal{{ d.id }}">
                    <div class="fw-bold text-primary mb-1" style="font-size: 13px;">{{ d.title }}</div>
                    <div class="text-muted text-truncate">📍 {{ d.region or 'Регион не указан' }}</div>
                    <div class="text-secondary text-truncate">📞 {{ d.phone or 'Нет телефона' }}</div>
                    <div class="text-dark mt-1 text-truncate">💬 {{ d.comment or 'Нет описания' }}</div>
                    <div class="mt-2 pt-1 border-top d-flex justify-content-between text-muted" style="font-size: 11px;">
                        <span>Сумма: {{ "{:,}".format(d.total_sum).replace(",", " ") }} ₸</span>
                        <span class="badge bg-light text-dark border">{{ d.manager or 'Не назначен' }}</span>
                    </div>
                </div>

                <div class="modal fade" id="cardModal{{ d.id }}" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <form method="POST" action="/update/{{ d.id }}">
                                <div class="modal-header bg-primary text-white">
                                    <h5 class="modal-title">Карточка клиента: {{ d.client }}</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row g-3">
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Компания / ТОО / КХ:</label>
                                            <input type="text" name="client" class="form-control" value="{{ d.client }}" required>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Телефон:</label>
                                            <input type="text" name="phone" class="form-control" value="{{ d.phone }}">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Регион / Область:</label>
                                            <input type="text" name="region" class="form-control" value="{{ d.region }}">
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Этап воронки:</label>
                                            <select name="stage" class="form-select">
                                                {% for sk, sn, sc in stages %}
                                                <option value="{{ sk }}" {% if d.stage == sk %}selected{% endif %}>{{ sn }}</option>
                                                {% endfor %}
                                            </select>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Сумма сделки (₸):</label>
                                            <input type="number" name="total_sum" class="form-control" value="{{ d.total_sum }}">
                                        </div>
                                        <div class="col-12">
                                            <label class="form-label fw-bold">Комментарий / История:</label>
                                            <textarea name="comment" class="form-control" rows="3">{{ d.comment }}</textarea>
                                        </div>
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                                    <button type="submit" class="btn btn-primary">Сохранить изменения</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
                {% endif %}
            {% endfor %}
        </div>
    </div>
    {% endfor %}
</div>

<div class="modal fade" id="addModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <form method="POST" action="/add">
                <div class="modal-header bg-success text-white">
                    <h5 class="modal-title">Новая заявка</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-2"><label class="form-label">Клиент / ТОО / КХ:</label><input type="text" name="client" class="form-control" required placeholder="ТОО Агро"></div>
                    <div class="mb-2"><label class="form-label">Телефон:</label><input type="text" name="phone" class="form-control" placeholder="+7..."></div>
                    <div class="mb-2"><label class="form-label">Регион:</label><input type="text" name="region" class="form-control" placeholder="Костанайская область"></div>
                    <div class="mb-2"><label class="form-label">Сумма (₸):</label><input type="number" name="total_sum" class="form-control" value="0"></div>
                    <div class="mb-2"><label class="form-label">Комментарий:</label><textarea name="comment" class="form-control" rows="2"></textarea></div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">Отмена</button>
                    <button type="submit" class="btn btn-success btn-sm">Создать</button>
                </div>
            </form>
        </div>
    </div>
</div>

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
    client_name = request.form.get("client")
    db["deals"].append({
        "id": str(len(db["deals"]) + 1),
        "title": client_name,
        "client": client_name,
        "phone": request.form.get("phone"),
        "region": request.form.get("region"),
        "stage": "stage_1",
        "manager": user["name"],
        "total_sum": int(request.form.get("total_sum") or 0),
        "comment": request.form.get("comment")
    })
    save_db(db)
    return redirect(url_for("index"))

@app.route("/update/<id>", methods=["POST"])
def update(id):
    if "user" not in session: return redirect(url_for("login"))
    db = load_db()
    for d in db["deals"]:
        if d["id"] == id:
            client_name = request.form.get("client")
            d["title"] = client_name
            d["client"] = client_name
            d["phone"] = request.form.get("phone")
            d["region"] = request.form.get("region")
            d["stage"] = request.form.get("stage")
            d["total_sum"] = int(request.form.get("total_sum") or 0)
            d["comment"] = request.form.get("comment")
            break
    save_db(db)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
