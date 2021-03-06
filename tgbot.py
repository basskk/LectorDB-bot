import telebot
import config
import os
import time
import random
import utils
from telebot import types
from data_handler import SQLighter

bot = telebot.TeleBot(config.token)
need_login_student = set()
need_login_operator = set()
wait_response_operator = set()

operator_markup = types.ReplyKeyboardMarkup()
operator_markup.row('/confirm')
operator_markup.row('/tmt')

@bot.message_handler(commands=['start'])
def register(message):
    chat_id = message.chat.id
    if chat_id in need_login_student:
        need_login_student.remove(chat_id)
    if chat_id in need_login_operator:
        need_login_operator.remove(chat_id)

    markup = types.ReplyKeyboardMarkup()
    markup.row('/Student')
    markup.row('/Operator')
    bot.send_message(message.chat.id, '''Зарегестрируйтесь по одной из этих кнопок или отправьте одну из этих команд:
    /Student
    /Operator''', reply_markup=markup)

@bot.message_handler(commands=['status'])
def send_status(message):
    status = utils.check_user(message.chat.id)
    bot.send_message(message.chat.id, status)


#REGISTER AS OPERATOR STEP 1
@bot.message_handler(commands=['Operator'])
def ask_login_op(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "напишите: Имя Фамилия email \nпример: Иван Васин igorvasin@mail.ru", reply_markup=markup)
    need_login_operator.add(message.chat.id)


#REGISTER AS STUDENT STEP 1
@bot.message_handler(commands=['Student'])
def ask_login_stud(message):
    bot.send_message(message.chat.id, "напишите: Имя Фамилия группу \nпример: Иван Васин 185")
    need_login_student.add(message.chat.id)

#REGISTER AS OPERATOR STEP 2
@bot.message_handler(func=lambda message: message.chat.id in need_login_operator)
def chech_login_op(message):
    try:
        data = message.text.split(' ')
        name = data[0]
        lastname = data[1]
        email = data[2]
        if utils.reg_operator(message.chat.id, name, lastname, email):
            bot.send_message(message.chat.id, "Успешно")
            need_login_operator.remove(message.chat.id)
        else:
            bot.send_message(message.chat.id, "Что-то пошло не так. Проверьте еще раз свои данные, если все равно не получается, напишите @goozlike")
    except:
        bot.send_message(message.chat.id, "напишите: Имя Фамилия email \nпример: Иван Васин igorvasin@mail.ru\nчтобы начать все заново напишите /start")


#REGISTER AS STUDENT STEP 2
@bot.message_handler(func=lambda message: message.chat.id in need_login_student)
def chech_login_stud(message):
    try:
        data = message.text.split(' ')
        name = data[0]
        lastname = data[1]
        group = data[2]
        if utils.reg_student(message.chat.id, name, lastname, group):
            bot.send_message(message.chat.id, "Успешно")
            need_login_student.remove(message.chat.id)
        else:
            bot.send_message(message.chat.id, "Что-то пошло не так. Проверьте еще раз свои данные, если все равно не получается, напишите @goozlike")
    except:
        bot.send_message(message.chat.id, "напишите: Имя Фамилия группу \nпример: Иван Васин 185\nчтобы начать все заново напишите /start")


#подтверждение съемки операторами
@bot.message_handler(commands=['confirm'])
def send_confirm(message):
    status = utils.check_user(message.chat.id) 
    if status == 'op' or status == 'o/p':
        query = SQLighter(config.database_name).get_query(message.chat.id)
        print(message.chat.id)
        print(query)
        if query[0][0] is not None:
            markup = types.ReplyKeyboardMarkup()
            markup.row('Буду снимать')
            markup.row('Не буду снимать')
            bot.send_message(message.chat.id, query[0][1] + '\n' + query[0][2] + '\n' + query[0][3],  reply_markup=markup)
            wait_response_operator.add(message.chat.id)
        else:
            bot.send_message(message.chat.id, 'Похоже, что ничего не запланирвано.')
        
