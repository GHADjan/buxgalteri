import telebot
from telebot import types
import sqlite3
import csv
import os


# Кнопки
categories = ['Продукты', 'Транспорт', 'Жилье', 'Развлечения']

bot = telebot.TeleBot('6067691510:AAGOdPyuNZ0RKYNLz6BPvXENkAqmV05y5A0')

# тоже кнопки потом обьединяем всё в одну функцию
expenses = ['Статистика', 'Очистить статистику', 'Экспорт в CSV']

# создание базы данных если он отсутсвует
def create_table(chat_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS expenses_{}
                 (id INTEGER,
                 category TEXT,
                 amount REAL,
                 PRIMARY KEY (id))'''.format(chat_id))
    conn.commit()
    conn.close()
# Функция для создания клавиатуры с категориями расходов и доп. кнопок
def get_categories_markup():
    markup = types.ReplyKeyboardMarkup(row_width=2)
    for category in categories:
        markup.add(category)
    markup.add('Статистика', 'Очистить статистику', 'Экспорт в CSV')
    return markup


# функция для экпорста с базы данных в CSV формат
def export_to_csv(chat_id):
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()
    with open('expenses.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Category', 'Amount'])
        for row in c.execute('SELECT category, amount FROM expenses_{}'.format(chat_id)).fetchall():
            writer.writerow(row)
    conn.close()

# create_table(message.chat.id)

# функция которая отвечает на любое сообщение и обрабатывает сообщение пользователя
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == '/start':
        create_table(message.chat.id)  # передаем chat_id в функцию create_table()
        bot.reply_to(message, "Привет! Я бот для учета расходов.")
        bot.reply_to(message, "Напиши на что ты потратил деньги или выбери категорию из списка.", reply_markup=get_categories_markup())
    elif message.text == 'Статистика':
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        total_expenses = c.execute('SELECT SUM(amount) FROM expenses_{} '.format(message.chat.id)).fetchone()[0]
        stats = 'Всего потрачено: {} сум\n---------------\n'.format(total_expenses)
        for row in c.execute('SELECT category, amount FROM expenses_{}'.format(message.chat.id)):  # используем message.chat.id
            stats += '{}: {}\n'.format(row[0], row[1])
        conn.close()
        bot.reply_to(message, stats)
    elif message.text == 'Очистить статистику':
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('DELETE FROM expenses_{}'.format(message.chat.id))
        conn.commit()
        conn.close()
        bot.reply_to(message, "Статистика очищена.")
    elif message.text == 'Экспорт в CSV':
        export_to_csv(message.chat.id)
        with open('expenses.csv', 'rb') as file:
            bot.send_document(message.chat.id, file)
        os.remove('expenses.csv')
    elif message.text in categories:
        category = message.text
        markup = types.ReplyKeyboardMarkup(row_width=2)
        markup.add('Статистика', 'Очистить статистику', 'Экспорт в CSV')
        if category in expenses:
            markup.add(category)
        msg = bot.reply_to(message, "Напиши сколько ты потратил на {}:".format(category), reply_markup=markup)
        bot.register_next_step_handler(msg, process_amount, category)
    else:
        msg = bot.reply_to(message, "Некорректная категория. Выбери категорию из списка.", reply_markup=get_categories_markup())
        bot.register_next_step_handler(msg, handle_message)

# Функция для обработки расхода
def process_amount(message, category):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
        conn = sqlite3.connect('expenses.db')
        c = conn.cursor()
        c.execute('INSERT INTO expenses_{} (category, amount) VALUES (?, ?)'.format(message.chat.id), (category, amount))  # используем message.chat.id
        conn.commit()
        conn.close()
        bot.reply_to(message, "Расходы на {} успешно добавлены.".format(category), reply_markup=get_categories_markup())
    except ValueError:
        msg = bot.reply_to(message, "Некорректная сумма. Попробуй ещё раз.", reply_markup=get_categories_markup())
        bot.register_next_step_handler(msg, process_amount, category)




bot.polling()