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
            <form method="P
