# -*- coding: utf-8 -*-
import json
import openpyxl
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

INPUT_FILE = "baza_selkhoz.xlsx"
DATA_FILE = "crm_data.json"

STAGES = [
    "1. Новый клиент",
    "2. Нужно выйти на ЛПР",
    "3. Скинул презентацию / инфу",
    "4. Скинул КП",
    "5. Нет обратной связи",
    "6. Веду переговоры",
    "7. Отложил / Передумал",
    "8. Купил у конкурентов",
    "9. Готов контрактоваться",
    "10. Сделали договор",
    "11. Внес предоплату",
    "12. Выполнен (Дебиторка)",
    "13. Оплачен полностью",
    "14. ⭐ Повторный заказ (VIP)"
]

def load_initial_excel():
    """Считывает Excel с учетом цветов строк и превращает в карточки клиентов"""
    try:
        wb = openpyxl.load_workbook(INPUT_FILE, data_only=True)
        sheet = wb.active
    except Exception as e:
        print(f"Ошибка загрузки Excel: {e}")
        return {stage: [] for stage in STAGES}

    kanban_data = {stage: [] for stage in STAGES}

    for idx, row in enumerate(sheet.iter_rows(min_row=2), start=2):
        row_vals = [cell.value if cell.value is not None else "" for cell in row]
        if not any(row_vals):
            continue

        # Считываем цвет первой ячейки
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

        card = {
            "id": f"client_{idx}",
            "company": str(row_vals[1]) if len(row_vals) > 1 else "Без названия",
            "name": str(row_vals[2]) if len(row_vals) > 2 else "",
            "phone": str(row_vals[3]) if len(row_vals) > 3 else "",
            "business": str(row_vals[4]) if len(row_vals) > 4 else "",
            "region": str(row_vals[5]) if len(row_vals) > 5 else "",
            "district": str(row_vals[6]) if len(row_vals) > 6 else "",
            "note": str(row_vals[7]) if len(row_vals) > 7 else "",
            "stage": target_stage
        }
        kanban_data[target_stage].append(card)

    return kanban_data

@app.route("/")
def index():
    data = load_initial_excel()
    return render_template_string(HTML_TEMPLATE, stages=STAGES, data_json=json.dumps(data, ensure_ascii=False))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Bitrix24 Style CRM - Воронка</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.3/dragula.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.3/dragula.min.css">
    <style>
        body { background-color: #eef2f5; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; overflow-x: auto; }
        .kanban-board { display: flex; padding: 20px; gap: 15px; min-width: 3800px; }
        .kanban-column { background: #e2e8f0; border-radius: 8px; width: 260px; min-height: 80vh; display: flex; flex-direction: column; }
        .column-header { padding: 12px; font-weight: bold; font-size: 14px; text-align: center; border-radius: 8px 8px 0 0; color: #fff; background: #2b5797; }
        .column-header.vip { background: linear-gradient(45deg, #d4af37, #ffd700); color: #000; }
        .kanban-cards { padding: 10px; flex-grow: 1; min-height: 200px; }
        .kanban-card { background: #fff; border-radius: 6px; padding: 12px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); cursor: grab; border-left: 4px solid #0078d4; }
        .kanban-card:active { cursor: grabbing; }
        .card-title { font-weight: bold; font-size: 14px; color: #1e293b; margin-bottom: 4px; }
        .card-subtitle { font-size: 12px; color: #64748b; margin-bottom: 6px; }
        .card-phone { font-size: 12px; font-weight: 600; color: #10b981; }
        .card-badge { font-size: 10px; background: #f1f5f9; padding: 2px 6px; border-radius: 4px; color: #475569; }
    </style>
</head>
<body>
    <div class="p-3 bg-white border-bottom d-flex justify-content-between align-items-center">
        <h4 class="m-0 text-primary">🚀 CRM Воронка Ангары (Битрикс24)</h4>
        <span class="badge bg-success">База подключена</span>
    </div>

    <div class="kanban-board">
        {% for stage in stages %}
        <div class="kanban-column">
            <div class="column-header {% if 'VIP' in stage %}vip{% endif %}">{{ stage }}</div>
            <div class="kanban-cards" id="stage-{{ loop.index }}">
                <!-- Карточки загружаются JS -->
            </div>
        </div>
        {% endfor %}
    </div>

    <script>
        const initialData = {{ data_json | safe }};
        const containers = [];

        Object.keys(initialData).forEach((stage, idx) => {
            const container = document.getElementById(`stage-${idx + 1}`);
            containers.push(container);

            initialData[stage].forEach(card => {
                const cardEl = document.createElement('div');
                cardEl.className = 'kanban-card';
                cardEl.setAttribute('data-id', card.id);
                cardEl.innerHTML = `
                    <div class="card-title">${card.company}</div>
                    <div class="card-subtitle">👤 ${card.name}</div>
                    <div class="card-phone">📞 ${card.phone}</div>
                    <div class="mt-2 d-flex justify-content-between">
                        <span class="card-badge">📍 ${card.region}</span>
                        <span class="card-badge">${card.business}</span>
                    </div>
                    ${card.note ? `<div class="mt-1 text-muted" style="font-size:11px;">📝 ${card.note}</div>` : ''}
                `;
                container.appendChild(cardEl);
            });
        });

        // Инициализация Drag-and-Drop
        dragula(containers).on('drop', function (el, target, source) {
            console.log('Карточка перенесена в столбец:', target.previousElementSibling.innerText);
        });
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(debug=True, port=5000)
