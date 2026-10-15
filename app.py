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
                "phone": "+7 705 626 54 24",
                "region": "Костанайская область",
                "stage": "stage_5",
                "manager": "Лемперт А.С. (РОП)",
                "total_sum": 0,
                "history": [{"date": "15.10.2026 12:00", "author": "РОП", "text": "Создана сделка, скинул КП"}],
                "tasks": [{"date": "15.10.2026", "type": "Звонок", "text": "Уточнить решение по КП", "done": False}]
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
                "history": [{"date": "15.10.2026 12:05", "author": "Директор", "text": "Не дозвон"}],
                "tasks": []
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
        .k-body { padding: 8px; overflow-y: auto; flex-grow: 1; min-height: 200px; }
        .deal-card { background: #ffffff; border-radius: 4px; padding: 10px; margin-bottom: 8px; font-size: 12px; border: 1px solid #ced4da; box-shadow: 0 1px 2px rgba(0,0,0,0.05); cursor: grab; transition: 0.15s; }
        .deal-card:active { cursor: grabbing; opacity: 0.7; }
        .deal-card:hover { border-color: #0d6efd; box-shadow: 0 3px 6px rgba(0,0,0,0.1); }
        .history-box { background: #f1f3f5; border-radius: 4px; padding: 8px; max-height: 130px; overflow-y: auto; font-size: 11px; }
        .drag-over { background-color: #d0e1fd !important; border: 2px dashed #0d6efd; }
    </style>
</head>
<body>

<div class="top-bar">
    <div class="d-flex align-items-center gap-3">
        <h5 class="m-0 fw-bold text-secondary">🗂️ CRM Воронка Ангары (Bitrix24)</h5>
        <button class="btn btn-success btn-sm fw-bold" data-bs-toggle="modal" data-bs-target="#addModal">+ Добавить сделку</button>
        <button class="btn btn-warning btn-sm fw-bold text-dark" data-bs-toggle="modal" data-bs-target="#tasksListModal">🔔 Напоминания <span class="badge bg-danger ms-1">{{ total_tasks_count }}</span></button>
    </div>
    <div class="d-flex align-items-center gap-3">
        <span class="badge bg-success">Облачная CRM Активна</span>
        <span class="text-dark small">👤 {{ user.name }}</span>
        <a href="/logout" class="btn btn-outline-danger btn-sm py-0">Выйти</a>
    </div>
</div>

<div class="kanban">
    {% for s_key, s_name, s_color in stages %}
    <div class="k-col" data-stage="{{ s_key }}">
        <div class="k-header" style="background-color: {{ s_color }}; {% if s_key == 'stage_2' %}color: #000;{% endif %}">{{ s_name }}</div>
        <div class="k-body" id="col-{{ s_key }}" ondragover="allowDrop(event)" ondragleave="removeDragOver(event)" ondrop="dropDeal(event, '{{ s_key }}')">
            {% for d in deals %}
                {% if d.stage == s_key %}
                <div class="deal-card" id="card-{{ d.id }}" draggable="true" ondragstart="dragDeal(event, '{{ d.id }}')" data-bs-toggle="modal" data-bs-target="#cardModal{{ d.id }}">
                    <div class="fw-bold text-primary mb-1" style="font-size: 13px;">{{ d.title }}</div>
                    <div class="text-muted text-truncate">📍 {{ d.region or 'Регион не указан' }}</div>
                    <div class="text-secondary text-truncate">📞 {{ d.phone or 'Нет телефона' }}</div>
                    
                    {% if d.tasks %}
                    <div class="mt-1"><span class="badge bg-warning text-dark">⏰ Задача: {{ d.tasks[-1].date }} ({{ d.tasks[-1].type }})</span></div>
                    {% endif %}

                    <div class="mt-2 pt-1 border-top d-flex justify-content-between text-muted" style="font-size: 11px;">
                        {% if loop.index0 >= 10 or d.total_sum > 0 %}
                        <span>Сумма: {{ "{:,}".format(d.total_sum).replace(",", " ") }} ₸</span>
                        {% else %}
                        <span>Сумма: —</span>
                        {% endif %}
                        <span class="badge bg-light text-dark border">{{ d.manager or 'Не назначен' }}</span>
                    </div>
                </div>

                <!-- Карточка клиента -->
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
                                            <label class="form-label fw-bold">Ответственный менеджер:</label>
                                            {% if user.role in ['director', 'rop'] %}
                                            <select name="manager" class="form-select">
                                                <option value="Не назначен" {% if d.manager == 'Не назначен' %}selected{% endif %}>Не назначен</option>
                                                <option value="Менеджер 1" {% if d.manager == 'Менеджер 1' %}selected{% endif %}>Менеджер 1</option>
                                                <option value="Менеджер 2" {% if d.manager == 'Менеджер 2' %}selected{% endif %}>Менеджер 2</option>
                                                <option value="Уралбаев Ж.А. (Директор)" {% if d.manager == 'Уралбаев Ж.А. (Директор)' %}selected{% endif %}>Уралбаев Ж.А. (Директор)</option>
                                                <option value="Лемперт А.С. (РОП)" {% if d.manager == 'Лемперт А.С. (РОП)' %}selected{% endif %}>Лемперт А.С. (РОП)</option>
                                            </select>
                                            {% else %}
                                            <input type="text" class="form-control bg-light" value="{{ d.manager }}" readonly>
                                            <input type="hidden" name="manager" value="{{ d.manager }}">
                                            <div class="form-text text-muted">Изменять ответственного может только РОП или Директор.</div>
                                            {% endif %}
                                        </div>

                                        <div class="col-md-6">
                                            <label class="form-label fw-bold">Сумма сделки (₸):</label>
                                            <input type="number" name="total_sum" class="form-control" value="{{ d.total_sum }}">
                                        </div>

                                        <!-- Блок постановки задачи / напоминания -->
                                        <div class="col-12 bg-light p-3 border rounded">
                                            <h6 class="fw-bold text-warning text-dark m-0 mb-2">⏰ Поставить напоминание / задачу:</h6>
                                            <div class="row g-2">
                                                <div class="col-md-4">
                                                    <input type="date" name="task_date" class="form-control form-control-sm">
                                                </div>
                                                <div class="col-md-4">
                                                    <select name="task_type" class="form-select form-select-sm">
                                                        <option value="Звонок">📞 Звонок</option>
                                                        <option value="Встреча">🤝 Встреча</option>
                                                        <option value="Отправить КП">📄 Отправить КП</option>
                                                        <option value="Отправить презентацию">📊 Отправить презентацию</option>
                                                        <option value="Выставить счет">💳 Выставить счет</option>
                                                    </select>
                                                </div>
                                                <div class="col-md-4">
                                                    <input type="text" name="task_text" class="form-control form-control-sm" placeholder="Что нужно сделать...">
                                                </div>
                                            </div>
                                        </div>

                                        <div class="col-12">
                                            <label class="form-label fw-bold text-success">+ Добавить комментарий в историю:</label>
                                            <textarea name="new_comment" class="form-control" rows="2" placeholder="Напишите результат звонка..."></textarea>
                                        </div>

                                        <div class="col-12">
                                            <label class="form-label fw-bold text-secondary">📜 История и задачи:</label>
                                            <div class="history-box">
                                                {% if d.history %}
                                                    {% for h in d.history|reverse %}
                                                    <div class="mb-1 border-bottom pb-1">
                                                        <span class="text-primary fw-bold">[{{ h.date }}] {{ h.author }}:</span> 
                                                        <span>{{ h.text }}</span>
                                                    </div>
                                                    {% endfor %}
                                                {% endif %}
                                            </div>
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

<!-- Модальное окно создания -->
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

<!-- Модальное окно списка всех напоминаний -->
<div class="modal fade" id="tasksListModal" tabindex="-1">
    <div class="modal-dialog modal-lg">
        <div class="modal-content">
            <div class="modal-header bg-warning text-dark">
                <h5 class="modal-title fw-bold">🔔 Все запланированные напоминания</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <div class="list-group">
                {% for d in deals %}
                    {% for t in d.tasks %}
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        <div>
                            <span class="badge bg-primary">{{ t.date }}</span>
                            <span class="badge bg-secondary">{{ t.type }}</span>
                            <strong class="ms-2">{{ d.client }}</strong>
                            <div class="small text-muted mt-1">{{ t.text }}</div>
                        </div>
                        <span class="badge bg-light text-dark border">Менеджер: {{ d.manager }}</span>
                    </div>
                    {% endfor %}
                {% endfor %}
                </div>
            </div>
        </div>
    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- Скрипт Drag and Drop (Перетаскивание мышкой) -->
<script>
function dragDeal(ev, dealId) {
    ev.dataTransfer.setData("dealId", dealId);
}

function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add("drag-over");
}

function removeDragOver(ev) {
    ev.currentTarget.classList.remove("drag-over");
}

function dropDeal(ev, targetStage) {
    ev.preventDefault();
    ev.currentTarget.classList.remove("drag-over");
    var dealId = ev.dataTransfer.getData("dealId");
    
    // Отправляем запрос на сервер об изменении этапа
    fetch('/move_deal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: dealId, stage: targetStage })
    }).then(res => res.json()).then(data => {
        if(data.success) {
            location.reload(); // Мгновенно обновляем воронку
        }
    });
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
    
    # Считаем общее количество задач
    total_tasks = sum(len(d.get("tasks", [])) for d in db["deals"])
    
    return render_template_string(CRM_HTML, user=user, stages=STAGES, deals=db["deals"], total_tasks_count=total_tasks)

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
                d["history"].append({
                    "date": now_str, 
                    "author": user["name"], 
                    "text": f"Перетащил карточку на этап: {stage_name}"
                })
                save_db(db)
                return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/add", methods=["POST"])
def add():
    if "user" not in session: return redirect(url_for("login"))
    user = USERS[session["user"]]
    db = load_db()
    client_name = request.form.get("client")
    initial_comment = request.form.get("comment", "").strip()
    
    now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
    history_list = []
    if initial_comment:
        history_list.append({"date": now_str, "author": user["name"], "text": initial_comment})
    else:
        history_list.append({"date": now_str, "author": user["name"], "text": "Создана новая заявка"})

    db["deals"].append({
        "id": str(len(db["deals"]) + 1),
        "title": client_name,
        "client": client_name,
        "phone": request.form.get("phone"),
        "region": request.form.get("region"),
        "stage": "stage_1",
        "manager": user["name"],
        "total_sum": int(request.form.get("total_sum") or 0),
        "history": history_list,
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
            
            # Задача
            task_date = request.form.get("task_date")
            task_type = request.form.get("task_type")
            task_text = request.form.get("task_text", "").strip()
            
            if task_date and task_text:
                if "tasks" not in d: d["tasks"] = []
                d["tasks"].append({"date": task_date, "type": task_type, "text": task_text, "done": False})
                now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
                d["history"].append({"date": now_str, "author": current_user["name"], "text": f"Поставил задачу ({task_type} на {task_date}): {task_text}"})

            if current_user["role"] in ["director", "rop"]:
                requested_manager = request.form.get("manager")
                if requested_manager:
                    d["manager"] = requested_manager
            
            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            
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
            d["phone"] = request.form.get("phone")
            d["region"] = request.form.get("region")
            break
            
    save_db(db)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
