from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_debugtoolbar import DebugToolbarExtension
import os
from mysql_db import MySQL
import mysql.connector as connector


login_man = LoginManager()

app = Flask(__name__)
application = app
app.secret_key = os.urandom(24)
""" toolbar = DebugToolbarExtension(app) """
app.config.from_pyfile('config.py')

mysql = MySQL(app)

login_man.init_app(app)
login_man.login_view = 'login'
login_man.login_message = 'need authorization'
login_man.login_message_category = 'danger'


class User(UserMixin):
    def __init__(self, user_id, login):
        super().__init__()
        self.id = user_id
        self.login = login


@login_man.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    search_user = "SELECT * FROM lab_py_users WHERE id = %s;"
    cursor.execute(search_user, (user_id,))
    db_user = cursor.fetchone()
    cursor.close()
    if db_user:
        return User(user_id=db_user.id, login=db_user.login)
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = dict(request.form)
        if user_data['login'] and user_data['password']:
            cursor = mysql.connection.cursor(named_tuple=True)
            search_user = "SELECT * FROM lab_py_users WHERE login = %s AND password_hash = SHA2(%s, 256);"
            cursor.execute(search_user, (
                user_data['login'], user_data['password'],))
            db_user = cursor.fetchone()
            cursor.close()
            if db_user:
                user_object = User(user_id=db_user.id, login=db_user.login)
                login_user(
                    user_object, remember=user_data.get('remember') == 'on')
                flash("u're logged in", 'success')
                return redirect(request.args.get('next') or url_for('index'))
            else:
                flash("incorrect login/pass", 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')


@app.route('/users')
def users():
    cursor = mysql.connection.cursor(named_tuple=True)
    search_user = "SELECT * FROM lab_py_users;"
    cursor.execute(search_user)
    users = cursor.fetchall()
    cursor.close()
    return render_template('users/index.html', users=users)


@app.route('/users/new')
@login_required
def new():
    return render_template('users/new.html', user={})


@app.route('/users/create', methods=['POST'])
@login_required
def create():
    login = request.form.get('login') or None
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    middle_name = request.form.get('middle_name')
    query = '''
    INSERT INTO lab_py_users (login, password_hash, first_name, last_name, middle_name)
    VALUES (%s, SHA2(%s, 256), %s, %s, %s )
    '''
    cursor = mysql.connection.cursor(named_tuple=True)
    try:
        cursor.execute(query, (login, password,
                               first_name, last_name, middle_name,))
    except connector.errors.DatabaseError as err:
        flash('Введены некорректные данные. Ошибка сохранения', 'danger')
        user = {
            'login': login,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'middle_name': middle_name
        }
        return render_template('users/new.html', user=user)
    mysql.connection.commit()
    cursor.close()
    flash(f"User {login} created successful", 'success')
    return redirect(url_for('users'))
