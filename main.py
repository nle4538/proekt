import os
import telebot
from telebot import types
from config import Token, ADMIN
from datetime import datetime
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler

API_TOKEN = os.environ.get(Token)
bot = telebot.TeleBot(Token)

# Подключение к базе данных
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    registration_date TEXT,
    referral_id INTEGER DEFAULT NULL,
    balance REAL DEFAULT 0
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS broadcasts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_text TEXT,
    photo_id TEXT DEFAULT NULL,
    send_time TEXT,
    status TEXT DEFAULT 'pending'
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    game TEXT,
    product TEXT,
    description TEXT,
    price REAL,
    game_id TEXT,
    payment_method TEXT,
    status TEXT,
    timestamp TEXT,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
)
''')
conn.commit()

# Временное хранилище заказов
temp_orders = {}

# Словарь с товарами Brawl Stars
brawl_stars_products = {
    'gemi30_pokupka': {'name': '30 💎', 'price': 230, 'desc': '30 гемов для Brawl Stars'},
    'gemi30_pokupka1': {'name': '80 💎', 'price': 560, 'desc': '80 гемов для Brawl Stars'},
    'gemi30_pokupka2': {'name': '170 💎', 'price': 1100, 'desc': '170 гемов для Brawl Stars'},
    'gemi30_pokupka3': {'name': '360 💎', 'price': 2150, 'desc': '360 гемов для Brawl Stars'},
    'gemi30_pokupka4': {'name': '950 💎', 'price': 4900, 'desc': '950 гемов для Brawl Stars'},
    'gemi30_pokupka5': {'name': '2000 💎', 'price': 9220, 'desc': '2000 гемов для Brawl Stars'},
    'gemi30_pokupka6': {'name': 'Brawl Pass', 'price': 230, 'desc': 'Бравл Пасс на текущий сезон'}
}

# Функция регистрации пользователя с учетом реферала
def register_user(user_id, username, first_name, referral_id=None):
    try:
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        existing_user = cursor.fetchone()
        if not existing_user:
            registration_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                'INSERT INTO users (user_id, username, first_name, registration_date, referral_id) VALUES (?, ?, ?, ?, ?)',
                (user_id, username, first_name, registration_date, referral_id))
            # Если есть реферер, увеличиваем его баланс на 5 единиц
            if referral_id:
                cursor.execute('UPDATE users SET balance = balance + 5 WHERE user_id = ?', (referral_id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Ошибка при регистрации пользователя: {e}")

# Команда /start с поддержкой реферальной ссылки
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    referral_id = None
    if len(args) > 1:
        try:
            referral_id = int(args[1])
        except ValueError:
            pass
    register_user(message.from_user.id, message.from_user.username, message.from_user.first_name, referral_id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🛍Магазин")
    btn3 = types.KeyboardButton("👤Профиль")
    btn4 = types.KeyboardButton("👨‍💻Поддержка")
    btn5 = types.KeyboardButton("📰Информация")
    markup.add(btn1, btn3, btn4, btn5)
    bot.send_message(message.chat.id,
                     text="Привет {0.first_name} ! 👋 Добро пожаловать в магазин по покупке доната! ⚡️ Для продолжения выбери кнопку на клавиатуре.".format(
                         message.from_user), reply_markup=markup)

# === Меню Brawl Stars ===
def show_brawlstars_menu(call):
    new_markup = types.InlineKeyboardMarkup()
    gemi30button = types.InlineKeyboardButton("💎 30 - 230 ₽", callback_data='gemi30_button')
    gemi80button = types.InlineKeyboardButton("💎 80 - 560 ₽", callback_data='gemi80_button')
    gemi170button = types.InlineKeyboardButton("💎 170 - 1100 ₽", callback_data='gemi170_button')
    gemi360button = types.InlineKeyboardButton("💎 360 - 2150 ₽", callback_data='gemi360_button')
    gemi950button = types.InlineKeyboardButton("💎 950 - 4900 ₽", callback_data='gemi950_button')
    gemi2000button = types.InlineKeyboardButton("💎 2000 - 9220 ₽", callback_data='gemi2000_button')
    brawlpassbutton = types.InlineKeyboardButton("Бравл Пасс⚡️", callback_data='brawlpass_button')
    back_button = types.InlineKeyboardButton("Назад", callback_data='back_to_main')
    new_markup.row(gemi30button, gemi80button)
    new_markup.row(gemi170button, gemi360button)
    new_markup.row(gemi950button, gemi2000button)
    new_markup.row(brawlpassbutton)
    new_markup.row(back_button)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Магазин / Brawl Stars:",
        reply_markup=new_markup
    )

def init_db():
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT,
        game TEXT NOT NULL,
        product TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        game_id TEXT NOT NULL,
        payment_method TEXT,
        payment_proof TEXT,
        status TEXT NOT NULL,
        admin_id INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        confirmed_at DATETIME,
        completed_at DATETIME
    )
    ''')
    conn.commit()

