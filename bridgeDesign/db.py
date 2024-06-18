from flask import Flask, flash, render_template, request, redirect, url_for
import sqlite3
import os
import threading
from sympy import sympify, SympifyError

# 确保database文件夹存在
database_folder = 'database'
if not os.path.exists(database_folder):
    os.makedirs(database_folder)

# 全局变量：数据库文件路径
database_path = os.path.join(database_folder, 'my_parameters.db')

# 确保templates文件夹存在
templates_folder = os.path.join(database_folder, 'templates')
if not os.path.exists(templates_folder):
    os.makedirs(templates_folder)

# 检查HTML模板文件是否存在，如果不存在则创建
html_files = {
    'index.html': '<html><body><h1>参数列表</h1>{% for parameter in parameters %}<p>{{ parameter.name }}: {{ parameter.value }}</p>{% endfor %}</body></html>',
    'add.html': '<html><body><h1>添加参数</h1><form method="post"><input type="text" name="name" /><input type="text" name="value" /><input type="submit" /></form></body></html>',
    'edit.html': '<html><body><h1>编辑参数</h1><form method="post"><input type="text" name="name" value="{{ parameter.name }}" /><input type="text" name="value" value="{{ parameter.value }}" /><input type="submit" /></form></body></html>'
}

def init_db():
    with sqlite3.connect(database_path) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS parameters
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      name TEXT NOT NULL,
                      value TEXT NOT NULL)''')
        conn.commit()


for filename, content in html_files.items():
    file_path = os.path.join(templates_folder, filename)
    if not os.path.isfile(file_path):
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)

# Flask应用程序
app = Flask(__name__, template_folder=templates_folder)
app.secret_key = '123456'


# 连接到SQLite数据库
def get_db_connection():
    conn = sqlite3.connect(os.path.join(database_folder, 'my_parameters.db'))
    conn.row_factory = sqlite3.Row
    return conn

def parse_input(input_str):
        # 从左到右找到第一个等号，等号左边的内容为变量名
        equal_index = input_str.find('=')
        if equal_index == -1:
            return None, None, None
        name = input_str[:equal_index].strip()

        # 从右到左找到最后一个等号，等号右边的内容为值和单位
        equal_index_r = input_str.rfind('=')
        if equal_index_r == -1:
            return None, None, None
        value_unit_str = input_str[equal_index_r + 1:].strip()

        # 找到值和单位的分界点，通常是数字和字母之间
        for i, char in enumerate(value_unit_str):
            if not char.isdigit() and char not in '.eE':
                # 分割值和单位
                value = value_unit_str[:i].strip()
                units = value_unit_str[i:].strip()
                break
        else:
            # 如果没有找到单位，整个字符串都是值
            value = value_unit_str
            units = ''
        
        action = name.split(' ')[0]
        name = name.split(' ')[1] 
        return action, name, value + ' ' + units

# 首页路由，显示所有参数
@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM parameters')
    parameters = cur.fetchall()
    conn.close()
    return render_template('index.html', parameters=parameters)

# 添加参数路由
@app.route('/add', methods=('GET', 'POST'))
def add():
    if request.method == 'POST':
        name = request.form['name']
        value = request.form['value']
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT * FROM parameters WHERE name = ?', (name,))
        existing_param = cur.fetchone()
        if existing_param:
            flash(f'警告：参数 "{name}" 已存在。')
        else:
            conn.execute('INSERT INTO parameters (name, value) VALUES (?, ?)',
                         (name, value))
            conn.commit()
            flash(f'参数 "{name}" 已添加。')
        conn.close()
        return redirect(url_for('index'))
    return render_template('add.html')

@app.route('/add_expression', methods=('POST',))
def add_expression():
    if request.method == 'POST':
        expression = request.form['expression']
        full_command = f'add {expression}'
        action, name, value = parse_input(full_command)
        if action == 'add':
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT * FROM parameters WHERE name = ?', (name,))
            existing_param = cur.fetchone()
            if existing_param:
                flash(f'警告：参数 "{name}" 已存在。')
            else:
                cur.execute('INSERT INTO parameters (name, value) VALUES (?, ?)',
                            (name, value))
                conn.commit()
                flash(f'参数 "{name}" 已添加。值为：{value}')
            conn.close()
        else:
            flash('无法识别的指令，请重新输入。')
        return redirect(url_for('index'))

# 编辑参数路由
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    conn = get_db_connection()
    parameter = conn.execute('SELECT * FROM parameters WHERE id = ?',
                             (id,)).fetchone()
    if request.method == 'POST':
        name = request.form['name']
        value = request.form['value']
        conn.execute('UPDATE parameters SET name = ?, value = ?'
                     ' WHERE id = ?',
                     (name, value, id))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    return render_template('edit.html', parameter=parameter)

# 删除参数路由
@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM parameters WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# 命令行界面线程
def cli_thread():
    conn = sqlite3.connect(database_path)
    c = conn.cursor()

    def add_parameter(name, value):
        c.execute("INSERT INTO parameters (name, value) VALUES (?, ?)", (name, value))
        conn.commit()

    def search_parameter(name):
        c.execute("SELECT value FROM parameters WHERE name=?", (name,))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return "Parameter not found."

    def del_parameter(name):
        c.execute("DELETE FROM parameters WHERE name=?", (name,))
        conn.commit()

    def change_parameter(name, value):
        c.execute("UPDATE parameters SET value=? WHERE name=?", (value, name))
        conn.commit()

    

    while True:
        input_str = input("请输入指令：")
        action, name, value = parse_input(input_str)
        if action == 'add':
            add_parameter(name, value)
            print(f"已添加参数：{name} = {value}")
        elif action == 'search':
            result = search_parameter(name)
            print(f"{name} = {result}" if result else "参数未找到。")
        elif action == 'del':
            del_parameter(name)
            print(f"已删除参数：{name}")
        elif action == 'change':
            change_parameter(name, value)
            print(f"已更新参数：{name} = {value}")
        else:
            print(action + '||' + name + '||' + value)
            print("无法识别的指令，请重新输入。")

# 启动命令行界面线程
threading.Thread(target=cli_thread, daemon=True).start()

# 运行Flask应用程序
if __name__ == '__main__':
    init_db()  # 初始化数据库
    threading.Thread(target=cli_thread, daemon=True).start()  # 启动CLI线程
    app.run(host='0.0.0.0', port=8080)  # 启动Flask应用程序
