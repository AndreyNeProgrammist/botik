from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from transformers import pipeline
import asyncio

# Токен вашего бота
BOT_TOKEN = "7693149839:AAEHpPvqdM4F3zhjxm1HJfe4ipy6sEUanVE"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация нейросети через Hugging Face
generator = pipeline("text-generation", model="sberbank-ai/rugpt3small_based_on_gpt2")

# Структура для хранения информации о пользователях
user_data = {}

# Расширенная база знаний
knowledge_base = """
1. Используйте светодиодные лампы: они потребляют на 75% меньше энергии по сравнению с традиционными лампами накаливания.
2. Выключайте устройства, которые не используются, из розетки: в режиме ожидания они могут потреблять до 10% общей энергии.
3. Утепляйте окна и двери: это поможет сократить расходы на отопление зимой и охлаждение летом.
4. Используйте энергосберегающую бытовую технику с классом энергоэффективности A+ и выше.
5. Стирайте вещи в холодной воде и на полных загрузках, чтобы уменьшить потребление энергии.
6. Используйте многозонные тарифы на электроэнергию, чтобы платить меньше за электричество в ночное время.
7. Регулярно чистите фильтры в кондиционерах и отопительных системах для их более эффективной работы.
8. Замените старые приборы на новые, более энергоэффективные.
"""

# Создание клавиатур
def create_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Задать вопрос"))
    builder.add(KeyboardButton(text="Калькулятор энергопотребления"))
    builder.add(KeyboardButton(text="Назад"))
    return builder.as_markup(resize_keyboard=True)

main_menu = create_main_menu()
back_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Назад")]], resize_keyboard=True)

# Обработчики команд
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "Привет! Я бот-консультант по энергосбережению. Нажми 'Задать вопрос', чтобы получить ответ на свой вопрос, или используй калькулятор энергопотребления.",
        reply_markup=main_menu
    )

@dp.message(lambda message: message.text == "Задать вопрос")
async def ask_question(message: types.Message):
    await message.answer(
        "Напишите свой вопрос, и я постараюсь ответить.",
        reply_markup=back_menu
    )

@dp.message(lambda message: message.text == "Калькулятор энергопотребления")
async def energy_calculator(message: types.Message):
    user_data[message.chat.id] = {"step": 1}
    await message.answer(
        "Введите площадь вашего жилья в квадратных метрах.",
        reply_markup=back_menu
    )

@dp.message(lambda message: message.text == "Назад")
async def go_back(message: types.Message):
    user_data.pop(message.chat.id, None)  # Удаляем данные пользователя
    await message.answer(
        "Вы вернулись в главное меню.",
        reply_markup=main_menu
    )

@dp.message()
async def handle_input(message: types.Message):
    chat_id = message.chat.id
    step = user_data.get(chat_id, {}).get("step")

    if step == 1:
        try:
            area = float(message.text)
            user_data[chat_id]["area"] = area
            user_data[chat_id]["step"] = 2
            await message.answer(
                "Введите средний расход электроэнергии на квадратный метр в киловатт-часах.",
                reply_markup=back_menu
            )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите число. Например: 50.",
                reply_markup=back_menu
            )
    elif step == 2:
        try:
            consumption_per_m2 = float(message.text)
            area = user_data[chat_id].get("area")
            total_consumption = area * consumption_per_m2
            user_data.pop(chat_id, None)  # Завершаем сценарий

            await message.answer(
                f"Ваше общее потребление электроэнергии составляет примерно {total_consumption:.2f} кВт·ч.",
                reply_markup=main_menu
            )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите число. Например: 5.",
                reply_markup=back_menu
            )
    else:
        user_question = message.text
        context = (
            "Энергосбережение включает в себя использование энергосберегающих технологий, утепление домов, "
            "выключение ненужного освещения и использование экологически чистой энергии.\n"
            f"Дополнительная информация:\n{knowledge_base}"
        )

        try:
            generated = generator(
                f"Вопрос: {user_question}\nКонтекст: {context}\nОтвет:",
                max_new_tokens=100,
                truncation=True
            )
            answer = generated[0]['generated_text'].split('Ответ:')[-1].strip()
            await message.answer(f"Ответ: {answer}", reply_markup=back_menu)
        except Exception as e:
            await message.answer(
                "Извините, произошла ошибка при обработке вашего вопроса. Попробуйте снова.",
                reply_markup=back_menu
            )
            print(f"Ошибка: {e}")

# Запуск бота
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
