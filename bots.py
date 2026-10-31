import telebot
from telebot import types, custom_filters
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage
from config import TOKEN

bot = telebot.TeleBot(TOKEN, state_storage=StateMemoryStorage())


SAVOLLAR = [
    ["Python'da ro'yxat qaysi qavsda yoziladi?", ["( )", "[ ]", "{ }"], 1],
    ["2 ** 3 nechaga teng?", ["6", "8", "9"], 1],
    ["Bot tokenini kim beradi?", ["@BotFather", "@Python", "Google"], 0],
]

class Quiz(StatesGroup):
    ism = State()
    savol = State()


def menyu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🎮 Boshlash", "ℹ️ Yordam")
    return kb


@bot.message_handler(commands=["start"], state="*")
def start(m):
    bot.delete_state(m.from_user.id, m.chat.id)
    bot.send_message(m.chat.id, "Salom! 🧠 Mini viktorinaga xush kelibsiz.",
                     reply_markup=menyu())


@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def yordam(m):
    bot.send_message(m.chat.id,
                     "🎮 Boshlash — 3 ta savol. Javob tugmasini bosing.\n"
                     "/cancel — to'xtatish")


def savol_yubor(chat_id, i):
    savol, variantlar, _ = SAVOLLAR[i]
    kb = types.InlineKeyboardMarkup()
    for j, v in enumerate(variantlar):
        kb.add(types.InlineKeyboardButton(v, callback_data=f"javob_{j}"))
    bot.send_message(chat_id, f"❓ {i + 1}-savol: {savol}", reply_markup=kb)


@bot.message_handler(commands=["test"])
def test(m):
    savol_yubor(m.chat.id, 0)

@bot.message_handler(commands=["cancel"], state="*")
def cancel(m):
    if bot.get_state(m.from_user.id, m.chat.id) is None:
        return
    bot.delete_state(m.from_user.id, m.chat.id)
    bot.send_message(m.chat.id, "❌ To'xtatildi", reply_markup=menyu())


@bot.message_handler(func=lambda m: m.text == "🎮 Boshlash")
def boshlash(m):
    bot.set_state(m.from_user.id, Quiz.ism, m.chat.id)
    bot.send_message(m.chat.id, "Ismingiz?", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=Quiz.ism)
def ism_qabul(m):
    bot.set_state(m.from_user.id, Quiz.savol, m.chat.id)
    with bot.retrieve_data(m.from_user.id, m.chat.id) as data:
        data["ism"] = m.text
        data["i"] = 0
        data["ball"] = 0
    savol_yubor(m.chat.id, 0)


@bot.message_handler(state=Quiz.savol)
def savol_matn(m):
    bot.send_message(m.chat.id, "Tugmalardan birini bosing 👆 (yoki /cancel)")


@bot.callback_query_handler(func=lambda call: call.data.startswith("javob_"))
def javob(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if bot.get_state(user_id, chat_id) != Quiz.savol.name:
        bot.answer_callback_query(call.id, "O'yin tugagan. 🎮 Boshlash ni bosing",
                                  show_alert=True)
        return

    tanlov = int(call.data.split("_")[1])

    with bot.retrieve_data(user_id, chat_id) as data:
        i = data["i"]
        togri = SAVOLLAR[i][2]
        if tanlov == togri:
            data["ball"] += 1
            belgi = "✅ To'g'ri!"
        else:
            belgi = "❌ Xato. To'g'ri javob: " + SAVOLLAR[i][1][togri]
        data["i"] = i + 1
        ism, ball, keyingi = data["ism"], data["ball"], data["i"]

    bot.edit_message_text(f"❓ {i + 1}-savol: {SAVOLLAR[i][0]}\n{belgi}",
                          chat_id, call.message.message_id)
    bot.answer_callback_query(call.id)

    if keyingi < len(SAVOLLAR):
        savol_yubor(chat_id, keyingi)
    else:
        bot.delete_state(user_id, chat_id)
        bot.send_message(chat_id, f" {ism}, natijangiz: {ball}/{len(SAVOLLAR)}",
                         reply_markup=menyu())


@bot.message_handler(func=lambda m: True)
def boshqa(m):
    bot.send_message(m.chat.id, "Pastdagi tugmalardan foydalaning",
                     reply_markup=menyu())


bot.infinity_polling()