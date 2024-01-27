import telebot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, \
    ReplyKeyboardRemove
from database import Database
import os
import random


TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)
db_file: str = 'data.db'


def keyboard_create(buttons) -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for button_text in buttons:
        markup.add(telebot.types.KeyboardButton(button_text))
    return markup


def check_step(user_id, step) -> bool:
    with Database(db_file) as db:
        user_data = db.get_user_data(user_id)
    if user_data is None or user_data[2] < step:  # Прервём функцию, если пользователь не на этом шаге!
        print(f'Пользователь [{user_id}] не может использовать шаг {step}!')
        return False
    return True


@bot.message_handler(commands=['start'])
def send_welcome(message: Message) -> None:
    """Приветственное сообщение, добавляющее кнопку."""

    user_id: int = message.from_user.id
    image: str = random.choice(('media/house.jpg', 'media/house2.jpg', 'media/house3.jpg'))
    text: str = ('Слушай, {}, у меня есть испытание для тебя. В старом доме под номером *325* хранятся сокровища,'
                 'и я хочу, чтобы ты их украл. Это будет проверка, чтобы понять насколько ты настоящий вор. '
                 'Будь осторожен и умело используй свои навыки. Кстати, держи отмычку. Удачи! 🗺')
    markup = keyboard_create(['Я готов!'])

    # Сохраним данные пользователя.
    with Database(db_file) as db:
        db.save_user_data(user_id, False, 0)
    print(f'Пользователь [{user_id}] создан или сброшен.')

    bot.send_photo(
        chat_id=user_id,
        photo=open(image, 'rb'),
        caption=text.format(message.from_user.first_name),
        reply_markup=markup,
        parse_mode='Markdown'
    )


@bot.message_handler(func=lambda message: message.text == "Я готов!")
def send_image_with_keyboard(message) -> None:
    """Действия бота, после нажатия на 'Я готов!'."""

    user_id: str = message.from_user.id
    # Можно ли игроку попасть сюда?
    if not check_step(user_id, 0):
        return

    chat_id: str = message.chat.id
    keyboard = keyboard_create(['Использовать отмычку 🗝', 'Войти через окно 🪟'])
    photo: str = 'media/first_step.jpg'
    text: str = 'Нужно выбрать способ, как попасть в дом.'

    bot.send_photo(
        chat_id=chat_id,
        photo=open(photo, 'rb'),
        caption=text,
        reply_markup=keyboard
    )


@bot.message_handler(func=lambda message: message.text == "Войти через окно 🪟")
def handle_window_button(message):
    """Если пользователь выберет окно."""

    user_id: str = message.from_user.id
    # Можно ли игроку попасть сюда?
    if not check_step(user_id, 0):
        return

    chat_id: str = message.chat.id
    image: str = random.choice(('media/laser.jpg', 'media/laser2.jpg'))
    text: str = 'Вы попали в ловушку! Игра окночена...'
    markup = keyboard_create(['Начать заново ⬅️'])

    # # Удалим прошлое сообщение.
    # bot.delete_message(chat_id, message.message_id + 1)

    bot.send_photo(
        chat_id=chat_id,
        caption=text,
        photo=open(image, 'rb'),
        reply_markup=markup
    )

    # Сбрасываем данные т.к. игрок проиграл.
    with Database(db_file) as db:
        db.save_user_data(user_id, False, -1)


@bot.message_handler(func=lambda message: message.text in ("Использовать отмычку 🗝", "Вернуться обратно 🪜"))
def handle_window_button(message):
    """Если пользователь выберет дверь."""

    user_id: str = message.from_user.id
    # Можно ли игроку попасть сюда?
    if not check_step(user_id, 0):
        return

    chat_id: str = message.chat.id
    image: str = 'media/room_0.jpg'
    text: str = 'Нужно выбрать что делать дальше. Можно войти в комнату, либо подняться на второй этаж.'
    markup = keyboard_create(["Подняться 🪜", "Пройти на кухню 🚪"])

    bot.send_photo(
        chat_id=chat_id,
        caption=text,
        photo=open(image, 'rb'),
        reply_markup=markup
    )

    # Меняем шаг.
    with Database(db_file) as db:
        db.set_user_step(user_id, 1)