init_db()

# === Глобальные переменные ===
temp_orders = {}  # Временные заказы до подтверждения
temp_payments = {}  # Информация о платежах
admin_orders = {}  # Заказы, взятые в работу админами

# === Продукты Brawl Stars ===
brawl_stars_products = {
    'gemi30_pokupka': {'name': '30 💎', 'price': 230, 'desc': '30 гемов для Brawl Stars'},
    'gemi30_pokupka1': {'name': '80 💎', 'price': 560, 'desc': '80 гемов для Brawl Stars'},
    'gemi30_pokupka2': {'name': '170 💎', 'price': 1100, 'desc': '170 гемов для Brawl Stars'},
    'gemi30_pokupka3': {'name': '360 💎', 'price': 2150, 'desc': '360 гемов для Brawl Stars'},
    'gemi950_pokupka4': {'name': '950 💎', 'price': 4900, 'desc': '950 гемов для Brawl Stars'},
    'gemi2000_pokupka5': {'name': '2000 💎', 'price': 9220, 'desc': '2000 гемов для Brawl Stars'},
    'gemi30_pokupka6': {'name': 'Brawl Pass', 'price': 230, 'desc': 'Бравл Пасс на текущий сезон'}
}

# === Обработка callback'ов ===
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == 'brawlstart_button':
        show_brawlstars_menu(call)
    elif call.data == 'pubgmobile_button':
        bot.send_message(call.message.chat.id, "🛠 Эта категория пока недоступна.")
    elif call.data == 'back_to_main':
        show_main_menu(call)
    elif call.data in ['gemi30_button', 'gemi80_button', 'gemi170_button',
                       'gemi360_button', 'gemi950_button', 'gemi2000_button', 'brawlpass_button']:
        show_product_description(call)
    elif call.data in brawl_stars_products.keys():
        handle_purchase(call)
    elif call.data.startswith('confirm_'):
        confirm_order(call)
    elif call.data.startswith('change_'):
        change_game_id(call)
    elif call.data.startswith('cancel_'):
        cancel_order(call)
    elif call.data.startswith('pay_'):
        process_payment(call)
    elif call.data.startswith('admin_confirm_'):
        handle_admin_confirm(call)
    elif call.data.startswith('admin_reject_'):
        handle_admin_reject(call)
    elif call.data.startswith('admin_complete_'):
        handle_admin_complete(call)
    elif call.data == 'history_button':
        callback_show_purchase_history(call)
    elif call.data == 'balans_button':
        show_balance_topup(call)
    elif call.data == 'ref_button':
        referral_system(call)
    elif call.data == 'main_menu':
        main_menu_callback(call)
    elif call.data == 'otzivi':
        bot.answer_callback_query(call.id, "У нас пока нет отзывов.", show_alert=True)

# === Меню ===
def show_main_menu(call):
    markup = types.InlineKeyboardMarkup()
    brawlstarts = types.InlineKeyboardButton("Brawl Stars", callback_data='brawlstart_button')
    pubg = types.InlineKeyboardButton("Pubg Mobile", callback_data='pubgmobile_button')
    markup.add(brawlstarts, pubg)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Выберите категорию или товар:", reply_markup=markup)

def show_brawlstars_menu(call):
    new_markup = types.InlineKeyboardMarkup()
    gemi30button = types.InlineKeyboardButton("💎 30 - 230 ₽", callback_data='gemi30_button')
    gemi80button = types.InlineKeyboardButton("💎 80 - 560 ₽", callback_data='gemi80_button')
    gemi170button = types.InlineKeyboardButton("💎 170 - 1100 ₽", callback_data='gemi170_button')
    gemi360button = types.InlineKeyboardButton("💎 360 - 2150 ₽", callback_data='gemi360_button')
    gemi950button = types.InlineKeyboardButton("💎 950 - 4900 ₽", callback_data='gemi950_button')
    gemi2000button = types.InlineKeyboardButton("💎 2000 - 9220 ₽", callback_data='gemi2000_button')
    brawlpassbutton = types.InlineKeyboardButton("Бравл Пасс⚡️", callback_data='brawlpass_button')
    back_button = types.InlineKeyboardButton("Назад", callback_data='back_to_main')
    new_markup.row(gemi30button, gemi80button)
    new_markup.row(gemi170button, gemi360button)
    new_markup.row(gemi950button, gemi2000button)
    new_markup.row(brawlpassbutton)
    new_markup.row(back_button)
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text="Магазин / Brawl Stars:", reply_markup=new_markup)

