# tg_bot

# 🏯 Ulan-Ude Guide Bot

Telegram-бот для поиска достопримечательностей, отелей и ресторанов Улан-Удэ.

## ⚙️ Технологии

- Python 3.10+
- `python-telegram-bot` v20 (async)
- SQLite (данные)
- `geopy` (геопоиск)

## 📁 Структура
bot/
├── main.py # Запуск
├── handlers/ # Обработчики команд
├── keyboards/ # Клавиатуры
├── models/ # Работа с БД
└── utils/geo.py # Расчёт расстояний
data/ # places.json, ulanude.db

📄 Лицензия
MIT
