from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
import aiosqlite
import aiofiles
import json
import os
import asyncio
from assets.data_dictionaries import class_dict, weekdays_dict


router = Router()
db_name = "database/data.sqlite3"
last_mtime = os.path.getmtime("assets/replacements.json")


async def notifier(bot: Bot):
    global last_mtime
    while True:
        current_mtime = os.path.getmtime("assets/replacements.json")
        if current_mtime != last_mtime:
            last_mtime = current_mtime
            async with aiosqlite.connect(db_name) as db:
                async with aiofiles.open("assets/replacements.json", "r", encoding="utf-8") as f:
                    content = await f.read()
                    data = await asyncio.to_thread(json.loads, content)
                classes = list(data[0].keys())
                weekday = list(data[0][classes[0]].keys())[0]
                cursor = await db.execute("""
                SELECT * FROM users WHERE is_subscribe = 1
                """)
                result = await cursor.fetchall()
                for element in result:
                    if element[2] in classes:
                        try:
                            await bot.send_message(element[1],
                                                   f"Замена для {class_dict[element[2]]} на {weekdays_dict[weekday]}")
                            lessons_lst = list(data[0][element[2]][weekday].values())
                            lessons_numbers = list(data[0][element[2]][weekday].keys())
                            lessons_lst_1 = []
                            for i in range(len(lessons_lst)):
                                lessons_lst_1.append(f"{lessons_numbers[i][-1]} Урок: {lessons_lst[i]["Lesson"]}; Кабинет: {lessons_lst[i]["Auditorium"]}")
                            await bot.send_message(element[1], ("\n").join(lessons_lst_1))
                        except Exception:
                            pass
                await cursor.close()
        await asyncio.sleep(600)


def get_main_inline_keyboard_1():
    keyboard_to_class = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="7А", callback_data="class_7a")],
            [InlineKeyboardButton(text="8А", callback_data="class_8a")],
            [InlineKeyboardButton(text="8Б", callback_data="class_8b")],
            [InlineKeyboardButton(text="9А", callback_data="class_9a")],
            [InlineKeyboardButton(text="9Б", callback_data="class_9b")],
            [InlineKeyboardButton(text="10А", callback_data="class_10a")],
            [InlineKeyboardButton(text="10Б", callback_data="class_10b")],
            [InlineKeyboardButton(text="10В", callback_data="class_10c")],
            [InlineKeyboardButton(text="11А", callback_data="class_11a")],
            [InlineKeyboardButton(text="11Б", callback_data="class_11b")],
            [InlineKeyboardButton(text="11В", callback_data="class_11c")]
        ]
    )
    return keyboard_to_class


def get_main_inline_keyboard_2():
    keyboard_to_shedule = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Понедельник", callback_data="Weekday_1")],
            [InlineKeyboardButton(text="Вторник", callback_data="Weekday_2")],
            [InlineKeyboardButton(text="Среда", callback_data="Weekday_3")],
            [InlineKeyboardButton(text="Четверг", callback_data="Weekday_4")],
            [InlineKeyboardButton(text="Пятница", callback_data="Weekday_5")],
            [InlineKeyboardButton(text="Суббота", callback_data="Weekday_6")]
        ]
    )
    return keyboard_to_shedule

def get_main_reply_keyboard():
    button_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Старт"), KeyboardButton(text="Команды для работы с ботом(помощь)")],
            [KeyboardButton(text="Выбрать класс обучения"), KeyboardButton(text="Посмотреть расписание уроков")],
            [KeyboardButton(text="Подписаться на рассылку сообщений"), KeyboardButton(text="Отписаться от рассылки соообщений")]
        ]
    )
    return button_keyboard


@router.message(Command("start"))
@router.message(F.text == "Старт")
async def start(message: Message):
    await message.answer(
        """
        Привет, тебя приветсвует <strong>ТГ-бот</strong> для учеников <u>ГОУ РК ФМЛИ</u>, который должен сделать процесс донесения информации об заменах уроков более быстрой и удобной
        Пропиши команду <strong>/help</strong>, чтобы увидеть команды, позволяющие работать с ботом
            """,
        parse_mode="HTML", reply_markup=get_main_reply_keyboard())


@router.message(Command("help"))
@router.message(F.text == "Команды для работы с ботом(помощь)")
async def help(message: Message):
    await message.answer("""
    <strong>Вот список команд, которые можно использовать:</strong>
    /start - начать
    /help - получить информацию о доступных командах
    /select_class - позволяет выбрать класс обучения, открывает доступ к командам ниже
    
    /subscribe - позволяет выбрать класс и подписаться на рассылку сообщений об заменах уроков и перестановок кабинетов, <strong>может быть выполнено, только если вы указали класс обучения!</strong>
    /unsubscribe - позволяет отписаться от рассылки
    /lessons - посмотреть какие уроки у вас в определенный день недели
    """, parse_mode="HTML")


