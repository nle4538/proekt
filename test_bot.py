import sqlite3
import os
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from main import bot, register_user, start, conn, cursor


# Фикстура для очистки БД перед каждым тестом
@pytest.fixture(autouse=True)
def clear_db():
    cursor.execute("DELETE FROM users")
    conn.commit()

def test_register_user():
    user_id = 123456
    username = "testuser"
    first_name = "Test"

    register_user(user_id, username, first_name)

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()

    assert result is not None
    assert result[1] == user_id
    assert result[2] == username
    assert result[3] == first_name
    assert datetime.strptime(result[4], "%Y-%m-%d %H:%M:%S")  # Проверка формата даты


# Тест: реферал получает +5 баланса при регистрации нового пользователя
def test_referral_bonus():
    # Сначала регистрируем реферала
    referrer_id = 789012
    register_user(referrer_id, "referrer", "Ref")

    # Регистрируем пользователя по реферальной ссылке
    user_id = 345678
    register_user(user_id, "newuser", "New", referral_id=referrer_id)

    # Проверяем баланс реферала
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (referrer_id,))
    balance = cursor.fetchone()[0]

    assert balance == 5


# Тест: команда /start регистрирует пользователя и отправляет сообщение
@patch('your_bot_file.bot.send_message')
def test_start_command(mock_send_message):
    message = MagicMock()
    message.from_user.id = 987654
    message.from_user.username = "starter"
    message.from_user.first_name = "Start"
    message.text = "/start"
    message.chat.id = 111222

    start(message)

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (message.from_user.id,))
    result = cursor.fetchone()

    assert result is not None
    assert result[1] == message.from_user.id
    mock_send_message.assert_called_once()