def show_product_description(call):
    product_map = {
        'gemi30_button': {'name': '30 💎', 'price': 230, 'desc': '30 гемов для Brawl Stars', 'callback': 'gemi30_pokupka'},
        'gemi80_button': {'name': '80 💎', 'price': 560, 'desc': '80 гемов для Brawl Stars', 'callback': 'gemi30_pokupka1'},
        'gemi170_button': {'name': '170 💎', 'price': 1100, 'desc': '170 гемов для Brawl Stars', 'callback': 'gemi30_pokupka2'},
        'gemi360_button': {'name': '360 💎', 'price': 2150, 'desc': '360 гемов для Brawl Stars', 'callback': 'gemi30_pokupka3'},
        'gemi950_button': {'name': '950 💎', 'price': 4900, 'desc': '950 гемов для Brawl Stars', 'callback': 'gemi950_pokupka4'},
        'gemi2000_button': {'name': '2000 💎', 'price': 9220, 'desc': '2000 гемов для Brawl Stars', 'callback': 'gemi2000_pokupka5'},
        'brawlpass_button': {'name': 'Brawl Pass', 'price': 230, 'desc': 'Бравл Пасс на текущий сезон', 'callback': 'gemi30_pokupka6'}
    }
    product = product_map[call.data]
    markup = types.InlineKeyboardMarkup()
    buy_btn = types.InlineKeyboardButton("🛒 Купить", callback_data=product['callback'])
    back_btn = types.InlineKeyboardButton("⬅️ Назад", callback_data='brawlstart_button')
    markup.add(buy_btn, back_btn)
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"🛍 Товар: {product['name']}\n"
             f"💰 Цена: {product['price']} RUB\n"
             f"📝 Описание: {product['desc']}\n"
             f"📖 Зачисление происходит через вход в аккаунт, мы гарантируем полную сохранность ваших данных!",
        reply_markup=markup
    )

# --- Блок профиля с исправленной логикой ---
@bot.message_handler(func=lambda message: message.text == "👤Профиль")
def profile(message):
    cursor.execute('SELECT balance, registration_date FROM users WHERE user_id = ?', (message.from_user.id,))
    result = cursor.fetchone()
    if result:
        balance, registration_date = result
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("Реф система", callback_data='ref_button')
        )
        markup.add(
            types.InlineKeyboardButton("История покупок", callback_data='history_button'),
        )
        bot.send_message(
            message.chat.id,
            f"📋Информация о {message.from_user.first_name}\n"
            f"ID: {message.from_user.id}\n"
            f"Дата регистрации: {registration_date}\n",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "❌ Произошла ошибка при получении данных.")

@bot.callback_query_handler(func=lambda call: call.data == 'history_button')
def callback_show_purchase_history(call):
    user_id = call.from_user.id
    cursor.execute('SELECT id, product, price, status, timestamp FROM orders WHERE user_id = ? ORDER BY timestamp DESC', (user_id,))
    orders = cursor.fetchall()
    if not orders:
        bot.answer_callback_query(call.id, "У вас пока нет покупок.", show_alert=True)
        return
    text = "📦 Ваша история покупок:\n"
    for order in orders:
        order_id, product, price, status, timestamp = order
        text += (f"Заказ #{order_id}\n"
                 f"Товар: {product}\n"
                 f"Цена: {price} ₽\n"
                 f"Статус: {status}\n"
                 f"Дата: {timestamp}\n\n")
    bot.send_message(call.message.chat.id, text)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == 'balans_button')
def show_balance_topup(call):
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        "Для пополнения баланса свяжитесь с поддержкой: @qwerty258b\n"
        "Укажите сумму пополнения и предпочитаемый способ оплаты."
    )

@bot.callback_query_handler(func=lambda call: call.data == 'ref_button')
def referral_system(call):
    bot.answer_callback_query(call.id)
    user_id = call.from_user.id
    cursor.execute('SELECT COUNT(*) FROM users WHERE referral_id = ?', (user_id,))
    referrals_count = cursor.fetchone()[0]
    referral_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(
        call.message.chat.id,
        f"👥 Реферальная система\n"
        f"Ваша реферальная ссылка: {referral_link}\n"
        f"Количество приглашенных: {referrals_count}\n"
        f"Вы получаете 15% от каждой покупки ваших рефералов!"
    )

@bot.callback_query_handler(func=lambda call: call.data == 'main_menu')
def main_menu_callback(call):
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🛍Магазин")
    btn3 = types.KeyboardButton("👤Профиль")
    btn4 = types.KeyboardButton("👨‍💻Поддержка")
    btn5 = types.KeyboardButton("📰Информация")
    markup.add(btn1, btn3, btn4, btn5)
    bot.send_message(call.message.chat.id,
                     text="Вы вернулись в главное меню.", reply_markup=markup)

