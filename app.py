from flask import Flask, render_template_string, request, redirect, url_for, session
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "angar_crm_super_secret_key_2026"

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
    ("tz", "3. Сбор ТЗ / Опросный лист"),
    ("calc", "4. Расчет стоимости"),
    ("kp", "5. Отправлено КП"),
    ("negotiation", "6. Переговоры / Согласование"),
    ("contract", "7. Договор на подписании"),
    ("prepay_wait", "8. Ожидание предоплаты"),
    ("production", "9. В производстве"),
    ("delivery", "10. Отгрузка / Доставка"),
    ("mounting", "11. Монтаж на объекте"),
    ("final_wait", "12. Выполнен / Ожидание остатка"),
    ("paid", "13. Оплачен полностью"),
    ("closed_lost", "14. Закрыто и не реализовано")
]

def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = {
            "deals": [
                {
                    "id": "1",
                    "title": "Ангар 20х50 для КФХ «Тобол»",
                    "client": "ИП Иванов И.И.",
                    "phone": "+7 701 555 3322",
                    "stage": "production",
                    "manager": "Менеджер 1",
                    "total_sum": 15000000,
                    "prepay": 5000000,
                    "second_pay": 5000000,
                    "final_pay": 0,
                    "reminder_date": "2026-10-20",
                    "reminder_time": "10:00",
                    "reminder_task": "Звонок по готовности ферм",
                    "comments": [{"time": "15.10.2026 10:30", "author": "Лемперт А.С. (РОП)", "text": "Согласован каркас, запустили в цех."}]
                }
            ],
            "tasks": [
                {
                    "id": "1",
                    "title": "Подготовить чертежи по спорткомплексу в Уральске",
                    "creator": "Лемперт А.С. (РОП)",
                    "responsible": "Уралбаев Ж.А. (Директор)",
                    "observer": "Лемперт А.С. (РОП)",
                    "deadline": "2026-10-18",
                    "status": "active"
                }
            ]
        }
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=4)
        return initial_data
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"deals": [], "tasks": []}