@bot.message_handler(func=lambda message: message.text == "Подняться 🪜")
def handle_window_button(message):
    """Если пользователь выберет подняться на второй этаж."""

    user_id: str = message.from_user.id
    # Можно ли игроку попасть сюда?
    if not check_step(user_id, 1):
        return

    chat_id: str = message.chat.id
    image: str = random.choice(('media/safe.jpg', 'media/safe2.jpg'))
    text: str = 'Тут абсолютно пусто. Только старый и ржавый сейф, покрытый паутиной 🕸'

    with Database(db_file) as db:
        user_data = db.get_user_data(user_id)

    # Поверка на наличие ключа.
    if user_data[1]:  # Ключ есть.
        markup = keyboard_create(["Открыть 🔐"])

        with Database(db_file) as db:  # Меняем шаг.
            db.set_user_step(user_id, 3)

    else:  # Ключ отсутствует.
        markup = keyboard_create(["Вернуться обратно 🪜"])

    bot.send_photo(
        chat_id=chat_id,
        caption=text,
        photo=open(image, 'rb'),
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "Пройти на кухню 🚪")
def handle_window_button(message):
    """Если пользователь пойдет на кухню."""

    user_id: str = message.from_user.id
    # Можно ли игроку попасть сюда?
    if not check_step(user_id, 1):
        return

    chat_id: str = message.chat.id
    image: str = 'media/key.jpg'
    text: str = ('Мне нужен какой-то код, чтобы открыть ящик. Мне кажется, мне кто-то говорил какие-то цифры, но не '
                 'могу вспомнить кто и где.')
    markup = keyboard_create(["Вернуться обратно 🪜"])

    bot.send_photo(
        chat_id=chat_id,
        caption=text,
        photo=open(image, 'rb'),
        reply_markup=markup
    )

    with Database(db_file) as db:  # Меняем шаг.
        db.set_user_step(user_id, 2)


@bot.message_handler(func=lambda message: message.text == "325")
def check_code(message):
    """Проверка кода для кухни"""

    user_id: str = message.from_user.id

    with Database(db_file) as db:
        has_key = db.get_user_data(user_id)

    # Можно ли игроку попасть сюда?
    if not check_step(user_id, 2) and has_key:
        return

    image: str = 'media/room_0.jpg'
    text: str = "Код верный! Ключ у вас в кармане."
    markup = keyboard_create(["Подняться 🪜", "Пройти на кухню 🚪"])

    bot.send_photo(
        chat_id=message.chat.id,
        caption=text,
        photo=open(image, 'rb'),
        reply_markup=markup
    )

    with Database(db_file) as db:  # Меняем даные пользователя.
        db.save_user_data(user_id, True, 1)


@bot.message_handler(func=lambda message: message.text == "Открыть 🔐")
def handle_window_button(message):
    """Если пользователь откроет сейф"""

    if not check_step(message.from_user.id, 3):
        return

    chat_id: str = message.chat.id
    text: str = ('Поздравляю! Ты смог открыть сейф! Ну а теперь тебе срочно нужно бежать, потому что я уже слышу '
                 'звук полицейской сирены! 🚔🚨')
    image: str = 'media/win.jpg'
    markup = keyboard_create(["Начать заново ⬅️"])

    bot.send_photo(
        chat_id=chat_id,
        caption=text,
        photo=open(image, 'rb'),
        reply_markup=markup
    )


@bot.message_handler(func=lambda message: message.text == "Начать заново ⬅️")
def reset_user_data(message):
    """Рестарт игры."""

    user_id: str = message.from_user.id
    markup = keyboard_create(['/start'])

    bot.send_message(
        chat_id=user_id,
        text='Чтобы начать заново, нажмите на кнопку, либо используйте /start',
        reply_markup=markup
    )


bot.polling(none_stop=True)
