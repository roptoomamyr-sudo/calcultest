# -*- coding: utf-8 -*-
import json
import os
import openpyxl
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

INPUT_FILE = "baza_selkhoz.xlsx"
DATA_FILE = "crm_db.json"

# Список ответственных сотрудников
MANAGERS = [
    "Не назначен",
    "РОП Лемперт Александр Сергеевич",
    "Директор Уралбаев Жанайдар Абишевич",
    "Менеджер 1",
    "Менеджер 2",
    "Менеджер 3"
]

STAGE_CONFIG = [
    {"name": "1. Новый клиент", "color": "#f8f9fa", "text": "#212529", "border": "#dee2e6"},
    {"name": "2. Нужно выйти на ЛПР", "color": "#5a6268", "text": "#ffffff", "border": "#4e555b"},
    {"name": "3. Скинул презентацию / инфу", "color": "#0dcaf0", "text": "#ffffff", "border": "#0bacce"},
    {"name": "4. Скинул КП", "color": "#20c997", "text": "#ffffff", "border": "#1baa80"},
    {"name": "5. Нет обратной связи", "color": "#ffc107", "text": "#000000", "border": "#d39e00"},
    {"name": "6. Веду переговоры", "color": "#0d6efd", "text": "#ffffff", "border": "#0b5ed7"},
    {"name": "7. Отложил / Передумал", "color": "#dc3545", "text": "#ffffff", "border": "#bb2d3b"},
    {"name": "8. Купил у конкурентов", "color": "#842029", "text": "#ffffff", "border": "#5c161d"},
    {"name": "9. Готов контрактоваться", "color": "#198754", "text": "#ffffff", "border": "#157347"},
    {"name": "10. Сделали договор", "color": "#0f5132", "text": "#ffffff", "border": "#0a3622"},
    {"name": "11. Внес предоплату", "color": "#a855f7", "text": "#ffffff", "border": "#9333ea"},
    {"name": "12. Выполнен (Дебиторка)", "color": "#6f42c1", "text": "#ffffff", "border": "#59359a"},
    {"name": "13. Оплачен полностью", "color": "#10b981", "text": "#ffffff", "border": "#059669"},
    {"name": "14. ⭐ Повторный заказ (VIP)", "color": "#ffd700", "text": "#000000", "border": "#b8860b"}
]

STAGES = [s["name"] for s in STAGE_CONFIG]

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass

    kanban_data = {stage: [] for stage in STAGES}
    try:
        wb = openpyxl.load_workbook(INPUT_FILE, data_only=True)
        sheet = wb.active
    except Exception as e:
        print(f"Ошибка загрузки Excel: {e}")
        return kanban_data

    for idx, row in enumerate(sheet.iter_rows(min_row=2), start=1):
        row_vals = [cell.value if cell.value is not None else "" for cell in row]
        if not any(row_vals):
            continue

        fill_color = row[0].fill.start_color.rgb if row[0].fill and row[0].fill.start_color else None
        target_stage = "1. Новый клиент"

        if fill_color:
            color_str = str(fill_color).upper()
            if "00FF00" in color_str or "92D050" in color_str or "C6EFCE" in color_str:
                target_stage = "4. Скинул КП"
            elif "00B0F0" in color_str or "BDD7EE" in color_str:
                target_stage = "3. Скинул презентацию / инфу"
            elif "FF0000" in color_str or "FFC7CE" in color_str or "F8CBAD" in color_str:
                target_stage = "7. Отложил / Передумал"

        initial_note = str(row_vals[7]) if len(row_vals) > 7 else ""
        card = {
            "id": f"client_{idx}",
            "company": str(row_vals[1]) if len(row_vals) > 1 else "Без названия",
            "name": str(row_vals[2]) if len(row_vals) > 2 else "",
            "phone": str(row_vals[3]) if len(row_vals) > 3 else "",
            "business": str(row_vals[4]) if len(row_vals) > 4 else "",
            "region": str(row_vals[5]) if len(row_vals) > 5 else "",
            "district": str(row_vals[6]) if len(row_vals) > 6 else "",
            "manager": "Не назначен",
            "note": initial_note,
            "history": [initial_note] if initial_note else ["Импорт из Excel"],
            "stage": target_stage
        }
        kanban_data[target_stage].append(card)

    save_data(kanban_data)
    return kanban_data

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@app.route("/")
def index():
    data = load_data()
    return render_template_string(
        HTML_TEMPLATE, 
        stage_config=STAGE_CONFIG, 
        managers=MANAGERS,
        data_json=json.dumps(data, ensure_ascii=False)
    )

