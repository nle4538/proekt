для работы установите завистимости;
pip install -r requirements.txt


В файле config.py задайте:
Token = 'ВАШ_ТОКЕН_ОТ_BOTFATHER'
ADMIN = 123456789  # Ваш Telegram ID

🛠 Запуск:
python main.py

Бот начнёт принимать команды:
/start — регистрация и главное меню
/admin — доступно только администратору

🗄 База данных:
Создаются автоматически при запуске:
users — пользователи
orders — заказы
broadcasts — рассылки
