from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

kb_1 = ReplyKeyboardMarkup(resize_keyboard=True)
b_1_1 = KeyboardButton("/help")
b_1_2 = KeyboardButton("/reg")
b_1_3 = KeyboardButton("/info")
b_1_4 = KeyboardButton("/delete")



ikb_1 = InlineKeyboardMarkup(row_width=2)
ikb_1_1 = InlineKeyboardButton(text= 'Your text here', url='Your URL here')
ikb_1_2 = InlineKeyboardButton(text= 'Your text here', url='Your URL here')

kb_1.add(b_1_1, b_1_2).insert(b_1_3).add(b_1_4)

ikb_1.add(ikb_1_1, ikb_1_2)

def get_cancel() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton('/cancel'))