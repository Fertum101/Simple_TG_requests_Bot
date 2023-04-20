from aiogram import Bot, Dispatcher, executor, types
from config import API_TOKEN, INFO_COMMAND, START_COMMAND, HELP_COMMAND
from keyboard import kb_1, ikb_1, get_cancel
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from array import *
import SQLite_db


storage = MemoryStorage()
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot=bot, storage=storage)
request_num = 0
clients = []
requests = []


async def on_startup(_):
    await SQLite_db.db_connect()
    print("Я переродился!")
    
class ClientStatesGroup(StatesGroup):
    problem = State()
    adress = State()
    phone = State()
    
class DeleteReqGroup(StatesGroup):
    req_num = State()
    
    
# Команды
@dp.message_handler(commands='start')
async def start_command(message: types.Message):
    await bot.send_photo(chat_id = message.chat.id, photo = 'Photo URL', caption = START_COMMAND, parse_mode = 'HTML', reply_markup = kb_1)
    await message.delete()

@dp.message_handler(commands='help')
async def help_command(message: types.Message):
    await bot.send_message(chat_id = message.chat.id,text = HELP_COMMAND, parse_mode = 'HTML')
    await message.delete()
   
@dp.message_handler(commands='info')
async def info_command(message: types.Message):
    await bot.send_message(chat_id = message.chat.id,text = INFO_COMMAND, parse_mode = 'HTML', reply_markup = ikb_1)
    await message.delete()
    
@dp.message_handler(commands=['cancel'], state='*')
async def cancel_reg(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        return
    await message.reply('Отменено', reply_markup=kb_1)
    await state.finish() 
    
@dp.message_handler(commands='delete', state=None)
async def delete_command(message: types.Message, state: FSMContext):
    await DeleteReqGroup.req_num.set()
    async with state.proxy() as data:
        data['user_id'] = message.from_user.username
        users = SQLite_db.cur.execute("SELECT user_id FROM request").fetchall()
        
        if users.count((message.from_user.username,)) != 0:
            await DeleteReqGroup.req_num.set()
            await bot.send_message(chat_id = message.chat.id, text = "Отправьте номер заявки для отмены", reply_markup = get_cancel())
        else:
            await bot.send_message(chat_id = message.chat.id, text = "Заявок на ваше имя нет!", reply_markup = kb_1)
            await state.finish()
        
    await message.delete()
    
    
# Состояние удаления заявки
@dp.message_handler(lambda message: message.text, content_types=['text'], state=DeleteReqGroup.req_num)
async def delete_req(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['req_num'] = message.text
        data['user_id'] = message.from_user.username
        
        users = SQLite_db.cur.execute("SELECT user_id FROM request").fetchall()
        reqs = SQLite_db.cur.execute("SELECT req_id FROM request").fetchall()
        
        if users.count((message.from_user.username,)) != 0 and reqs.count((int(data['req_num']),)) != 0:
            if users[reqs.index((int(data['req_num']),))] == (data['user_id'],):
                print("Удалил " + data['req_num'] + " заявку!")
                
                SQLite_db.cur.execute("DELETE FROM request WHERE req_id = ? AND user_id = ?", (data['req_num'], data['user_id'],))
                SQLite_db.db.commit()
                
                await bot.send_message(chat_id = message.chat.id, text = "Заявка №" + str(data['req_num']) + " отменена!", reply_markup = kb_1)
                await bot.send_message(chat_id = 'Your chat_id here', text = "Заявка №" + str(data['req_num']) + " от @" + data['user_id'] + " отменена!")
            else:
                await bot.send_message(chat_id = message.chat.id, text = "Заявка №" + str(data['req_num']) + " на ваше имя не найдена!", reply_markup = kb_1)
        else:
            await bot.send_message(chat_id = message.chat.id, text = "Заявка №" + str(data['req_num']) + " на ваше имя не найдена!", reply_markup = kb_1)
                   
    await state.finish()
    
    
# Состояние регистрации заявки
@dp.message_handler(commands='reg', state=None)
async def reg_command(message: types.Message) -> None:
    await ClientStatesGroup.problem.set()
    await bot.send_message(chat_id = message.chat.id, text = "Опишите вашу проблему максимально подробно", reply_markup = get_cancel())
    await message.delete()
    
@dp.message_handler(lambda message: not message.text, state='*')
async def check_problem(message: types.Message):
    return await message.reply('Напишите текстом')

@dp.message_handler(lambda message: message.text, content_types=['text'], state=ClientStatesGroup.problem)
async def get_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['problem'] = message.text
    await ClientStatesGroup.next()
    await message.reply('Напишите адрес, по которому требуется выполнение заявки (Район, улица, дом)')
    
@dp.message_handler(lambda message: message.text, content_types=['text'], state=ClientStatesGroup.adress)
async def get_adress(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['adress'] = message.text
    await ClientStatesGroup.next()
    await message.reply('Напишите ваш номер телефона (Или имя в Telegram) для связи.')

@dp.message_handler(lambda message: message.text, content_types=['text'], state=ClientStatesGroup.phone)
async def get_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
        global request_num
        global clients
        global requests
        request_num += 1
        
        if clients.count(message.chat.id) == 0:
            clients.append(message.chat.id)
            requests.append([request_num])
        else:
            requests[clients.index(message.chat.id)].append(request_num)
            
        print(clients)
        print(requests)

    async with state.proxy() as data:
        SQLite_db.cur.execute("INSERT INTO request (problem, adress, phone, user_id) VALUES ( ?, ?, ?, ?)", (data['problem'], data['adress'], data['phone'], message.from_user.username))
        SQLite_db.db.commit()
        
        reqs = await SQLite_db.get_all_requests()
        await message.reply('Ваша заявка зарегестрирована! Мастер свяжется с вами в ближайшее время для обсуждения деталей заявки.')
        
        await bot.send_message(chat_id = message.from_user.id, text= "Заявка №" + str(reqs[-1][0]) + "\nЗаявленная проблема:\n" + data['problem'] + '\nАдресс:\n' + data['adress'] + '\nТелефон для связи:\n' + data['phone'], reply_markup = kb_1)
        await bot.send_message(chat_id = 'Your chat_id here', text = "Заявка №" + str(reqs[-1][0]) + ". От @" + message.from_user.username + "\nЗаявленная проблема:\n" + data['problem'] + '\nАдресс:\n' + data['adress'] + '\nТелефон для связи:\n' + data['phone'])
    
    await state.finish()



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates = True, on_startup = on_startup) 