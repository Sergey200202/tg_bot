import os
import requests
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEATHER_API = os.getenv('WEATHER_API_KEY')
VISUAL_CROSSING_API_KEY = 0

application = Application.builder().token(TOKEN).build()

ULAN_UDE_COORDS = {
    'lat': 51.8345,
    'lon': 107.5845,
    'name': 'Улан-Удэ',
    'country': 'Россия'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌤️ Погода сейчас", callback_data="weather")],
        [InlineKeyboardButton("📅 Прогноз на 3 дня", callback_data="forecast")],
        [InlineKeyboardButton("🏛️ Достопримечательности", callback_data="attractions")],
        [InlineKeyboardButton("🍽️ Рестораны", callback_data="restaurants")],
        [InlineKeyboardButton("🏨 Отели", callback_data="hotels")],
        [InlineKeyboardButton("🛍️ Магазины", callback_data="shops")],
        [InlineKeyboardButton("ℹ️ О городе", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = """
🏙️ Добро пожаловать в бот-гид по Улан-Удэ!

Я расскажу тебе всё о столице солнечной Бурятии:

• 🌤️ Текущая погода и прогноз
• 🏛️ Главные достопримечательности 
• 🍽️ Лучшие рестораны и кафе
• 🏨 Где остановиться
• 🛍️ Магазины и ТЦ
• ℹ️ Интересные факты о городе

Выбери, что хочешь узнать!
    """

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    if action == 'weather':
        await show_weather(query)
    elif action == 'forecast':
        await show_forecast(query)
    elif action == 'attractions':
        await show_attractions(query)
    elif action == 'restaurants':
        await show_restaurants(query)
    elif action == 'hotels':
        await show_hotels(query)
    elif action == 'shops':
        await show_shops(query)
    elif action == 'about':
        await show_about(query)
    
    await show_main_menu(query)

def get_weather_visual_crossing():
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Ulan-Ude?unitGroup=metric&include=current&key={VISUAL_CROSSING_API_KEY}&contentType=json&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        current = data['currentConditions']
        
        weather_info = {
            "city": "Улан-Удэ",
            "country": "Россия",
            "temp": round(current['temp']),
            "feels_like": round(current['feelslike']),
            "description": current['conditions'],
            "humidity": round(current['humidity'] * 100),
            "pressure": round(current['pressure']),
            "wind_speed": round(current['windspeed'] * 0.27778, 1),  # km/h to m/s
            "visibility": round(current['visibility'] * 1000),  # km to m
            "uv_index": current.get('uvindex', 0),
            "sunrise": data['days'][0].get('sunrise', 'N/A'),
            "sunset": data['days'][0].get('sunset', 'N/A')
        }
        
        return weather_info, None
        
    except Exception as e:
        return None, f"Ошибка получения погоды: {str(e)}"


def get_weather_weatherapi():
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API}&q=Ulan-Ude&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        current = data['current']
        
        weather_info = {
            "city": data['location']['name'],
            "country": data['location']['country'],
            "temp": round(current['temp_c']),
            "feels_like": round(current['feelslike_c']),
            "description": current['condition']['text'],
            "humidity": current['humidity'],
            "pressure": current['pressure_mb'],
            "wind_speed": round(current['wind_kph'] * 0.27778, 1),  # km/h to m/s
            "visibility": current['vis_km'] * 1000,  # km to m
            "uv_index": current.get('uv', 0),
            "wind_dir": current['wind_dir'],
            "updated": current['last_updated']
        }
        
        return weather_info, None
        
    except Exception as e:
        return None, f"Ошибка получения погоды: {str(e)}"

# Получение прогноза погоды
def get_weather_forecast():
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Ulan-Ude?unitGroup=metric&include=days&key={VISUAL_CROSSING_API_KEY}&contentType=json&lang=ru"
        response = requests.get(url)
        data = response.json()
        
        forecast = []
        for day in data['days'][:3]:  # Берем 3 дня
            forecast.append({
                'datetime': day['datetime'],
                'temp_max': round(day['tempmax']),
                'temp_min': round(day['tempmin']),
                'description': day['conditions'],
                'humidity': round(day['humidity'] * 100),
                'precip': day.get('precip', 0),
                'wind_speed': round(day['windspeed'] * 0.27778, 1)
            })
        
        return forecast, None
        
    except Exception as e:
        return None, f"Ошибка получения прогноза: {str(e)}"

# Функции отображения информации
async def show_weather(query):
    # Пробуем разные источники погоды
    weather_info, error = get_weather_visual_crossing()
    
    if error:
        # Если первый источник не сработал, пробуем второй
        weather_info, error = get_weather_weatherapi()
    
    if error:
        await query.edit_message_text(f"❌ {error}")
        return
    
    weather_emojis = {
        "ясно": "☀️", "солнечно": "☀️", "облачно": "☁️", "пасмурно": "☁️",
        "дождь": "🌧️", "снег": "❄️", "гроза": "⛈️", "туман": "🌫️",
        "небольшой дождь": "🌦️", "небольшой снег": "🌨️"
    }
    
    weather_desc = weather_info["description"].lower()
    emoji = "🌤️"
    for key, value in weather_emojis.items():
        if key in weather_desc:
            emoji = value
            break
    
    # Форматируем время восхода и заката, если есть
    sunrise_sunset = ""
    if 'sunrise' in weather_info and weather_info['sunrise'] != 'N/A':
        sunrise_sunset = f"🌅 Восход: {weather_info['sunrise'][11:16]}\n🌇 Закат: {weather_info['sunset'][11:16]}\n"
    
    response_text = f"""
{emoji} *Погода в Улан-Удэ сейчас*

🌡️ Температура: *{weather_info['temp']}°C*
💭 Ощущается как: *{weather_info['feels_like']}°C*
📝 *{weather_info['description']}*
💧 Влажность: *{weather_info['humidity']}%*
📊 Давление: *{weather_info['pressure']} hPa*
💨 Ветер: *{weather_info['wind_speed']} m/s*
👁️ Видимость: *{weather_info['visibility']} м*
☀️ УФ-индекс: *{weather_info['uv_index']}*

{sunrise_sunset}
*Обновлено:* {datetime.now().strftime('%H:%M')}
    """
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_forecast(query):
    forecast, error = get_weather_forecast()
    
    if error:
        await query.edit_message_text(f"❌ {error}")
        return
    
    response_text = "📅 *Прогноз погоды в Улан-Удэ на 3 дня:*\n\n"
    
    for day in forecast:
        # Преобразуем дату в читаемый формат
        date_obj = datetime.strptime(day['datetime'], '%Y-%m-%d')
        date_str = date_obj.strftime('%d.%m')
        day_name = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'][date_obj.weekday()]
        
        weather_emojis = {
            "ясно": "☀️", "солнечно": "☀️", "облачно": "☁️", "пасмурно": "☁️",
            "дождь": "🌧️", "снег": "❄️", "гроза": "⛈️", "туман": "🌫️"
        }
        
        weather_desc = day['description'].lower()
        emoji = "🌤️"
        for key, value in weather_emojis.items():
            if key in weather_desc:
                emoji = value
                break
        
        precip_text = ""
        if day['precip'] > 0:
            precip_text = f"💧 Осадки: {day['precip']}mm\n"
        
        response_text += f"""
{emoji} *{day_name}, {date_str}*
📈 Макс: *{day['temp_max']}°C* | 📉 Мин: *{day['temp_min']}°C*
📝 {day['description']}
💨 Ветер: {day['wind_speed']} m/s
{precip_text}
"""
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

# Остальные функции (show_attractions, show_restaurants и т.д.) остаются без изменений
async def show_attractions(query):
    attractions = [
        {
            'name': 'Памятник Ленину (Голова Ленина)',
            'description': 'Самая большая голова Ленина в мире - визитная карточка города',
            'address': 'пл. Советов',
            'emoji': '🗿'
        },
        {
            'name': 'Этнографический музей народов Забайкалья',
            'description': 'Музей под открытым небом с традиционными бурятскими жилищами',
            'address': 'пос. Верхняя Берёзовка, 17Б',
            'emoji': '🏕️'
        },
        {
            'name': 'Иволгинский дацан',
            'description': 'Центр буддизма в России, резиденция Пандито Хамбо-ламы',
            'address': 'с. Верхняя Иволга (40 км от города)',
            'emoji': '🕌'
        },
        {
            'name': 'Театр оперы и балета',
            'description': 'Красивейшее здание в национальном стиле',
            'address': 'ул. Ленина, 51',
            'emoji': '🎭'
        },
        {
            'name': 'Площадь Революции',
            'description': 'Исторический центр города с фонтанами и сквером',
            'address': 'пл. Революции',
            'emoji': '🏛️'
        },
        {
            'name': 'Свято-Одигитриевский собор',
            'description': 'Первый каменный храм в Забайкалье',
            'address': 'ул. Ленина, 2',
            'emoji': '⛪'
        }
    ]
    
    response_text = "🏛️ *Главные достопримечательности Улан-Удэ:*\n\n"
    
    for i, attr in enumerate(attractions, 1):
        response_text += f"{i}. {attr['emoji']} *{attr['name']}*\n"
        response_text += f"   📍 {attr['address']}\n"
        response_text += f"   ℹ️ {attr['description']}\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_restaurants(query):
    restaurants = [
        {
            'name': 'Ресторан "Бурятия"',
            'cuisine': 'Бурятская, русская',
            'address': 'ул. Ербанова, 7',
            'specialty': 'Позы, буузы, бухлер',
            'emoji': '🍖'
        },
        {
            'name': 'Кафе "Баатар"',
            'cuisine': 'Бурятская, азиатская',
            'address': 'пр. 50-летия Октября, 33',
            'specialty': 'Традиционные бурятские блюда',
            'emoji': '🥟'
        },
        {
            'name': 'Ресторан "Медведь"',
            'cuisine': 'Европейская, русская',
            'address': 'ул. Ленина, 46',
            'specialty': 'Блюда из дичи и рыбы Байкала',
            'emoji': '🐟'
        },
        {
            'name': 'Чайная "Юрта"',
            'cuisine': 'Бурятская, чайная церемония',
            'address': 'ул. Борсоева, 15',
            'specialty': 'Бурятский чай с молоком',
            'emoji': '🍵'
        },
        {
            'name': 'Ресторан "Саган Морин"',
            'cuisine': 'Бурятская, монгольская',
            'address': 'ул. Революции 1905 года, 44',
            'specialty': 'Блюда в аутентичной атмосфере',
            'emoji': '🏇'
        }
    ]
    
    response_text = "🍽️ *Лучшие рестораны Улан-Удэ:*\n\n"
    
    for i, rest in enumerate(restaurants, 1):
        response_text += f"{i}. {rest['emoji']} *{rest['name']}*\n"
        response_text += f"   📍 {rest['address']}\n"
        response_text += f"   🍳 {rest['cuisine']}\n"
        response_text += f"   👑 {rest['specialty']}\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_hotels(query):
    hotels = [
        {
            'name': 'Гостиница "Бурятия"',
            'stars': '⭐⭐⭐⭐',
            'address': 'ул. Ербанова, 12',
            'features': 'Бассейн, ресторан, Wi-Fi',
            'price': 'от 3500 руб/ночь',
            'emoji': '🏨'
        },
        {
            'name': 'Отель "Мэрген"',
            'stars': '⭐⭐⭐',
            'address': 'ул. Гагарина, 25',
            'features': 'SPA, парковка, завтрак включен',
            'price': 'от 2800 руб/ночь',
            'emoji': '🛌'
        },
        {
            'name': 'Гостиница "Сагаан Морин"',
            'stars': '⭐⭐⭐⭐',
            'address': 'ул. Борсоева, 18',
            'features': 'Бизнес-центр, конференц-зал',
            'price': 'от 3200 руб/ночь',
            'emoji': '💼'
        },
        {
            'name': 'Мини-отель "Байкал Плаза"',
            'stars': '⭐⭐⭐',
            'address': 'пр. 50-летия Октября, 29',
            'features': 'Центр города, вид на город',
            'price': 'от 2200 руб/ночь',
            'emoji': '🌆'
        }
    ]
    
    response_text = "🏨 *Отели Улан-Удэ:*\n\n"
    
    for i, hotel in enumerate(hotels, 1):
        response_text += f"{i}. {hotel['emoji']} *{hotel['name']}*\n"
        response_text += f"   {hotel['stars']}\n"
        response_text += f"   📍 {hotel['address']}\n"
        response_text += f"   🎯 {hotel['features']}\n"
        response_text += f"   💰 {hotel['price']}\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_shops(query):
    shops = [
        {
            'name': 'ТЦ "Форум"',
            'type': 'Крупнейший торговый центр',
            'address': 'ул. Ербанова, 3',
            'features': '200+ магазинов, фудкорт, кинотеатр',
            'emoji': '🏬'
        },
        {
            'name': 'ТРЦ "Пионер"',
            'type': 'Торгово-развлекательный центр',
            'address': 'ул. Революции 1905 года, 33',
            'features': 'Магазины, кафе, развлечения',
            'emoji': '🎯'
        },
        {
            'name': 'Рынок "Центральный"',
            'type': 'Продуктовый рынок',
            'address': 'ул. Каландаришвили, 39',
            'features': 'Свежие продукты, сувениры',
            'emoji': '🛒'
        },
        {
            'name': 'Сувенирная лавка "Байкальские дары"',
            'type': 'Сувениры',
            'address': 'ул. Ленина, 27',
            'features': 'Бурятские сувениры, чай, кедровые орехи',
            'emoji': '🎁'
        }
    ]
    
    response_text = "🛍️ *Магазины и ТЦ Улан-Удэ:*\n\n"
    
    for i, shop in enumerate(shops, 1):
        response_text += f"{i}. {shop['emoji']} *{shop['name']}*\n"
        response_text += f"   🏬 {shop['type']}\n"
        response_text += f"   📍 {shop['address']}\n"
        response_text += f"   🎯 {shop['features']}\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_about(query):
    about_text = """
🏙️ *Улан-Удэ - столица Бурятии*

*Основная информация:*
• 📍 Расположение: Восточная Сибирь, в 100 км от Байкала
• 👥 Население: ~437,000 человек
• 🗓️ Основан: 1666 год
• 🌆 Статус: Столица Республики Бурятия

*Интересные факты:*
• 🗿 Имеет самую большую скульптуру головы Ленина в мире
• 🕌 Крупный центр буддизма в России
• 🌍 Единственный город, где представлены 3 мировые религии: православие, буддизм и ислам
• 🏔️ Расположен в долине рек Селенга и Уда

*Климат:*
• ❄️ Резко континентальный климат
• 🌡️ Средняя температура января: -25°C
• 🌡️ Средняя температура июля: +20°C
• ☀️ Более 260 солнечных дней в году

*Культура:*
• 🎭 Известен Театром оперы и балета
• 🥟 Родина знаменитых бурятских поз (бууз)
• 🎪 Центр бурятской национальной культуры

*Туризм:*
• 🚗 Ворота к озеру Байкал
• 🏕️ Богатая этнографическая культура
• 🍖 Уникальная бурятская кухня
• 🛕 Буддийские дацаны и монастыри
    """
    await query.edit_message_text(about_text, parse_mode='Markdown')

# Показать главное меню
async def show_main_menu(query):
    keyboard = [
        [InlineKeyboardButton("🌤️ Погода сейчас", callback_data="weather")],
        [InlineKeyboardButton("📅 Прогноз на 3 дня", callback_data="forecast")],
        [InlineKeyboardButton("🏛️ Достопримечательности", callback_data="attractions")],
        [InlineKeyboardButton("🍽️ Рестораны", callback_data="restaurants")],
        [InlineKeyboardButton("🏨 Отели", callback_data="hotels")],
        [InlineKeyboardButton("🛍️ Магазины", callback_data="shops")],
        [InlineKeyboardButton("ℹ️ О городе", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "Что ещё хочешь узнать об Улан-Удэ?"
    
    await query.message.reply_text(text, reply_markup=reply_markup)

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    
    if any(word in text for word in ['улан', 'улан-удэ', 'уланудэ', 'бурятия', 'погода']):
        await show_main_menu(update.message)
    else:
        response = """
🏙️ Привет! Я бот-гид по Улан-Удэ.

Я специализируюсь только на столице Бурятии. Используй кнопки меню или команду /start чтобы узнать всё об этом замечательном городе!

*Интересные факты об Улан-Удэ:*
• Город основан в 1666 году
• Здесь находится самая большая голова Ленина в мире
• Столица буддизма в России
• Более 260 солнечных дней в году
        """
        await update.message.reply_text(response, parse_mode='Markdown')

# Команда /info
async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🏙️ *Бот-гид по Улан-Удэ - Справка*

*Доступные команды:*
/start - Главное меню
/info - Эта справка

*Я могу рассказать о:*
• 🌤️ Текущей погоде в Улан-Удэ
• 📅 Прогнозе погоды на 3 дня
• 🏛️ Главных достопримечательностях
• 🍽️ Лучших ресторанах и кафе
• 🏨 Гостиницах и отелях
• 🛍️ Магазинах и ТЦ
• ℹ️ Интересных фактах о городе

*Просто используй кнопки меню!*
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Основная функция
def main():
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🏙️ Бот-гид по Улан-Удэ запущен!")
    application.run_polling()

if __name__ == '__main__':
    main()
