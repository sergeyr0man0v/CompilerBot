import os
import subprocess
import telebot
from telebot import types
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start', 'hello'], content_types=['text'])
def send_welcome(message):
    bot.reply_to(message, "Hello")


@bot.message_handler(commands=['compile', 'interpret'], content_types=['text'])
def compile_offer(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    py_btn = types.KeyboardButton('Python3')
    cxx_btn = types.KeyboardButton('C++17')

    markup.add(py_btn, cxx_btn)
    text = bot.send_message(message.chat.id, 'Choose language', reply_markup=markup)
    bot.register_next_step_handler(text, compile_text)


def compile_text(message):
    lang = message.text
    if lang.lower() not in ('python3', 'c++17'):
        bot.send_message(message.chat.id, "Incorrect language")
    else:
        text = 'Input your code [and input data] in format:\n' \
               'your-code-should be here[===your-input-data]\n\n' \
               'Example:\n' \
               'x = int(input())\n' \
               'print(x + 3)\n' \
               '===\n' \
               '4'
        response = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(response, compiler, lang)


def compiler(message, lang):
    code, inp_data = '', ''
    if '===' in message.text:
        code, inp_data = message.text.split('===')
    else:
        code = message.text
    if code == '':
        bot.send_message(message.chat.id, "There is nothing to compile")
    else:
        result = None
        if lang.lower() == 'python3':
            result = subprocess.run(f"cat << EOF > awesome-solution.py \n{code}\nEOF\n"
                                    f'python3 awesome-solution.py {inp_data}', shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            subprocess.run('rm awesome-solution.py', shell=True)
        elif lang.lower() == 'c++17':
            result = subprocess.run(f"cat << EOF > awesome-solution.cpp \n{code}\nEOF\n"
                                    f'g++ awesome-solution.cpp -o a.out &&'
                                    f'./a.out << EOF \n{inp_data}\nEOF', shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            subprocess.run('rm awesome-solution.cpp', shell=True)
        text = ''
        if result.returncode == 0:
            text = result.stdout
        else:
            text = result.stderr
        if not text.strip():
            text = 'output is empty'
        bot.send_message(message.chat.id, text)


@bot.message_handler(commands=['python-shell'], content_types=['text'])
def python_shell_offer(message):
    text = bot.send_message(message.chat.id, 'Input "exit" to exit')
    bot.register_next_step_handler(text, python_shell)


def python_shell(message):
    if message.text == 'exit':
        bot.send_message(message.chat.id, "Ok, bro. I'm done")
    else:
        code = message.text
        if code[0].isdigit():
            code = f'print({code})'
        if code == '':
            bot.send_message(message.chat.id, "There is nothing to compile")
        else:
            result = subprocess.run(f"cat << EOF > awesome-solution.py \n{code}\nEOF\n"
                                    f'python3 awesome-solution.py', shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            subprocess.run('rm awesome-solution.py', shell=True)
            text = ''
            if result.returncode == 0:
                text = result.stdout
            else:
                text = result.stderr
            if not text.strip():
                text = 'output is empty'
            response = bot.send_message(message.chat.id, text)
            bot.register_next_step_handler(response, python_shell)


@bot.message_handler(commands=['make-file'], content_types=['text'])
def make_file_offer(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    py_btn = types.KeyboardButton('.py')
    cxx_btn = types.KeyboardButton('.cpp')
    txt_btn = types.KeyboardButton('.txt')
    custom_btn = types.KeyboardButton('custom file')

    markup.add(py_btn, cxx_btn, txt_btn, custom_btn)
    text = bot.send_message(message.chat.id, 'Choose language', reply_markup=markup)
    bot.register_next_step_handler(text, make_file_text_inp)


def make_file_text_inp(message):
    lang = message.text
    if lang.lower() == 'custom file':
        text = bot.send_message(message.chat.id, "Input extension")
        bot.register_next_step_handler(text, make_file_text_inp)
    else:
        text = 'Input your code [and file name] in format:\n' \
               'your-code-should be here[===file name]\n\n' \
               'Example:\n' \
               'a = int(input())\n' \
               'b = int(input())\n' \
               'print(a + b)\n' \
               '===\n' \
               'sum.py'
        response = bot.send_message(message.chat.id, text)
        bot.register_next_step_handler(response, make_file, lang)


def make_file(message, lang):
    code, filename = '', 'awesome-solution'
    if '===' in message.text:
        code, filename = message.text.split('===')
    else:
        code = message.text
    if filename[-len(lang):] != lang:
        filename += lang
    result = subprocess.run(f"cat << EOF > {filename} \n{code}\nEOF\n", shell=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
    if result.returncode == 0:
        if lang.lower() == '.py':
            result = subprocess.run(f'autopep8 --in-place --aggressive {filename}', shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        elif lang.lower() in ('.cpp', '.hpp', '.h'):
            result = subprocess.run(f'clang-format -style=google -i {filename}', shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        doc = open(filename, 'rb')
        bot.send_document(message.chat.id, doc)
    else:
        bot.send_message(message.chat.id, result.stderr)
    subprocess.run(f'rm {filename}', shell=True)


@bot.message_handler(content_types=['audio'])
def echo_audio(message):
    print(message)
    bot.send_message(message.chat.id, message)


"""@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)"""

bot.infinity_polling()
