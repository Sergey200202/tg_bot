import os
import requests
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from dotenv import load_dotenv
from datetime import datetime
import time
from functools import lru_cache

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
WEATHER_API = os.getenv('WEATHER_API_KEY')
VISUAL_CROSSING_API_KEY = os.getenv('VISUAL_CROSSING_API_KEY', 'demo')

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

ULAN_UDE_COORDS = {
    'lat': 51.8345,
    'lon': 107.5845,
    'name': 'Улан-Удэ',
    'country': 'Россия'
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [[KeyboardButton("🚀 Начать")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    welcome_text = """
🏙️ Добро пожаловать в бот-гид по Улан-Удэ!

Я расскажу тебе всё о столице солнечной Бурятии:

• 🌤️ Текущая погода
• 📅 Текущая дата и время
• 🏛️ Главные достопримечательности 
• 🍽️ Лучшие рестораны и кафе
• 🏨 Где остановиться
• 🛍️ Магазины и ТЦ
• ℹ️ Интересные факты о городе

Нажми кнопку *"🚀 Начать"* ниже, чтобы открыть меню!
    """

    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия кнопки 'Начать'"""
    text = update.message.text
    
    if text == "🚀 Начать":
        await show_main_menu(update.message)

async def show_main_menu(message):
    """Показать главное меню с инлайн-кнопками"""
    keyboard = [
        [InlineKeyboardButton("📅 Текущая дата и время", callback_data="datetime")],
        [InlineKeyboardButton("🌤️ Погода сейчас", callback_data="weather")],
        [InlineKeyboardButton("🏛️ Достопримечательности", callback_data="attractions")],
        [InlineKeyboardButton("🍽️ Рестораны", callback_data="restaurants")],
        [InlineKeyboardButton("🏨 Отели", callback_data="hotels")],
        [InlineKeyboardButton("🛍️ Магазины", callback_data="shops")],
        [InlineKeyboardButton("ℹ️ О городе", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "🏙️ Выбери, что хочешь узнать об Улан-Удэ:"
    
    await message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия инлайн-кнопок"""
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    try:
        if action == 'weather':
            await show_weather(query)
        elif action == 'datetime':
            await show_current_datetime(query)
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
        
        # После выполнения действия показываем меню снова
        await show_main_menu_after_action(query)
        
    except Exception as e:
        logger.error(f"Error in button_handler: {e}")
        await query.edit_message_text("❌ Произошла ошибка при обработке запроса. Попробуйте позже.")

async def show_main_menu_after_action(query):
    """Показать главное меню после выполнения действия"""
    keyboard = [
        [InlineKeyboardButton("📅 Текущая дата и время", callback_data="datetime")],
        [InlineKeyboardButton("🌤️ Погода сейчас", callback_data="weather")],
        [InlineKeyboardButton("🏛️ Достопримечательности", callback_data="attractions")],
        [InlineKeyboardButton("🍽️ Рестораны", callback_data="restaurants")],
        [InlineKeyboardButton("🏨 Отели", callback_data="hotels")],
        [InlineKeyboardButton("🛍️ Магазины", callback_data="shops")],
        [InlineKeyboardButton("ℹ️ О городе", callback_data="about")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "Что ещё хочешь узнать об Улан-Удэ?"
    
    await query.message.reply_text(text, reply_markup=reply_markup)

def get_current_datetime_info():
    """Получение текущей даты и времени для Улан-Удэ"""
    try:
        # Улан-Удэ находится в часовом поясе UTC+8 (IRKT - Irkutsk Time)
        utc_offset = 8  # часовой пояс Улан-Удэ
        
        # Текущее время UTC
        utc_now = datetime.utcnow()
        
        # Время в Улан-Удэ
        ulan_ude_time = utc_now.replace(hour=(utc_now.hour + utc_offset) % 24)
        
        # Форматирование даты и времени
        current_date = ulan_ude_time.strftime('%d.%m.%Y')
        current_time = ulan_ude_time.strftime('%H:%M:%S')
        day_of_week = ulan_ude_time.strftime('%A')
        
        # Русские названия дней недели
        days_russian = {
            'Monday': 'Понедельник',
            'Tuesday': 'Вторник',
            'Wednesday': 'Среда',
            'Thursday': 'Четверг',
            'Friday': 'Пятница',
            'Saturday': 'Суббота',
            'Sunday': 'Воскресенье'
        }
        
        # Русские названия месяцев
        months_russian = {
            'January': 'января',
            'February': 'февраля',
            'March': 'марта',
            'April': 'апреля',
            'May': 'мая',
            'June': 'июня',
            'July': 'июля',
            'August': 'августа',
            'September': 'сентября',
            'October': 'октября',
            'November': 'ноября',
            'December': 'декабря'
        }
        
        day_name_ru = days_russian.get(day_of_week, day_of_week)
        month_name_ru = months_russian.get(ulan_ude_time.strftime('%B'), ulan_ude_time.strftime('%B'))
        
        # Красивое форматирование даты
        beautiful_date = f"{ulan_ude_time.day} {month_name_ru} {ulan_ude_time.year}"
        
        datetime_info = {
            'city': 'Улан-Удэ',
            'timezone': 'IRKT (UTC+8)',
            'current_date': current_date,
            'current_time': current_time,
            'day_of_week': day_name_ru,
            'beautiful_date': beautiful_date,
            'timestamp': ulan_ude_time.timestamp(),
            'day_number': ulan_ude_time.day,
            'month_number': ulan_ude_time.month,
            'year': ulan_ude_time.year,
            'hour': ulan_ude_time.hour,
            'minute': ulan_ude_time.minute,
            'second': ulan_ude_time.second
        }
        
        return datetime_info, None
        
    except Exception as e:
        return None, f"Ошибка получения времени: {str(e)}"

async def show_current_datetime(query):
    """Показать текущую дату и время в Улан-Удэ"""
    datetime_info, error = get_current_datetime_info()
    
    if error:
        logger.error(f"Datetime error: {error}")
        await query.edit_message_text(f"❌ {error}")
        return
    
    # Определяем приветствие по времени суток
    hour = datetime_info['hour']
    if 5 <= hour < 12:
        greeting = "🌅 Доброе утро!"
        time_emoji = "🌄"
    elif 12 <= hour < 18:
        greeting = "☀️ Добрый день!"
        time_emoji = "🏙️"
    elif 18 <= hour < 23:
        greeting = "🌇 Добрый вечер!"
        time_emoji = "🌆"
    else:
        greeting = "🌙 Доброй ночи!"
        time_emoji = "🌃"
    
    # Определяем сезон по месяцу
    month = datetime_info['month_number']
    if month in [12, 1, 2]:
        season_emoji = "❄️"
        season_text = "зима"
    elif month in [3, 4, 5]:
        season_emoji = "🌱"
        season_text = "весна"
    elif month in [6, 7, 8]:
        season_emoji = "☀️"
        season_text = "лето"
    else:
        season_emoji = "🍂"
        season_text = "осень"
    
    response_text = f"""
{time_emoji} *Текущая дата и время в Улан-Удэ*

{greeting}

📅 *Дата:* {datetime_info['beautiful_date']}
🕐 *Время:* {datetime_info['current_time']}
📆 *День недели:* {datetime_info['day_of_week']}
🌍 *Часовой пояс:* {datetime_info['timezone']}
{season_emoji} *Сезон:* {season_text}

*Интересные факты о времени в Улан-Удэ:*
• ⏰ Город находится в одном часовом поясе с Иркутском
• 🌞 Разница с Москвой: +5 часов
• 🗓️ Сегодня {datetime_info['day_number']}-й день месяца
• 📊 Текущий год: {datetime_info['year']}

*Обновлено:* {datetime.utcnow().strftime('%H:%M:%S')} UTC
    """
    await query.edit_message_text(response_text, parse_mode='Markdown')

def format_time(time_str):
    """Форматирование времени"""
    try:
        if 'T' in time_str:
            time_obj = datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S')
            return time_obj.strftime('%H:%M')
        return time_str
    except Exception:
        return time_str

@lru_cache(maxsize=1)
def get_weather_cached(api_type: str, cache_timeout=300):
    """Кэширование запросов погоды"""
    if api_type == "visual_crossing":
        return get_weather_visual_crossing()
    else:
        return get_weather_weatherapi()

def get_weather_visual_crossing():
    """Получение погоды через Visual Crossing API"""
    try:
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Ulan-Ude?unitGroup=metric&include=current&key={VISUAL_CROSSING_API_KEY}&contentType=json&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
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
            "wind_speed": round(current['windspeed'] * 0.27778, 1),
            "visibility": round(current['visibility'], 1),
            "uv_index": current.get('uvindex', 0),
            "sunrise": format_time(data['days'][0].get('sunrise', 'N/A')),
            "sunset": format_time(data['days'][0].get('sunset', 'N/A'))
        }
        
        return weather_info, None
        
    except requests.exceptions.Timeout:
        return None, "Таймаут при получении данных о погоде"
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка соединения: {str(e)}"
    except KeyError as e:
        return None, f"Неожиданный формат данных: {str(e)}"
    except Exception as e:
        return None, f"Ошибка получения погоды: {str(e)}"

def get_weather_weatherapi():
    """Получение погоды через WeatherAPI"""
    try:
        url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API}&q=Ulan-Ude&lang=ru"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        current = data['current']
        
        weather_info = {
            "city": data['location']['name'],
            "country": data['location']['country'],
            "temp": round(current['temp_c']),
            "feels_like": round(current['feelslike_c']),
            "description": current['condition']['text'],
            "humidity": current['humidity'],
            "pressure": round(current['pressure_mb']),
            "wind_speed": round(current['wind_kph'] * 0.27778, 1),
            "visibility": current['vis_km'],
            "uv_index": current.get('uv', 0),
            "wind_dir": current['wind_dir'],
            "updated": current['last_updated']
        }
        
        return weather_info, None
        
    except requests.exceptions.Timeout:
        return None, "Таймаут при получении данных о погоде"
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка соединения: {str(e)}"
    except KeyError as e:
        return None, f"Неожиданный формат данных: {str(e)}"
    except Exception as e:
        return None, f"Ошибка получения погоды: {str(e)}"

async def show_weather(query):
    """Показать текущую погоду"""
    # Пробуем разные источники погоды
    weather_info, error = get_weather_visual_crossing()
    
    if error:
        logger.warning(f"Visual Crossing API failed: {error}")
        weather_info, error = get_weather_weatherapi()
    
    if error:
        logger.error(f"Weather API failed: {error}")
        await query.edit_message_text(f"❌ {error}")
        return
    
    weather_emojis = {
        "ясно": "☀️", "солнечно": "☀️", "облачно": "☁️", "пасмурно": "☁️",
        "дождь": "🌧️", "снег": "❄️", "гроза": "⛈️", "туман": "🌫️",
        "небольшой дождь": "🌦️", "небольшой снег": "🌨️", "переменная облачность": "⛅"
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
        sunrise_sunset = f"🌅 Восход: {weather_info['sunrise']}\n🌇 Закат: {weather_info['sunset']}\n"
    
    response_text = f"""
{emoji} *Погода в Улан-Удэ сейчас*

🌡️ Температура: *{weather_info['temp']}°C*
💭 Ощущается как: *{weather_info['feels_like']}°C*
📝 *{weather_info['description']}*
💧 Влажность: *{weather_info['humidity']}%*
📊 Давление: *{weather_info['pressure']} гПа*
💨 Ветер: *{weather_info['wind_speed']} м/с*
👁️ Видимость: *{weather_info['visibility']} км*
☀️ УФ-индекс: *{weather_info['uv_index']}*

{sunrise_sunset}
*Обновлено:* {datetime.now().strftime('%H:%M')}
    """
    await query.edit_message_text(response_text, parse_mode='Markdown')

async def show_attractions(query):
    """Показать достопримечательности в виде альбома с фото по URL"""
    
    # Описание достопримечательностей
    attractions = [
        {
            'name': 'Памятник Ленину (Голова Ленина)',
            'description': 'Самая большая голова Ленина в мире - визитная карточка города',
            'address': 'пл. Советов',
            'emoji': '🗿',
            '2gis_url': 'https://go.2gis.com/WedTM',
            'photo_url': 'https://github.com/Sergey200202/tg_bot/blob/main/Images/lenin_head.JPG?raw=true'  
        },
        {
            'name': 'Этнографический музей народов Забайкалья',
            'description': 'Музей под открытым небом с традиционными бурятскими жилищами',
            'address': 'пос. Верхняя Берёзовка, 17Б',
            'emoji': '🏕️',
            '2gis_url': 'https://go.2gis.com/sHGKa',
            'photo_url': 'https://github.com/Sergey200202/tg_bot/blob/main/Images/ethno_museum.JPG?raw=true'  
        },
        {
            'name': 'Иволгинский дацан',
            'description': 'Центр буддизма в России, резиденция Пандито Хамбо-ламы',
            'address': 'с. Верхняя Иволга (40 км от города)',
            'emoji': '🕌',
            '2gis_url': 'https://go.2gis.com/quIAY',
            'photo_url': 'https://github.com/Sergey200202/tg_bot/blob/main/Images/datsan.JPG?raw=true'  
        },
        {
            'name': 'Театр оперы и балета',
            'description': 'Красивейшее здание в национальном стиле',
            'address': 'ул. Ленина, 51',
            'emoji': '🎭',
            '2gis_url': 'https://go.2gis.com/fqOTE',
            'photo_url': 'https://github.com/Sergey200202/tg_bot/blob/main/Images/opera_theater.JPG?raw=true'  
        },
        {
            'name': 'Площадь Революции',
            'description': 'Исторический центр города с фонтанами и сквером',
            'address': 'пл. Революции',
            'emoji': '🏛️',
            '2gis_url': 'https://go.2gis.com/pWgJs',
            'photo_url': 'https://github.com/Sergey200202/tg_bot/blob/main/Images/revolution_square.JPG?raw=true' 
        },
        {
            'name': 'Свято-Одигитриевский собор',
            'description': 'Первый каменный храм в Забайкалье',
            'address': 'ул. Ленина, 2',
            'emoji': '⛪',
            '2gis_url': 'https://go.2gis.com/6mGEz',
            'photo_url': 'https://github.com/Sergey200202/tg_bot/blob/main/Images/cathedral.JPG?raw=true'  
        }
    ]
    
    # Формируем общую подпись
    caption = "🏛️ *Главные достопримечательности Улан-Удэ:*\n\n"
    
    for i, attr in enumerate(attractions, 1):
        caption += f"{i}. {attr['emoji']} *{attr['name']}*\n"
        caption += f"   📍 {attr['address']}\n"
        caption += f"   ℹ️ {attr['description']}\n"
        caption += f"   🗺️ [Открыть в 2ГИС]({attr['2gis_url']})\n\n"
    
    # Создаем медиа-группу для альбома
    media_group = []
    
    # Для первого фото добавляем подпись, для остальных - только фото
    for i, attr in enumerate(attractions):
        if i == 0:
            media_group.append(
                InputMediaPhoto(
                    media=attr['photo_url'],
                    caption=caption,
                    parse_mode='Markdown'
                )
            )
        else:
            media_group.append(
                InputMediaPhoto(
                    media=attr['photo_url']
                )
            )
    
    try:
        # Удаляем предыдущее сообщение с кнопками
        await query.message.delete()
        
        # Отправляем альбом
        await query.message.reply_media_group(media=media_group)
        
    except Exception as e:
        logger.error(f"Error sending photo album: {e}")
        # Если не удалось отправить альбом, отправляем текстовую версию
        await query.message.reply_text(caption, parse_mode='Markdown', disable_web_page_preview=True)

async def show_restaurants(query):
    """Показать рестораны"""
    restaurants = [
        {
            'name': 'Этноресторан "Орда"',
            'cuisine': 'Бурятская, азиатская',
            'address': 'ул. Пушкина, 4а',
            'specialty': 'Традиционные бурятские блюда',
            'emoji': '🍖',
            '2gis_url': 'https://go.2gis.com/uC9y3'
        },
        {
            'name': 'Гурмэ-ресторан "Voyage"',
            'cuisine': 'Мировая',
            'address': 'ул. Ранжурова, 11',
            'specialty': 'Мировые блюда',
            'emoji': '🥘',
            '2gis_url': 'https://go.2gis.com/UvPWv'
        },
        {
            'name': 'Ресторан "Тэнгис"',
            'cuisine': 'Бурятская, паназиатская',
            'address': 'ул. Ербанова, 12',
            'specialty': 'Блюда из морепродуктов',
            'emoji': '🐟',
            '2gis_url': 'https://go.2gis.com/bHxCi'
        },
        {
            'name': 'Ресторан-бар "Гёдзе"',
            'cuisine': 'Паназиатская',
            'address': 'ул. Свободы, 15',
            'specialty': 'Караоке кабинки',
            'emoji': '🎤',
            '2gis_url': 'https://go.2gis.com/slkG4'
        },
        {
            'name': 'Ресторан-бар "Сахар"',
            'cuisine': 'Итальянская, средиземноморская',
            'address': 'ул. Сухэ-Батора, 7',
            'specialty': 'Блюда в аутентичной атмосфере',
            'emoji': '🍷',
            '2gis_url': 'https://go.2gis.com/d5T1Y'
        }
    ]
    
    response_text = "🍽️ *Лучшие рестораны Улан-Удэ:*\n\n"
    
    for i, rest in enumerate(restaurants, 1):
        response_text += f"{i}. {rest['emoji']} *{rest['name']}*\n"
        response_text += f"   📍 {rest['address']}\n"
        response_text += f"   🍳 {rest['cuisine']}\n"
        response_text += f"   👑 {rest['specialty']}\n"
        response_text += f"   🗺️ [Открыть в 2ГИС]({rest['2gis_url']})\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)

async def show_hotels(query):
    """Показать отели"""
    hotels = [
        {
            'name': 'Отель "Cosmos Selection Ulan-Ude"',
            'stars': '⭐⭐⭐⭐⭐',
            'address': 'ул. Борсоева, 19б',
            'features': 'SPA, парковка, завтрак включен',
            'price': 'от 6200 руб/ночь',
            'emoji': '🛌',
            '2gis_url': 'https://go.2gis.com/2moZG'
        },
        {
            'name': 'Гостиница "Сагаан Морин"',
            'stars': '⭐⭐⭐⭐',
            'address': 'ул. Гагарина, 25б',
            'features': 'Бизнес-центр, конференц-зал',
            'price': 'от 4950 руб/ночь',
            'emoji': '💼',
            '2gis_url': 'https://go.2gis.com/szcW2'
        },
        {
            'name': 'Отель "Байкал Плаза"',
            'stars': '⭐⭐⭐⭐',
            'address': 'ул. Ербанова, 12',
            'features': 'Центр города, вид на город',
            'price': 'от 3500 руб/ночь',
            'emoji': '🌆',
            '2gis_url': 'https://go.2gis.com/THSet'
        },
        {
            'name': 'Отель "City Park"',
            'stars': '⭐⭐⭐',
            'address': 'ул. Октябрьская, 2б',
            'features': 'SPA, парковка, конференц-залы',
            'price': 'от 3000 руб/ночь',
            'emoji': '🌃',
            '2gis_url': 'https://go.2gis.com/oJuBA'
        },
        {
            'name': 'Гостиница "Бурятия"',
            'stars': '⭐⭐⭐',
            'address': 'ул. Коммунистическая, 47а',
            'features': 'Сауна, ресторан, Wi-Fi',
            'price': 'от 2900 руб/ночь',
            'emoji': '🏨',
            '2gis_url': 'https://go.2gis.com/dEgnK'
        },
    ]
    
    response_text = "🏨 *Отели Улан-Удэ:*\n\n"
    
    for i, hotel in enumerate(hotels, 1):
        response_text += f"{i}. {hotel['emoji']} *{hotel['name']}*\n"
        response_text += f"   {hotel['stars']}\n"
        response_text += f"   📍 {hotel['address']}\n"
        response_text += f"   🎯 {hotel['features']}\n"
        response_text += f"   💰 {hotel['price']}\n"
        response_text += f"   🗺️ [Открыть в 2ГИС]({hotel['2gis_url']})\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)

async def show_shops(query):
    """Показать магазины"""
    shops = [
        {
            'name': 'ТЦ "Форум"',
            'type': 'Крупнейший торговый центр',
            'address': 'ул. Ленина, 39',
            'features': '200+ магазинов, фудкорт, кинотеатр',
            'emoji': '🏬',
            '2gis_url': 'https://go.2gis.com/B3laE'
        },
        {
            'name': 'ТРЦ "Пионер"',
            'type': 'Торгово-развлекательный центр',
            'address': 'ул. Корабельная, 41',
            'features': 'Магазины, кафе, развлечения',
            'emoji': '🎯',
            '2gis_url': 'https://go.2gis.com/q0dui'
        },
        {
            'name': 'Рынок "Центральный"',
            'type': 'Продуктовый рынок',
            'address': 'ул. Балтахинова, 9',
            'features': 'Свежие продукты, сувениры',
            'emoji': '🛒',
            '2gis_url': 'https://go.2gis.com/PmHDI'
        },
        {
            'name': 'ТД "Юбилейный"',
            'type': 'Торговый дом',
            'address': 'ул. Гагарина, 24',
            'features': 'Хоз. товары',
            'emoji': '🛠️',
            '2gis_url': 'https://go.2gis.com/2Ai6B'
        }
    ]
    
    response_text = "🛍️ *Магазины и ТЦ Улан-Удэ:*\n\n"
    
    for i, shop in enumerate(shops, 1):
        response_text += f"{i}. {shop['emoji']} *{shop['name']}*\n"
        response_text += f"   🏬 {shop['type']}\n"
        response_text += f"   📍 {shop['address']}\n"
        response_text += f"   🎯 {shop['features']}\n"
        response_text += f"   🗺️ [Открыть в 2ГИС]({shop['2gis_url']})\n\n"
    
    await query.edit_message_text(response_text, parse_mode='Markdown', disable_web_page_preview=True)

async def show_about(query):
    """Показать информацию о городе"""
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

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    text = update.message.text.lower()
    
    triggers = ['улан', 'улан-удэ', 'уланудэ', 'бурятия', 'погода', 'меню', 
                'байкал', 'сибирь', 'город', 'гид', 'путеводитель', 'что посмотреть',
                'время', 'дата', 'сколько время', 'который час']
    
    if text == "🚀 начать":
        await show_main_menu(update.message)
    elif any(trigger in text for trigger in triggers):
        await show_main_menu(update.message)
    else:
        response = """
🏙️ Привет! Я бот-гид по Улан-Удэ.

Я специализируюсь только на столице Бурятии. Нажми кнопку *"🚀 Начать"* или используй команду /start чтобы открыть меню и узнать всё об этом замечательном городе!

*Интересные факты об Улан-Удэ:*
• Город основан в 1666 году
• Здесь находится самая большая голова Ленина в мире
• Столица буддизма в России
• Более 260 солнечных дней в году
        """
        await update.message.reply_text(response, parse_mode='Markdown')

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /info"""
    help_text = """
🏙️ *Бот-гид по Улан-Удэ - Справка*

*Доступные команды:*
/start - Главное меню с кнопкой "Начать"
/info - Эта справка
/help - Помощь

*Я могу рассказать о:*
• 📅 Текущей дате и времени в Улан-Удэ
• 🌤️ Текущей погоде в Улан-Удэ
• 🏛️ Главных достопримечательностях
• 🍽️ Лучших ресторанах и кафе
• 🏨 Гостиницах и отелях
• 🛍️ Магазинах и ТЦ
• ℹ️ Интересных фактах о городе

*Нажми "🚀 Начать" чтобы открыть меню!*
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
🤖 *Доступные команды:*
/start - Начать работу с ботом
/info - Информация о боте
/help - Эта справка

Просто напишите название города или нажмите кнопку "🚀 Начать"!
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Произошла непредвиденная ошибка. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logger.error(f"Error in error handler: {e}")

def main():
    """Основная функция"""
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    print("🏙️ Бот-гид по Улан-Удэ запущен!")
    logger.info("Бот запущен успешно")
    application.run_polling()

if __name__ == '__main__':
    main()