@router.message(Command("subscribe"))
@router.message(F.text == "Подписаться на рассылку сообщений")
async def subscribe(message: Message):
    async with aiosqlite.connect(db_name) as db:
        user_id = message.from_user.id
        cursor = await db.execute("""
        SELECT * FROM users WHERE user_id = ?
        """, (user_id,))
        result = await cursor.fetchone()
        if not result:
            await message.answer("Вы не указали свой класс обучения")
            return
        else:
            await db.execute("""
            UPDATE users SET is_subscribe = ? WHERE user_id = ?
            """, (True, user_id))
            await message.answer("Вы успешно подписались на рассылку сообщений об заменах")

        await cursor.close()
        await db.commit()


@router.message(Command("unsubscribe"))
@router.message(F.text == "Отписаться от рассылки соообщений")
async def unsubscribe(message: Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(db_name) as db:
        cursor = await db.execute("""
        SELECT * FROM users WHERE user_id = ?
        """, (user_id,))
        result = await cursor.fetchone()
        if not result:
            await message.answer("Вы не указали свой класс обучения")
            return
        elif result[3] == False:
            await message.answer("Вы не подписаны на рассылку сообщений об заменах")
            return
        else:
            await db.execute("""
            UPDATE users SET is_subscribe = ? WHERE user_id = ?
            """, (False, user_id))
            await message.answer("Вы успешно отписались от рассылки сообщений об заменах")

        await cursor.close()
        await db.commit()


@router.message(Command("select_class"))
@router.message(F.text == "Выбрать класс обучения")
async def select_class(message: Message, state: FSMContext):
    user_id = str(message.from_user.id)
    await message.answer("Выберите ваш класс обучения", reply_markup=get_main_inline_keyboard_1())
    await state.update_data(user_id=user_id)
    await state.set_state("user")


@router.callback_query(lambda x: "class_" in x.data)
@router.message(StateFilter("user"))
async def select_class_1(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    if not user_id:
        user_id = str(callback.from_user.id)
    classname = callback.data.split("_")[1]
    async with aiosqlite.connect(db_name) as db:
        await callback.answer(f"Был выбран класс {class_dict[classname]}")
        try:
            await db.execute("""
            INSERT INTO users (user_id, classname) VALUES (?, ?)
            """, (user_id, classname))
        except Exception:
            await db.execute("""
            UPDATE users SET classname = ? WHERE user_id = ?
            """, (classname, user_id))
        await db.commit()
        await state.clear()


@router.message(Command("lessons"))
@router.message(F.text == "Посмотреть расписание уроков")
async def lessons(message: Message, state: FSMContext):
    async with aiosqlite.connect(db_name) as db:
        user_id = str(message.from_user.id)
        cursor = await db.execute("""
        SELECT classname FROM users WHERE user_id = ?
        """, (user_id,))
        result = await cursor.fetchone()
        if not result:
            await message.answer("Вы не указали свой класс обучения")
            return
        else:
            classname = result[0]
            await state.update_data(classname=classname)
            await state.set_state("weekday_lessons")
            await message.answer("Выберите день недели", reply_markup=get_main_inline_keyboard_2())
        await cursor.close()


@router.callback_query(lambda x: "Weekday_" in x.data)
@router.message(StateFilter("weekday_lessons"))
async def select_weekday(callback: CallbackQuery, state: FSMContext):
    weekday = callback.data
    data = await state.get_data()
    classname = data.get("classname")
    if not classname:
        user_id = str(callback.from_user.id)
        async with aiosqlite.connect(db_name) as db:
            cursor = await db.execute("""
               SELECT classname FROM users WHERE user_id = ?
               """, (user_id,))
            result = await cursor.fetchone()
            classname = result[0]


    await callback.message.answer(f"Расписание на {weekdays_dict[weekday]} для {class_dict[classname]}")
    async with aiofiles.open("assets/shedule.json", "r", encoding="utf-8") as f:
        content = await f.read()
        shedule_data = await asyncio.to_thread(json.loads, content)
    async with aiofiles.open("assets/replacements.json", "r", encoding="utf-8") as f:
        content = await f.read()
        replacements_data = await asyncio.to_thread(json.loads, content)

    shedule_lessons = shedule_data[0][classname][weekday]
    lessons_lst = []
    counter = 1
    if weekday in replacements_data[0][classname].values():
        replacements_lessons = replacements_data[0][classname][weekday]
        for element in shedule_lessons:
            if element in list(replacements_lessons.keys()):
                element_lst = list(replacements_lessons[element].values())
                lessons_lst.append(f"{counter} Урок: {element_lst[0]};  Кабинет: {element_lst[1]}")
                counter += 1
            else:
                element_lst = list(shedule_lessons[element].values())
                lessons_lst.append(f"{counter} Урок: {element_lst[0]};  Кабинет: {element_lst[1]}")
                counter += 1
    else:
        for element in shedule_lessons:
            element_lst = list(shedule_lessons[element].values())
            lessons_lst.append(f"{counter} Урок: {element_lst[0]};  Кабинет: {element_lst[1]}")
            counter += 1
    await callback.message.answer(("\n").join(lessons_lst))
    await state.clear()