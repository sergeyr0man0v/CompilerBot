import os
import subprocess
import telebot
import signal
from telebot import types
from dotenv import load_dotenv
import time

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)


def async_process(cmd):
    start = time.time()
    time.sleep(0.1)
    res = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, shell=True, encoding='utf-8', preexec_fn=os.setsid)
    while time.time() - start < 4 and res.poll() is None:
        print(time.time())
        time.sleep(0.2)
    if res.poll() is None:
        os.killpg(os.getpgid(res.pid), signal.SIGTERM)
        return 'Too long for me', 'No errors'
    elif res.poll() == 0:
        return res.stdout.read(), res.stderr.read()
    else:
        return res.stderr.read(), res.stdout.read()


@bot.message_handler(commands=['start', 'hello'], content_types=['text'])
def send_welcome(message):
    bot.reply_to(message, "Hello")


@bot.message_handler(commands=['help'], content_types=['text'])
def help_cmd(message):
    text = "Allowed commands:\n" \
           "1) /compile or /interpret (C++17 or Python3 code allowed).\n\tWill compile your code and return program output.\n" \
           "\tYou can add input data in your message if you need.\n" \
           "2) /python-shell\n\tSomething similar to the classic python-shell\n" \
           "3) /make-file\n\tWill make and return file with necessary extension"
    bot.reply_to(message, text)


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
        ''' TODO: run commands from user with limited rights '''
        if any(i in code for i in
               ("os", "subprocess", "open", "shututil", "ls", "cd", "touch", "filesystem", "fstream")):
            bot.send_message(message.chat.id, "Let's not")
            return
        result = None
        if lang.lower() == 'python3':
            filename = 'awesome-solution.py'
            result = subprocess.run(f"cat << EOF > {filename} \n{code}\nEOF\n", shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            result.stdout, result.stderr = async_process(f'python3 {filename} {inp_data}')
            subprocess.run(f'rm {filename}', shell=True)
        elif lang.lower() == 'c++17':
            filename = 'awesome-solution.cpp'
            result = subprocess.run(f"cat << EOF > {filename} \n{code}\nEOF\n", shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            result.stdout, result.stderr = async_process(f'g++ awesome-solution.cpp -o a.out &&'
                                                         f'./a.out << EOF \n{inp_data}\nEOF')
            subprocess.run(f'rm {filename}', shell=True)
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
            ''' TODO: run commands from user with limited rights '''
            if any(i in code for i in ("os", "subprocess", "open", "shututil", "ls", "cd", "touch")):
                bot.send_message(message.chat.id, "Let's not")
                return
            filename = 'awesome-solution.py'
            result = subprocess.run(f"cat << EOF > {filename} \n{code}\nEOF\n", shell=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            result.stdout, result.stderr = async_process(f'python3 {filename}')
            subprocess.run(f'rm {filename}', shell=True)
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


@bot.message_handler(func=lambda msg: True, content_types=['text'])
def echo_all(message):
    bot.register_next_step_handler(message, make_file, 'txt')


bot.infinity_polling()