#cброс подтверждений
@bot.message_handler(commands=['abort'])
def abort_confirm(message):
    if message.chat.id in wait_response_operator:
        wait_response_operator.remove(message.chat.id)

    db = SQLighter(config.database_name)
    db.abort_confirm(message.chat.id)
    bot.send_message(message.chat.id, "Успешно",  reply_markup=operator_markup)
    print(db.get_all_queries(message.chat.id))
    

 
@bot.message_handler(func=lambda message: message.chat.id in wait_response_operator)
def commit_query(message):
    if message.text == 'Буду снимать':
        res = SQLighter(config.database_name).commit(message.chat.id, '1')
        if res:
            query = SQLighter(config.database_name).get_query(message.chat.id)
            if query[0][0] is not None:
                markup = types.ReplyKeyboardMarkup()
                markup.row('Буду снимать')
                markup.row('Не буду снимать')
                bot.send_message(message.chat.id, query[0][1] + '\n' + query[0][2] + '\n' + query[0][3],  reply_markup=markup)
                wait_response_operator.add(message.chat.id)
            else:
                wait_response_operator.remove(message.chat.id)
                bot.send_message(message.chat.id, 'Похоже, что ничего не запланирвано.', reply_markup = operator_markup)

        else:
            wait_response_operator.remove(message.chat.id)
            bot.send_message(message.chat.id, 'Похоже, что ничего не запланирвано.')

    elif message.text == 'Не буду снимать':
        res = SQLighter(config.database_name).commit(message.chat.id, '-1')
        if res:
            query = SQLighter(config.database_name).get_query(message.chat.id)
            if query[0][0] is not None:
                markup = types.ReplyKeyboardMarkup()
                markup.row('Буду снимать')
                markup.row('Не буду снимать')
                bot.send_message(message.chat.id, query[0][1] + '\n' + query[0][2] + '\n' + query[0][3],  reply_markup=markup)
                wait_response_operator.add(message.chat.id)
            else:
                wait_response_operator.remove(message.chat.id)
                bot.send_message(message.chat.id, 'Похоже, что ничего не запланирвано.', reply_markup = operator_markup)
        else:
            wait_response_operator.remove(message.chat.id)
            bot.send_message(message.chat.id, 'Похоже, что ничего не запланирвано.')


#handle student request to week timetable
@bot.message_handler(commands=['stud_tmt'])
def student_timetable(message):
    db = SQLighter(config.database_name)
    classes = db.get_stud_tmt(message.chat.id, 7)
    for c in classes:
        print(c)
        bot.send_message(message.chat.id, c[0] + '\n' + c[1] + '\n' + c[2])



#@bot.message_handler(commands=['test'])
#def find_file_ids(message):
#    for file in os.listdir('music/'):
#        if file.split('.')[-1] == 'ogg':
#            f = open('music/'+file, 'rb')
#            msg = bot.send_voice(message.chat.id, f, None)
#            # А теперь отправим вслед за файлом его file_id
#            bot.send_message(message.chat.id, msg.voice.file_id, reply_to_message_id=msg.message_id)
#        time.sleep(3)
#
#@bot.message_handler(commands=['game'])
#def game(message):
#    # Подключаемся к БД
#    db_worker = SQLighter(config.database_name)
#    # Получаем случайную строку из БД
#    row = db_worker.select_single(random.randint(1, utils.get_rows_count()))
#    # Формируем разметку
#    #markup = utils.generate_markup(row[2], row[3])
#    # Отправляем аудиофайл с вариантами ответа
#    #bot.send_voice(message.chat.id, row[1], reply_markup=markup)
#    # Включаем "игровой режим"
#    utils.set_user_game(message.chat.id, row[2])
#    # Отсоединяемся от БД
#    db_worker.close()
#
if __name__ == '__main__':
    bot.polling(none_stop=True)