@app.route("/update_card", methods=["POST"])
def update_card():
    req = request.json
    card_id = req.get("id")
    new_stage = req.get("stage")
    new_comment = req.get("comment")
    new_manager = req.get("manager")

    data = load_data()
    found_card = None

    for stage, cards in data.items():
        for card in cards:
            if card["id"] == card_id:
                found_card = card
                break
        if found_card:
            break

    if found_card:
        if new_comment:
            found_card["history"].insert(0, new_comment)
            found_card["note"] = new_comment
        
        if new_manager:
            found_card["manager"] = new_manager

        if new_stage and new_stage != found_card["stage"]:
            data[found_card["stage"]] = [c for c in data[found_card["stage"]] if c["id"] != card_id]
            found_card["stage"] = new_stage
            data[new_stage].append(found_card)

        save_data(data)
        return jsonify({"status": "success"})

    return jsonify({"status": "not_found"}), 404

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Bitrix24 Style CRM - Ангары</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.3/dragula.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.3/dragula.min.css">
    <style>
        body { background-color: #eef2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow-x: auto; }
        .kanban-board { display: flex; padding: 20px; gap: 12px; min-width: 4100px; }
        .kanban-column { background: #e2e8f0; border-radius: 8px; width: 270px; min-height: 80vh; display: flex; flex-direction: column; }
        .column-header { padding: 12px; font-weight: bold; font-size: 13px; text-align: center; border-radius: 8px 8px 0 0; }
        .kanban-cards { padding: 10px; flex-grow: 1; min-height: 200px; }
        .kanban-card { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); cursor: pointer; border-left: 5px solid #0078d4; }
        .card-title { font-weight: bold; font-size: 14px; color: #1e293b; margin-bottom: 4px; }
        .card-subtitle { font-size: 12px; color: #64748b; margin-bottom: 4px; }
        .card-phone { font-size: 12px; font-weight: 600; color: #10b981; }
        .card-manager { font-size: 11px; background: #e0e7ff; color: #3730a3; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
        .card-badge { font-size: 10px; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #475569; }
        .info-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="p-3 bg-white border-bottom d-flex justify-content-between align-items-center shadow-sm">
        <h4 class="m-0 text-primary">🚀 CRM Воронка Ангары (Битрикс24)</h4>
        <span class="badge bg-success px-3 py-2">Облачная CRM Активна</span>
    </div>

    <div class="kanban-board">
        {% for stage in stage_config %}
        <div class="kanban-column" data-stage="{{ stage.name }}">
            <div class="column-header" style="background: {{ stage.color }}; color: {{ stage.text }}; border-bottom: 3px solid {{ stage.border }};">
                {{ stage.name }}
            </div>
            <div class="kanban-cards" id="stage-{{ loop.index0 }}"></div>
        </div>
        {% endfor %}
    </div>

    <div class="modal fade" id="clientModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header bg-primary text-white">
                    <h5 class="modal-title" id="mCompany">Карточка клиента</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Наименование:</label>
                                <div id="mCompanyVal" class="fs-6 fw-bold text-dark"></div>
                            </div>
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Контактное лицо (ЛПР):</label>
                                <div id="mNameVal" class="text-secondary"></div>
                            </div>
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Номер телефона:</label>
                                <div id="mPhoneVal" class="text-success fw-bold fs-5"></div>
                            </div>
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Ответственный менеджер:</label>
                                <select id="mManagerSelect" class="form-select form-select-sm mt-1">
                                    {% for mgr in managers %}
                                    <option value="{{ mgr }}">{{ mgr }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Направление бизнеса:</label>
                                <div id="mBusinessVal" class="text-secondary"></div>
                            </div>
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Регион и район:</label>
                                <div id="mRegionVal" class="text-secondary"></div>
                            </div>
                            <div class="info-box">
                                <label class="fw-bold text-secondary small">Текущий этап воронки:</label>
                                <select id="mStageSelect" class="form-select form-select-sm mt-1">
                                    {% for stage in stage_config %}
                                    <option value="{{ stage.name }}">{{ stage.name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                        </div>
                    </div>

                    <hr>
                    <h6 class="text-primary fw-bold">💬 История действий и комментарии</h6>
                    <div class="mb-3">
                        <textarea id="newCommentInput" class="form-control" rows="2" placeholder="Напишите результат общения..."></textarea>
                        <button class="btn btn-sm btn-success mt-2" onclick="addComment()">Добавить комментарий</button>
                    </div>
                    <div class="info-box" style="max-height: 150px; overflow-y: auto;">
                        <ul id="mHistoryList" class="mb-0 ps-3 text-secondary small"></ul>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Закрыть</button>
                    <button type="button" class="btn btn-primary" onclick="saveCardChanges()">Сохранить изменения</button>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        const initialData = {{ data_json | safe }};
        const stageConfig = {{ stage_config | safe }};
        let currentCard = null;
        let modal = new bootstrap.Modal(document.getElementById('clientModal'));

        const containers = [];
        stageConfig.forEach((stageObj, idx) => {
            const container = document.getElementById(`stage-${idx}`);
            containers.push(container);

            if (initialData[stageObj.name]) {
                initialData[stageObj.name].forEach(card => {
                    renderCard(card, container, stageObj);
                });
            }
        });

        function renderCard(card, container, stageObj) {
            const cardEl = document.createElement('div');
            cardEl.className = 'kanban-card';
            cardEl.setAttribute('data-id', card.id);
            cardEl.style.borderLeftColor = stageObj.color;
            
            cardEl.innerHTML = `
                <div class="card-title">${card.company}</div>
                <div class="card-subtitle">👤 ${card.name || 'Нет данных'}</div>
                <div class="card-phone">📞 ${card.phone || 'Нет телефона'}</div>
                <div class="mt-2 d-flex justify-content-between align-items-center">
                    <span class="card-badge">📍 ${card.region || 'Регион'}</span>
                    <span class="card-manager">👨‍💼 ${card.manager || 'Не назначен'}</span>
                </div>
                ${card.note ? `<div class="mt-1 text-muted text-truncate" style="font-size:11px;">📝 ${card.note}</div>` : ''}
            `;
            cardEl.onclick = () => openCardModal(card);
            container.appendChild(cardEl);
        }

        function openCardModal(card) {
            currentCard = card;
            document.getElementById('mCompany').innerText = card.company;
            document.getElementById('mCompanyVal').innerText = card.company;
            document.getElementById('mNameVal').innerText = card.name || 'Не указано';
            document.getElementById('mPhoneVal').innerText = card.phone || 'Не указан';
            document.getElementById('mBusinessVal').innerText = card.business || 'Не указано';
            document.getElementById('mRegionVal').innerText = (card.region || '') + (card.district ? ', ' + card.district : '');
            document.getElementById('mStageSelect').value = card.stage;
            document.getElementById('mManagerSelect').value = card.manager || 'Не назначен';
            document.getElementById('newCommentInput').value = '';

            const historyList = document.getElementById('mHistoryList');
            historyList.innerHTML = '';
            if (card.history && card.history.length > 0) {
                card.history.forEach(item => {
                    const li = document.createElement('li');
                    li.innerText = item;
                    historyList.appendChild(li);
                });
            } else {
                historyList.innerHTML = '<li>Нет записей</li>';
            }

            modal.show();
        }

        function addComment() {
            const commentText = document.getElementById('newCommentInput').value.trim();
            if (!commentText) return;
            
            if (!currentCard.history) currentCard.history = [];
            currentCard.history.unshift(commentText);
            currentCard.note = commentText;

            const historyList = document.getElementById('mHistoryList');
            const li = document.createElement('li');
            li.innerText = commentText;
            historyList.prepend(li);
            document.getElementById('newCommentInput').value = '';
        }

        function saveCardChanges() {
            if (!currentCard) return;
            const newStage = document.getElementById('mStageSelect').value;
            const newManager = document.getElementById('mManagerSelect').value;
            const commentText = document.getElementById('newCommentInput').value.trim();

            fetch('/update_card', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: currentCard.id,
                    stage: newStage,
                    manager: newManager,
                    comment: commentText || null
                })
            }).then(res => res.json()).then(res => {
                if (res.status === 'success') {
                    location.reload();
                }
            });
        }

        dragula(containers).on('drop', function (el, target, source) {
            const cardId = el.getAttribute('data-id');
            const newStage = target.parentElement.getAttribute('data-stage');
            
            fetch('/update_card', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: cardId,
                    stage: newStage,
                    comment: null
                })
            });
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