def save_db(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Angar CRM - Управление продажами</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body { background-color: #f4f6f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .navbar { background: #1e293b; }
        .kanban-container { display: flex; overflow-x: auto; padding-bottom: 20px; gap: 15px; }
        .kanban-col { min-width: 280px; background: #e2e8f0; border-radius: 8px; padding: 10px; display: flex; flex-direction: column; max-height: 80vh; overflow-y: auto; }
        .kanban-col h5 { font-size: 14px; font-weight: bold; color: #334155; text-transform: uppercase; margin-bottom: 10px; }
        .deal-card { background: white; border-radius: 6px; padding: 12px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 13px; position: relative; }
        .badge-debt { background: #fee2e2; color: #991b1b; font-weight: bold; }
        .badge-paid { background: #dcfce7; color: #166534; font-weight: bold; }
    </style>
</head>
<body>
    <nav class="navbar navbar-dark px-4 py-2 d-flex justify-content-between align-items-center">
        <a class="navbar-brand fw-bold" href="/"><i class="fa-solid fa-industry"></i> Ангар CRM <small class="text-muted fs-6">| РОП: Лемперт А.С.</small></a>
        <div class="d-flex align-items-center text-white gap-3">
            <span><i class="fa-solid fa-user-circle"></i> {{ user.name }}</span>
            <a href="/logout" class="btn btn-outline-light btn-sm">Выйти</a>
        </div>
    </nav>
    <div class="container-fluid mt-3">
        <ul class="nav nav-tabs">
            <li class="nav-item"><a class="nav-link {% if active_tab == 'kanban' %}active{% endif %}" href="/"><i class="fa-solid fa-columns"></i> Воронка (Канбан)</a></li>
            <li class="nav-item"><a class="nav-link {% if active_tab == 'tasks' %}active{% endif %}" href="/tasks"><i class="fa-solid fa-list-check"></i> Задачи</a></li>
            {% if user.role in ['director', 'rop'] %}
            <li class="nav-item"><a class="nav-link {% if active_tab == 'analytics' %}active{% endif %}" href="/analytics"><i class="fa-solid fa-chart-pie"></i> Аналитика воронки</a></li>
            {% endif %}
            <li class="nav-item"><a class="nav-link {% if active_tab == 'calculator' %}active{% endif %}" href="/calculator"><i class="fa-solid fa-calculator"></i> Калькулятор и КП</a></li>
        </ul>
    </div>
    <div class="container-fluid mt-3">
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
'''

LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Вход в Angar CRM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-dark d-flex align-items-center justify-content-center vh-100">
    <div class="card p-4 shadow" style="width: 350px;">
        <h3 class="text-center mb-3">Вход в CRM</h3>
        {% if error %}<div class="alert alert-danger py-2">{{ error }}</div>{% endif %}
        <form method="POST">
            <div class="mb-3">
                <label class="form-label">Логин:</label>
                <input type="text" name="username" class="form-control" required autofocus>
            </div>
            <div class="mb-3">
                <label class="form-label">Пароль:</label>
                <input type="password" name="password" class="form-control" required>
            </div>
            <button type="submit" class="btn btn-primary w-100">Войти</button>
        </form>
    </div>
</body>
</html>
'''

KANBAN_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", '''
<div class="row mb-3 align-items-center">
    <div class="col-md-8 d-flex gap-2">
        <button class="btn btn-success btn-sm" data-bs-toggle="modal" data-bs-target="#addDealModal"><i class="fa-solid fa-plus"></i> Добавить клиента</button>
        <form method="GET" class="d-flex gap-2">
            <select name="manager_filter" class="form-select form-select-sm" onchange="this.form.submit()">
                <option value="">Все менеджеры</option>
                {% for m in all_managers %}
                <option value="{{ m }}" {% if manager_filter == m %}selected{% endif %}>{{ m }}</option>
                {% endfor %}
            </select>
        </form>
    </div>
</div>

<div class="kanban-container">
    {% for s_key, s_name in stages %}
    <div class="kanban-col">
        <h5>{{ s_name }}</h5>
        {% for deal in deals %}
            {% if deal.stage == s_key %}
                {% set debt = deal.total_sum - (deal.prepay + deal.second_pay + deal.final_pay) %}
                <div class="deal-card border-start border-4 {% if debt > 0 %}border-danger{% else %}border-success{% endif %}">
                    <div class="fw-bold text-primary">{{ deal.title }}</div>
                    <div class="text-muted small">Клиент: {{ deal.client }}</div>
                    <div class="text-muted small">Тел: {{ deal.phone }}</div>
                    <hr class="my-1">
                    <div class="small"><b>Сумма:</b> {{ "{:,}".format(deal.total_sum).replace(',', ' ') }} ₸</div>
                    <div class="small">
                        <b>Долг:</b> 
                        <span class="badge {% if debt > 0 %}badge-debt{% else %}badge-paid{% endif %}">
                            {{ "{:,}".format(debt).replace(',', ' ') }} ₸
                        </span>
                    </div>
                    <div class="small text-secondary mt-1"><i class="fa-solid fa-user"></i> {{ deal.manager if deal.manager else 'Не назначен' }}</div>
                    
                    <div class="mt-2 d-flex justify-content-between align-items-center">
                        <button class="btn btn-outline-primary btn-sm py-0 px-2" data-bs-toggle="modal" data-bs-target="#dealModal{{ deal.id }}">Открыть</button>
                        <span class="text-muted" style="font-size: 10px;">{{ deal.comments|last.time if deal.comments else '' }}</span>
                    </div>
                </div>

                <!-- Модальное окно сделки -->
                <div class="modal fade" id="dealModal{{ deal.id }}" tabindex="-1">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <form method="POST" action="/update_deal/{{ deal.id }}">
                                <div class="modal-header">
                                    <h5 class="modal-title">{{ deal.title }}</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body">
                                    <div class="row mb-3">
                                        <div class="col-md-6">
                                            <label class="form-label">Название / Объект:</label>
                                            <input type="text" name="title" class="form-control" value="{{ deal.title }}" required>
                                        </div>
                                        <div class="col-md-6">
                                            <label class="form-label">Клиент:</label>
                                            <input type="text" name="client" class="form-control" value="{{ deal.client }}">
                                        </div>
                                    </div>
                                    <div class="row mb-3">
                                        <div class="col-md-4">
                                            <label class="form-label">Телефон:</label>
                                            <input type="text" name="phone" class="form-control" value="{{ deal.phone }}">
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Этап воронки:</label>
                                            <select name="stage" class="form-select">
                                                {% for k, v in stages %}
                                                <option value="{{ k }}" {% if deal.stage == k %}selected{% endif %}>{{ v }}</option>
                                                {% endfor %}
                                            </select>
                                        </div>
                                        <div class="col-md-4">
                                            <label class="form-label">Ответственный:</label>
                                            {% if user.role in ['director', 'rop'] %}
                                            <select name="manager" class="form-select">
                                                <option value="" {% if not deal.manager %}selected{% endif %}>-- Не назначен --</option>
                                                {% for m in all_managers %}
                                                <option value="{{ m }}" {% if deal.manager == m %}selected{% endif %}>{{ m }}</option>
                                                {% endfor %}
                                            </select>
                                            {% else %}
                                                {% if not deal.manager %}
                                                <select name="manager" class="form-select">
                                                    <option value="">-- Выбрать себя --</option>
                                                    <option value="{{ user.name }}">{{ user.name }} (Взять себе)</option>
                                                </select>
                                                {% else %}
                                                <input type="text" class="form-control" value="{{ deal.manager }}" readonly>
                                                <input type="hidden" name="manager" value="{{ deal.manager }}">
                                                <small class="text-muted">Смену меняет только РОП</small>
                                                {% endif %}
                                            {% endif %}
                                        </div>
                                    </div>

                                    <h6 class="text-primary mt-4">Финансовый учет и дебиторка</h6>
                                    <div class="row mb-3 bg-light p-2 rounded">
                                        <div class="col-md-3">
                                            <label class="form-label small">Общая сумма (₸):</label>
                                            <input type="number" name="total_sum" class="form-control" value="{{ deal.total_sum }}">
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label small">Предоплата (₸):</label>
                                            <input type="number" name="prepay" class="form-control" value="{{ deal.prepay }}">
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label small">2-й платеж (₸):</label>
                                            <input type="number" name="second_pay" class="form-control" value="{{ deal.second_pay }}">
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label small">Окончат. расчет (₸):</label>
                                            <input type="number" name="final_pay" class="form-control" value="{{ deal.final_pay }}">
                                        </div>
                                    </div>

                                    <h6 class="text-primary mt-3">Напоминание / Задача по клиенту</h6>
                                    <div class="row mb-3 bg-light p-2 rounded">
                                        <div class="col-md-4">
                                            <label class="form-label small">Дата:</label>
                                            <input type="date" name="reminder_date" class="form-control" value="{{ deal.reminder_date }}">
                                        </div>
                                        <div class="col-md-3">
                                            <label class="form-label small">Время:</label>
                                            <input type="time" name="reminder_time" class="form-control" value="{{ deal.reminder_time }}">
                                        </div>
                                        <div class="col-md-5">
                                            <label class="form-label small">Действие (Звонок, КП и т.д.):</label>
                                            <input type="text" name="reminder_task" class="form-control" value="{{ deal.reminder_task }}" placeholder="Например: Позвонить по КП">
                                        </div>
                                    </div>

                                    <h6 class="text-primary mt-3">Добавить комментарий / Заметку</h6>
                                    <textarea name="new_comment" class="form-control mb-3" rows="2" placeholder="Введите текст комментария..."></textarea>

                                    <h6 class="text-muted">История изменений и комментариев:</h6>
                                    <div class="border rounded p-2 bg-white" style="max-height: 150px; overflow-y: auto;">
                                        {% for c in deal.comments %}
                                        <div class="border-bottom py-1 small">
                                            <span class="text-muted">[{{ c.time }}] <b>{{ c.author }}</b>:</span> {{ c.text }}
                                        </div>
                                        {% endfor %}
                                    </div>
                                </div>
                                <div class="modal-footer">
                                    <button type="submit" class="btn btn-primary">Сохранить изменения</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            {% endif %}
        {% endfor %}
    </div>
    {% endfor %}
</div>

<!-- Модальное окно: Добавить клиента -->
<div class="modal fade" id="addDealModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <form method="POST" action="/add_deal">
                <div class="modal-header">
                    <h5 class="modal-title">Новый клиент / сделка</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="mb-3">
                        <label class="form-label">Название объекта / проекта:</label>
                        <input type="text" name="title" class="form-control" required placeholder="Ангар 15х30">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Имя клиента / Компания:</label>
                        <input type="text" name="client" class="form-control" required placeholder="ТОО АгроХолдинг">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Телефон:</label>
                        <input type="text" name="phone" class="form-control" placeholder="+7 ...">
                    </div>
                    <div class="mb-3">
                        <label class="form-label">Общая сумма договора (₸):</label>
                        <input type="number" name="total_sum" class="form-control" value="0">
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="submit" class="btn btn-success">Создать клиента</button>
                </div>
            </form>
        </div>
    </div>
</div>
''')

TASKS_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", '''
<div class="row">
    <div class="col-md-4">
        <div class="card p-3 shadow-sm">
            <h5 class="mb-3">Поставить новую задачу</h5>
            <form method="POST" action="/add_task">
                <div class="mb-2">
                    <label class="form-label small">Суть задачи:</label>
                    <input type="text" name="title" class="form-control" required placeholder="Подготовить чертежи...">
                </div>
                <div class="mb-2">
                    <label class="form-label small">Ответственный:</label>
                    <select name="responsible" class="form-select">
                        {% for m in all_managers %}
                        <option value="{{ m }}">{{ m }}</option>
                        {% endfor %}
                        <option value="Уралбаев Ж.А. (Директор)">Уралбаев Ж.А. (Директор)</option>
                        <option value="Лемперт А.С. (РОП)">Лемперт А.С. (РОП)</option>
                    </select>
                </div>
                <div class="mb-2">
                    <label class="form-label small">Наблюдатель:</label>
                    <select name="observer" class="form-select">
                        <option value="Лемперт А.С. (РОП)">Лемперт А.С. (РОП)</option>
                        <option value="Уралбаев Ж.А. (Директор)">Уралбаев Ж.А. (Директор)</option>
                    </select>
                </div>
                <div class="mb-3">
                    <label class="form-label small">Срок (Дедлайн):</label>
                    <input type="date" name="deadline" class="form-control" required>
                </div>
                <button type="submit" class="btn btn-primary w-100 btn-sm">Поставить задачу</button>
            </form>
        </div>
    </div>
    
    <div class="col-md-8">
        <h4 class="mb-3">Список задач компании</h4>
        <div class="list-group">
            {% for t in tasks %}
            <div class="list-group-item list-group-item-action d-flex justify-content-between align-items-center mb-2 rounded shadow-sm">
                <div>
                    <h6 class="mb-1 fw-bold">{{ t.title }}</h6>
                    <small class="text-muted">Поставил: {{ t.creator }} | <b>Ответственный: {{ t.responsible }}</b> | Наблюдатель: {{ t.observer }}</small><br>
                    <small class="text-danger">Дедлайн: {{ t.deadline }}</small>
                </div>
                <div>
                    {% if t.status == 'active' %}
                    <a href="/complete_task/{{ t.id }}" class="btn btn-outline-success btn-sm">Выполнить</a>
                    {% else %}
                    <span class="badge bg-success">Выполнено</span>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>
''')

ANALYTICS_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", '''
<div class="row">
    <div class="col-md-12">
        <h3 class="mb-4">Аналитика воронки продаж и дебиторская задолженность</h3>
        <div class="row text-white">
            <div class="col-md-4 mb-3">
                <div class="card bg-primary p-3 shadow">
                    <h5>Всего сделок</h5>
                    <h3>{{ total_deals }}</h3>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-success p-3 shadow">
                    <h5>Общая сумма портфеля</h5>
                    <h3>{{ "{:,}".format(total_sum_all).replace(',', ' ') }} ₸</h3>
                </div>
            </div>
            <div class="col-md-4 mb-3">
                <div class="card bg-danger p-3 shadow">
                    <h5>Общая дебиторка (остаток)</h5>
                    <h3>{{ "{:,}".format(total_debt_all).replace(',', ' ') }} ₸</h3>
                </div>
            </div>
        </div>
    </div>
</div>
''')

CALCULATOR_TEMPLATE = HTML_TEMPLATE.replace("{% block content %}{% endblock %}", '''
<div class="row">
    <div class="col-md-6">
        <div class="card p-4 shadow-sm">
            <h4 class="mb-3">Калькулятор арочных / прямостенных ангаров</h4>
            <div class="mb-3">
                <label class="form-label">Ширина (м):</label>
                <input type="number" id="width" class="form-control" value="15">
            </div>
            <div class="mb-3">
                <label class="form-label">Длина (м):</label>
                <input type="number" id="length" class="form-control" value="40">
            </div>
            <div class="mb-3">
                <label class="form-label">Тип ангара:</label>
                <select id="type" class="form-select">
                    <option value="cold">Холодный (тент ПВХ / профлист)</option>
                    <option value="warm">Утепленный (сэндвич-панели / минеральная вата)</option>
                </select>
            </div>
            <button onclick="calculate()" class="btn btn-primary w-100">Рассчитать предварительную стоимость</button>
        </div>
    </div>
    <div class="col-md-6">
        <div class="card p-4 shadow-sm bg-light">
            <h4>Результат расчета и генерации КП</h4>
            <div id="calcResult" class="mt-3 fs-5">
                Нажмите кнопку расчета слева, чтобы получить смету и сформировать коммерческое предложение.
            </div>
        </div>
    </div>
</div>
<script>
function calculate() {
    let w = document.getElementById('width').value;
    let l = document.getElementById('length').value;
    let type = document.getElementById('type').value;
    let area = w * l;
    let pricePerSq = (type === 'warm') ? 45000 : 25000;
    let total = area * pricePerSq;
    document.getElementById('calcResult').innerHTML = `
        <b>Площадь ангара:</b> ${area} кв.м.<br>
        <b>Исполнение:</b> ${type === 'warm' ? 'Утепленный' : 'Холодный'}<br>
        <hr>
        <h3 class="text-success">Итого стоимость: ${total.toLocaleString()} ₸</h3>
        <p class="text-muted small mt-2">Расчет сформирован для коммерческого предложения.</p>
    `;
}
</script>
''')

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username in USERS and USERS[username]["pass"] == password:
            session["user"] = username
            return redirect(url_for("index"))
        error = "Неверный логин или пароль"
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    user_info = USERS[session["user"]]
    db = load_db()
    manager_filter = request.args.get("manager_filter", "")
    deals = db["deals"]
    if manager_filter:
        deals = [d for d in deals if d.get("manager") == manager_filter]
    all_managers = [u["name"] for u in USERS.values() if u["role"] == "manager"]
    return render_template_string(KANBAN_TEMPLATE, active_tab="kanban", user=user_info, stages=STAGES, deals=deals, all_managers=all_managers, manager_filter=manager_filter)

@app.route("/add_deal", methods=["POST"])
def add_deal():
    if "user" not in session:
        return redirect(url_for("login"))
    user_info = USERS[session["user"]]
    db = load_db()
    new_id = str(len(db["deals"]) + 1)
    new_deal = {
        "id": new_id,
        "title": request.form.get("title"),
        "client": request.form.get("client"),
        "phone": request.form.get("phone"),
        "stage": "new",
        "manager": user_info["name"] if user_info["role"] == "manager" else "",
        "total_sum": int(request.form.get("total_sum") or 0),
        "prepay": 0,
        "second_pay": 0,
        "final_pay": 0,
        "reminder_date": "",
        "reminder_time": "",
        "reminder_task": "",
        "comments": [{"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "author": user_info["name"], "text": "Создана новая карточка клиента."}]
    }
    db["deals"].append(new_deal)
    save_db(db)
    return redirect(url_for("index"))

@app.route("/update_deal/<deal_id>", methods=["POST"])
def update_deal(deal_id):
    if "user" not in session:
        return redirect(url_for("login"))
    user_info = USERS[session["user"]]
    db = load_db()
    for deal in db["deals"]:
        if deal["id"] == deal_id:
            deal["title"] = request.form.get("title")
            deal["client"] = request.form.get("client")
            deal["phone"] = request.form.get("phone")
            old_stage = deal["stage"]
            new_stage = request.form.get("stage")
            deal["stage"] = new_stage
            new_manager = request.form.get("manager")
            if user_info["role"] in ["director", "rop"]:
                deal["manager"] = new_manager
            elif not deal.get("manager") and new_manager:
                deal["manager"] = user_info["name"]
            deal["total_sum"] = int(request.form.get("total_sum") or 0)
            deal["prepay"] = int(request.form.get("prepay") or 0)
            deal["second_pay"] = int(request.form.get("second_pay") or 0)
            deal["final_pay"] = int(request.form.get("final_pay") or 0)
            deal["reminder_date"] = request.form.get("reminder_date")
            deal["reminder_time"] = request.form.get("reminder_time")
            deal["reminder_task"] = request.form.get("reminder_task")
            new_comment = request.form.get("new_comment")
            if new_comment:
                deal["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "author": user_info["name"], "text": new_comment})
            elif old_stage != new_stage:
                deal["comments"].append({"time": datetime.now().strftime("%d.%m.%Y %H:%M"), "author": user_info["name"], "text": "Изменен этап воронки."})
            break
    save_db(db)
    return redirect(url_for("index"))

@app.route("/tasks")
def tasks_page():
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    user_info = USERS[session["user"]]
    all_managers = [u["name"] for u in USERS.values() if u["role"] == "manager"]
    return render_template_string(TASKS_TEMPLATE, active_tab="tasks", user=user_info, tasks=db["tasks"], all_managers=all_managers)

@app.route("/add_task", methods=["POST"])
def add_task():
    if "user" not in session:
        return redirect(url_for("login"))
    user_info = USERS[session["user"]]
    db = load_db()
    new_t = {
        "id": str(len(db["tasks"]) + 1),
        "title": request.form.get("title"),
        "creator": user_info["name"],
        "responsible": request.form.get("responsible"),
        "observer": request.form.get("observer"),
        "deadline": request.form.get("deadline"),
        "status": "active"
    }
    db["tasks"].append(new_t)
    save_db(db)
    return redirect(url_for("tasks_page"))

@app.route("/complete_task/<task_id>")
def complete_task(task_id):
    if "user" not in session:
        return redirect(url_for("login"))
    db = load_db()
    for t in db["tasks"]:
        if t["id"] == task_id:
            t["status"] = "completed"
    save_db(db)
    return redirect(url_for("tasks_page"))

@app.route("/analytics")
def analytics_page():
    if "user" not in session:
        return redirect(url_for("login"))
    user_info = USERS[session["user"]]
    if user_info["role"] not in ["director", "rop"]:
        return "Доступ ограничен", 403
    db = load_db()
    total_deals = len(db["deals"])
    total_sum_all = sum(d.get("total_sum", 0) for d in db["deals"])
    total_debt_all = sum(d.get("total_sum", 0) - (d.get("prepay", 0) + d.get("second_pay", 0) + d.get("final_pay", 0)) for d in db["deals"])
    return render_template_string(ANALYTICS_TEMPLATE, active_tab="analytics", user=user_info, total_deals=total_deals, total_sum_all=total_sum_all, total_debt_all=total_debt_all)

@app.route("/calculator")
def calculator_page():
    if "user" not in session:
        return redirect(url_for("login"))
    user_info = USERS[session["user"]]
    return render_template_string(CALCULATOR_TEMPLATE, active_tab="calculator", user=user_info)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