# Админ-панель
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.chat.id == ADMIN:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Статистика пользователей")
        btn2 = types.KeyboardButton("Создать рассылку")
        btn3 = types.KeyboardButton("Отменить рассылку")
        btn4 = types.KeyboardButton("Вернуться в главное меню")
        btn5 = types.KeyboardButton("История заказов")
        btn6 = types.KeyboardButton("Статистика продаж")
        markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
        bot.send_message(
            message.chat.id,
            text="✅ Вы вошли в панель управления администратора",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, text="❌ Вам запрещено использовать эту команду.")

# Статистика пользователей
@bot.message_handler(func=lambda message: message.text == "Статистика пользователей")
def show_statistics(message):
    if message.chat.id != ADMIN:
        bot.send_message(message.chat.id, text="❌ Вам запрещено использовать эту команду.")
        return
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]
    cursor.execute('SELECT user_id, username, first_name, registration_date FROM users')
    users = cursor.fetchall()
    conn.close()
    stats_text = f"📊 Статистика пользователей:\nОбщее количество пользователей: {total_users}\n"
    for user in users:
        user_id, username, first_name, registration_date = user
        stats_text += f"ID: {user_id}, Имя: {first_name}, Username: @{username}, Зарегистрирован: {registration_date}\n"
    bot.send_message(message.chat.id, text=stats_text)

# Вернуться в главное меню
@bot.message_handler(func=lambda message: message.text == "Вернуться в главное меню")
def go_to_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🛍Магазин")
    btn3 = types.KeyboardButton("👤Профиль")
    btn4 = types.KeyboardButton("👨‍💻Поддержка")
    btn5 = types.KeyboardButton("📰Информация")
    markup.add(btn1, btn3, btn4, btn5)
    bot.send_message(message.chat.id,
                     text="Привет {0.first_name} ! 👋 Добро пожаловать в магазин по покупке доната! ⚡️ Для продолжения выбери кнопку на клавиатуре.".format(
                         message.from_user), reply_markup=markup)

# Создать рассылку
@bot.message_handler(func=lambda message: message.text == "Создать рассылку")
def handle_create_broadcast(message):
    if message.chat.id == ADMIN:
        create_broadcast(message)
    else:
        bot.send_message(message.chat.id, text="❌ Вам запрещено использовать эту команду.")

# Отменить рассылку
@bot.message_handler(func=lambda message: message.text == "Отменить рассылку")
def handle_cancel_broadcast(message):
    if message.chat.id == ADMIN:
        cancel_broadcast(message)
    else:
        bot.send_message(message.chat.id, text="❌ Вам запрещено использовать эту команду.")

# Последние заказы
@bot.message_handler(func=lambda message: message.text == "История заказов")
def admin_orders_list(message):
    if message.chat.id != ADMIN:
        bot.send_message(message.chat.id, "❌ Вам запрещено использовать эту команду.")
        return
    admin_show_orders(message)

@bot.message_handler(func=lambda message: message.text == "Статистика продаж")
def admin_show_stats(message):
    if message.chat.id != ADMIN:
        bot.send_message(message.chat.id, "❌ Вам запрещено использовать эту команду.")
        return
    admin_sales_statistics(message)

# === Магазин ===
@bot.message_handler(func=lambda message: message.text == "🛍Магазин")
def open_shop(message):
    markup = types.InlineKeyboardMarkup()
    brawlstarts = types.InlineKeyboardButton("Brawl Stars", callback_data='brawlstart_button')
    pubg = types.InlineKeyboardButton("Pubg Mobile", callback_data='pubgmobile_button')
    markup.add(brawlstarts, pubg)
    bot.send_message(message.chat.id, "Выберите категорию или товар:", reply_markup=markup)

# === Поддержка ===
@bot.message_handler(func=lambda message: message.text == "👨‍💻Поддержка")
def support(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    bot.send_message(message.chat.id, text="По всем вопросам писать - @qwerty258b")

# === Информация ===
@bot.message_handler(func=lambda message: message.text == "📰Информация")
def info(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup_info = types.InlineKeyboardMarkup()
    otzivibutton = types.InlineKeyboardButton("Отзывы", callback_data='otzivi')
    markup_info.add(otzivibutton)
    bot.send_message(message.chat.id,
                     text="📰 Наш канал - https://\n⚠️ Публикуем исключительно важные новости",
                     reply_markup=markup_info)


# === Обработка выбора "Создать рассылку" из админ-панели ===
def create_broadcast(message):
    bot.send_message(ADMIN, "Отправьте текст рассылки (или напишите 'отмена' для выхода):")
    bot.register_next_step_handler(message, process_broadcast_text)

def process_broadcast_text(message):
    if message.text.lower() in ['отмена', '/cancel']:
        cancel_broadcast_creation(message)
        return
    broadcast_text = message.text
    bot.send_message(ADMIN, "Хотите добавить фото? Отправьте фото или напишите 'нет' (или 'отмена' для выхода):")
    bot.register_next_step_handler(message, lambda msg: process_broadcast_photo(msg, broadcast_text))

def process_broadcast_photo(message, broadcast_text):
    if message.text and message.text.lower() in ['отмена', '/cancel']:
        cancel_broadcast_creation(message)
        return
    photo_id = None
    if message.content_type == 'photo':
        photo_id = message.photo[-1].file_id
    elif message.text.lower() == 'нет':
        photo_id = None
    else:
        bot.send_message(ADMIN, "Некорректный формат. Рассылка будет без фото.")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("Отправить сейчас"), types.KeyboardButton("Выбрать указанное время"), types.KeyboardButton("Отмена"))
    bot.send_message(ADMIN, "Выберите способ отправки (или нажмите 'Отмена'):", reply_markup=markup)
    bot.register_next_step_handler(message, lambda msg: choose_broadcast_method(msg, broadcast_text, photo_id))

def choose_broadcast_method(message, broadcast_text, photo_id):
    if message.text == "Отмена" or message.text == "/cancel":
        admin(message)
    elif message.text == "Отправить сейчас":
        send_immediately(broadcast_text, photo_id)
    elif message.text == "Выбрать указанное время":
        bot.send_message(ADMIN, "Укажите дату и время отправки в формате YYYY-MM-DD HH:MM:")
        bot.register_next_step_handler(message, lambda msg: save_scheduled_broadcast(msg, broadcast_text, photo_id))
    else:
        bot.send_message(ADMIN, "Неверный выбор. Попробуйте снова.")

def save_scheduled_broadcast(message, broadcast_text, photo_id):
    if message.text.lower() in ['отмена', '/cancel']:
        cancel_broadcast_creation(message)
        return
    try:
        send_time = datetime.strptime(message.text, '%Y-%m-%d %H:%M')
        current_time = datetime.now()
        if send_time < current_time:
            bot.send_message(ADMIN, "Время должно быть в будущем. Попробуйте снова.")
            return
        cursor.execute('INSERT INTO broadcasts (message_text, photo_id, send_time) VALUES (?, ?, ?)',
                       (broadcast_text, photo_id, send_time.strftime('%Y-%m-%d %H:%M')))
        conn.commit()
        bot.send_message(ADMIN, "Рассылка успешно запланирована!")
    except ValueError:
        bot.send_message(ADMIN, "Неверный формат даты и времени. Попробуйте снова.")

def send_immediately(broadcast_text, photo_id):
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    for user in users:
        user_id = user[0]
        try:
            if photo_id:
                bot.send_photo(user_id, photo_id, caption=broadcast_text)
            else:
                bot.send_message(user_id, broadcast_text)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    bot.send_message(ADMIN, "Рассылка успешно отправлена!")

def cancel_broadcast_creation(message):
    bot.send_message(ADMIN, "Создание рассылки отменено.")
    return

@bot.message_handler(commands=['cancel_broadcast'])
def cancel_broadcast(message):
    if message.chat.id != ADMIN:
        bot.send_message(message.chat.id, "❌ Только администратор может использовать эту команду.")
        return
    cursor.execute('SELECT id, message_text, send_time FROM broadcasts WHERE status = ?', ('pending',))
    broadcasts = cursor.fetchall()
    if not broadcasts:
        bot.send_message(ADMIN, "Список запланированных рассылок пуст.")
        return
    broadcast_list = "Запланированные рассылки:\n"
    for broadcast in broadcasts:
        broadcast_id, message_text, send_time = broadcast
        broadcast_list += f"ID: {broadcast_id}, Время: {send_time}, Сообщение: {message_text[:50]}...\n"
    bot.send_message(ADMIN, broadcast_list)
    bot.send_message(ADMIN, "Введите ID рассылки, которую хотите отменить:")

def process_cancel_broadcast(message):
    try:
        broadcast_id = int(message.text)
        cursor.execute('SELECT * FROM broadcasts WHERE id = ? AND status = ?', (broadcast_id, 'pending'))
        broadcast = cursor.fetchone()
        if not broadcast:
            bot.send_message(ADMIN, "Рассылка с указанным ID не найдена или уже отправлена.")
            return
        cursor.execute('UPDATE broadcasts SET status = ? WHERE id = ?', ('cancelled', broadcast_id))
        conn.commit()
        bot.send_message(ADMIN, f"Рассылка с ID {broadcast_id} успешно отменена.")
    except ValueError:
        bot.send_message(ADMIN, "Неверный формат ID. Попробуйте снова.")

# === Обработка покупки ===
def handle_purchase(call):
    product = brawl_stars_products[call.data]
    msg = bot.send_message(
        call.message.chat.id,
        f"🛒 Вы выбрали: {product['name']}\n"
        f"💰 Цена: {product['price']} RUB\n"
        f"📝 Описание: {product['desc']}\n"
        "🔢 Введите ваш игровой ID в Brawl Stars (только цифры):"
    )
    bot.register_next_step_handler(msg, process_game_id, product)

# === Обработка игрового ID ===
def process_game_id(message, product):
    try:
        game_id = message.text.strip()
        if not game_id.isdigit():
            msg = bot.send_message(
                message.chat.id,
                "❌ Ошибка: Игровой ID должен содержать только цифры.\nПожалуйста, введите корректный ID:"
            )
            bot.register_next_step_handler(msg, process_game_id, product)
            return
        temp_order = {
            'user_id': message.from_user.id,
            'username': message.from_user.username,
            'game': 'Brawl Stars',
            'product': product['name'],
            'description': product['desc'],
            'price': product['price'],
            'game_id': game_id
        }
        temp_orders[message.from_user.id] = temp_order
        markup = types.InlineKeyboardMarkup(row_width=2)
        confirm_btn = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{message.from_user.id}")
        change_btn = types.InlineKeyboardButton("✏️ Изменить ID", callback_data=f"change_{message.from_user.id}")
        cancel_btn = types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{message.from_user.id}")
        markup.add(confirm_btn, change_btn, cancel_btn)
        bot.send_message(
            message.chat.id,
            f"🔍 Проверьте данные заказа:\n"
            f"🎮 Игра: Brawl Stars\n"
            f"🛍 Товар: {product['name']}\n"
            f"📝 Описание: {product['desc']}\n"
            f"💰 Цена: {product['price']} RUB\n"
            f"🆔 Ваш игровой ID: {game_id}\n"
            "Все верно?",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# === Изменение игрового ID ===
def change_game_id(call):
    try:
        user_id = int(call.data.split('_')[1])
        if user_id not in temp_orders:
            bot.answer_callback_query(call.id, "❌ Ошибка: заказ не найден", show_alert=True)
            return
        msg = bot.send_message(
            call.message.chat.id,
            "🔢 Введите новый игровой ID в Brawl Stars (только цифры):"
        )
        bot.register_next_step_handler(msg, update_game_id, user_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

def update_game_id(message, user_id):
    try:
        game_id = message.text.strip()
        if not game_id.isdigit():
            msg = bot.send_message(
                message.chat.id,
                "❌ Ошибка: Игровой ID должен содержать только цифры.\nВведите корректный ID:"
            )
            bot.register_next_step_handler(msg, update_game_id, user_id)
            return
        temp_orders[user_id]['game_id'] = game_id
        markup = types.InlineKeyboardMarkup(row_width=2)
        confirm_btn = types.InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{user_id}")
        change_btn = types.InlineKeyboardButton("✏️ Изменить ID", callback_data=f"change_{user_id}")
        cancel_btn = types.InlineKeyboardButton("❌ Отменить", callback_data=f"cancel_{user_id}")
        markup.add(confirm_btn, change_btn, cancel_btn)
        bot.send_message(
            message.chat.id,
            f"🔍 Проверьте данные заказа:\n"
            f"🎮 Игра: Brawl Stars\n"
            f"🛍 Товар: {temp_orders[user_id]['product']}\n"
            f"📝 Описание: {temp_orders[user_id]['description']}\n"
            f"💰 Цена: {temp_orders[user_id]['price']} RUB\n"
            f"🆔 Ваш игровой ID: {game_id}\n"
            "Все верно?",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")

# === Подтверждение заказа ===
def confirm_order(call):
    try:
        user_id = int(call.data.split('_')[1])
        order = temp_orders.get(user_id)
        if not order:
            bot.answer_callback_query(call.id, "❌ Ошибка: заказ не найден", show_alert=True)
            return
        cursor.execute('''
            INSERT INTO orders (user_id, username, game, product, description, price, game_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order['user_id'], order['username'], order['game'],
            order['product'], order['description'], order['price'],
            order['game_id'], 'pending_payment'
        ))
        conn.commit()
        order_db_id = cursor.lastrowid
        markup = types.InlineKeyboardMarkup(row_width=1)
        card_btn = types.InlineKeyboardButton("💳 Банковская карта", callback_data=f"pay_card_{order_db_id}")
        crypto_btn = types.InlineKeyboardButton("💰 Криптовалюта", callback_data=f"pay_crypto_{order_db_id}")
        markup.add(card_btn, crypto_btn)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ Заказ подтвержден!\n"
                 f"Товар: {order['product']}\n"
                 f"Описание: {order['description']}\n"
                 f"Сумма: {order['price']} RUB\n"
                 f"Выберите способ оплаты:",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при подтверждении заказа: {str(e)}")

# === Обработка оплаты ===
def process_payment(call):
    try:
        payment_method = call.data.split('_')[1]
        order_db_id = call.data.split('_')[2]
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_db_id,))
        order = cursor.fetchone()
        if not order:
            bot.answer_callback_query(call.id, "❌ Ошибка: заказ не найден", show_alert=True)
            return
        cursor.execute('''
            UPDATE orders
            SET payment_method = ?, status = 'awaiting_payment'
            WHERE id = ?
        ''', (payment_method, order_db_id))
        conn.commit()
        payment_details = {
            'card': "💳 Карта Сбербанка: 2200 1234 5678 9010\n👤 Получатель: Иван Иванов\n💬 Назначение платежа: " + str(order_db_id),
            'crypto': "💰 BTC: 1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa\n💰 ETH: 0x71C7656EC7ab88b098defB751B7401B5f6d8976F\n💬 ID платежа: " + str(order_db_id)
        }
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"💸 Оплата через {payment_method.upper()}\n"
                 f"Реквизиты для оплаты:\n{payment_details[payment_method]}\n"
                 f"🛍 Товар: {order[4]}\n"
                 f"💰 Сумма: {order[6]} RUB\n"
                 f"📌 После оплаты отправьте скриншот чека/перевода в этот чат\n"
                 f"⌛ Обычно доставка занимает 5-15 минут",
            reply_markup=None
        )
        temp_payments[call.from_user.id] = {
            'order_id': order_db_id,
            'payment_method': payment_method
        }
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка при обработке платежа: {str(e)}")

# === Обработка доказательства оплаты ===
@bot.message_handler(content_types=['photo', 'document'])
def handle_payment_proof(message):
    try:
        if message.content_type not in ['photo', 'document']:
            bot.reply_to(message, "❌ Я принимаю только изображения или файлы с квитанциями.")
            return
        user_id = message.from_user.id
        payment_info = temp_payments.get(user_id)
        if not payment_info:
            bot.reply_to(message, "❌ Не найдено активного платежа. Пожалуйста, начните процесс оплаты заново.")
            return
        if message.content_type == 'photo':
            file_id = message.photo[-1].file_id
        elif message.document.mime_type.startswith('image/'):
            file_id = message.document.file_id
        else:
            bot.reply_to(message, "❌ Мы принимаем только изображения (скриншоты/квитанции).")
            return
        order_id = payment_info['order_id']
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        if not order:
            bot.reply_to(message, "❌ Ошибка: заказ не найден. Обратитесь в поддержку.")
            return
        cursor.execute('''
            UPDATE orders
            SET payment_proof = ?, status = 'payment_review'
            WHERE id = ?
        ''', (file_id, order_id))
        conn.commit()
        order_details = (
            f"🆕 Новый платёж на проверку!\n"
            f"🆔 Заказ: #{order[0]}\n"
            f"👤 Пользователь: @{message.from_user.username} (ID: {message.from_user.id})\n"
            f"📱 Игровой ID: {order[7]}\n"
            f"🎮 Игра: {order[3]}\n"
            f"🛍 Товар: {order[4]}\n"
            f"📝 Описание: {order[5]}\n"
            f"💰 Сумма: {order[6]} RUB\n"
            f"💳 Способ оплаты: {order[8]}"
        )
        if message.content_type == 'photo':
            bot.send_photo(ADMIN, file_id, caption=order_details)
        else:
            bot.send_document(ADMIN, file_id, caption=order_details)
        markup = types.InlineKeyboardMarkup()
        confirm_btn = types.InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"admin_confirm_{order_id}")
        reject_btn = types.InlineKeyboardButton("❌ Отклонить", callback_data=f"admin_reject_{order_id}")
        markup.add(confirm_btn, reject_btn)
        bot.send_message(ADMIN, "Действия с заказом:", reply_markup=markup)
        bot.reply_to(message, "✅ Скриншот оплаты отправлен на проверку.")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}. Попробуйте ещё раз.")

# === Обработка действий администратора ===
def handle_admin_confirm(call):
    try:
        order_id = call.data.split('_')[2]
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        if not order:
            bot.answer_callback_query(call.id, "❌ Заказ не найден", show_alert=True)
            return
        cursor.execute('''
            UPDATE orders 
            SET status = 'in_progress', admin_id = ?, confirmed_at = datetime('now')
            WHERE id = ?
        ''', (call.from_user.id, order_id))
        conn.commit()
        admin_orders[order_id] = {'admin_id': call.from_user.id, 'user_id': order[1]}
        bot.send_message(order[1], f"✅ Ваш платеж по заказу #{order_id} подтвержден.\nЗаказ на обработке.")
        markup = types.InlineKeyboardMarkup()
        complete_btn = types.InlineKeyboardButton("✅ Заказ выполнен", callback_data=f"admin_complete_{order_id}")
        markup.add(complete_btn)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"🛠 Заказ #{order_id} взят в работу:\n"
                 f"🛍 Товар: {order[4]}\n"
                 f"💰 Сумма: {order[6]} RUB\n"
                 f"После выполнения нажмите кнопку ниже.",
            reply_markup=markup
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

def handle_admin_reject(call):
    try:
        order_id = call.data.split('_')[2]
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        if not order:
            bot.answer_callback_query(call.id, "❌ Заказ не найден", show_alert=True)
            return
        cursor.execute('''
            UPDATE orders 
            SET status = 'rejected', completed_at = datetime('now') 
            WHERE id = ?
        ''', (order_id,))
        conn.commit()
        bot.send_message(order[1], f"🚫 Ваш заказ #{order_id} был отклонён.\nПлатёж не прошёл или произошла ошибка.")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"❌ Заказ #{order_id} был отклонён.\nПользователь уведомлён."
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

def handle_admin_complete(call):
    try:
        order_id = call.data.split('_')[2]
        if order_id not in admin_orders or admin_orders[order_id]['admin_id'] != call.from_user.id:
            bot.answer_callback_query(call.id, "❌ Этот заказ не назначен вам.", show_alert=True)
            return
        cursor.execute('''
            UPDATE orders 
            SET status = 'completed', completed_at = datetime('now') 
            WHERE id = ?
        ''', (order_id,))
        conn.commit()
        del admin_orders[order_id]
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        bot.send_message(order[1], f"🎉 Ваш заказ #{order_id} выполнен!\nМожете проверять!")
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"✅ Заказ #{order_id} успешно выполнен!\nПользователь уведомлён."
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

# === Отмена заказа ===
def cancel_order(call):
    try:
        user_id = int(call.data.split('_')[1])
        if user_id in temp_orders:
            del temp_orders[user_id]
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ Заказ отменён. Вы можете начать заново."
        )
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Ошибка: {str(e)}")

# === Статистика продаж ===
def admin_sales_statistics(message):
    if message.chat.id != ADMIN:
        bot.send_message(message.chat.id, "❌ Только администратор может использовать эту команду.")
        return
    cursor.execute('SELECT COUNT(*), SUM(price) FROM orders')
    total_orders, total_revenue = cursor.fetchone()
    cursor.execute('SELECT COUNT(*), SUM(price) FROM orders WHERE status = "completed"')
    completed_orders, completed_revenue = cursor.fetchone()
    avg_check = total_revenue / total_orders if total_orders else 0
    text = (
        f"📈 Статистика продаж:\n"
        f"Всего заказов: {total_orders}\n"
        f"Общий доход: {total_revenue or 0:.2f} ₽\n"
        f"Выполнено заказов: {completed_orders}\n"
        f"Доход от выполненных: {completed_revenue or 0:.2f} ₽\n"
        f"Средний чек: {avg_check:.2f} ₽"
    )
    bot.send_message(message.chat.id, text)

# === История заказов ===
def admin_show_orders(message):
    if message.chat.id != ADMIN:
        bot.send_message(message.chat.id, "❌ Только администратор может использовать эту команду.")
        return
    cursor.execute('SELECT id, user_id, username, product, price, status, timestamp FROM orders ORDER BY timestamp DESC LIMIT 20')
    orders = cursor.fetchall()
    if not orders:
        bot.send_message(message.chat.id, "Заказов нет.")
        return
    text = "🛒 Последние заказы:\n"
    for order in orders:
        order_id, user_id, username, product, price, status, timestamp = order
        text += (
            f"#{order_id} | Пользователь: @{username} ({user_id})\n"
            f"Товар: {product}\n"
            f"Цена: {price} ₽\n"
            f"Статус: {status}\n"
            f"Дата: {timestamp}\n"
        )
    bot.send_message(message.chat.id, text)

# === Планировщик рассылок ===
scheduler = BackgroundScheduler()
def send_scheduled_broadcasts():
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    cursor.execute('SELECT id, message_text, photo_id FROM broadcasts WHERE send_time <= ? AND status = ?', (current_time, 'pending'))
    broadcasts = cursor.fetchall()
    for broadcast in broadcasts:
        broadcast_id, message_text, photo_id = broadcast
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        for user in users:
            user_id = user[0]
            try:
                if photo_id:
                    bot.send_photo(user_id, photo_id, caption=message_text)
                else:
                    bot.send_message(user_id, message_text)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
        cursor.execute('UPDATE broadcasts SET status = ? WHERE id = ?', ('sent', broadcast_id))
        conn.commit()
scheduler.add_job(send_scheduled_broadcasts, 'interval', minutes=1)
scheduler.start()

# === Запуск бота ===
try:
    bot.polling(none_stop=True)
except Exception as e:
    print(f"Произошла ошибка: {e}")