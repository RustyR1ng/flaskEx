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


def load_roles():
    cursor = mysql.connection.cursor(named_tuple=True)
    search_user = "SELECT id, name FROM lab_py_roles;"
    cursor.execute(search_user)
    roles = cursor.fetchall()
    cursor.close()
    return roles


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
    search_user = "SELECT lab_py_users.*, lab_py_roles.name AS role_name FROM lab_py_users LEFT OUTER JOIN lab_py_roles ON lab_py_users.role_id = lab_py_roles.id;"
    cursor.execute(search_user)
    users = cursor.fetchall()
    cursor.close()
    return render_template('users/index.html', users=users)


@app.route('/users/<int:user_id>')
@login_required
def show(user_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    search_user = "SELECT * FROM lab_py_users WHERE id = %s;"
    cursor.execute(search_user, (user_id,))
    user = cursor.fetchone()
    search_user_role = "SELECT * FROM lab_py_roles WHERE id = %s;"
    cursor.execute(search_user_role, (user.role_id,))
    role = cursor.fetchone()
    cursor.close()
    return render_template('users/show.html', user=user, role=role)


@app.route('/users/new')
@login_required
def new():
    return render_template('users/new.html', user={}, roles=load_roles())


@app.route('/users/<int:user_id>/edit')
@login_required
def edit(user_id):
    cursor = mysql.connection.cursor(named_tuple=True)
    search_user = "SELECT * FROM lab_py_users WHERE id = %s;"
    cursor.execute(search_user, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    return render_template('users/edit.html', user=user, roles=load_roles())


@app.route('/users/create', methods=['POST'])
@login_required
def create():
    login = request.form.get('login') or None
    password = request.form.get('password') or None
    first_name = request.form.get('first_name') or None
    last_name = request.form.get('last_name') or None
    middle_name = request.form.get('middle_name') or None
    role_id = request.form.get('role_id') or None
    query = '''
    INSERT INTO lab_py_users (login, password_hash, first_name, last_name, middle_name, role_id)
    VALUES (%s, SHA2(%s, 256), %s, %s, %s, %s )
    '''
    cursor = mysql.connection.cursor(named_tuple=True)
    try:
        cursor.execute(query, (login, password,
                               first_name, last_name, middle_name, role_id,))
    except connector.errors.DatabaseError as err:
        flash('Введены некорректные данные. Ошибка сохранения', 'danger')
        user = {
            'login': login,
            'password': password,
            'first_name': first_name,
            'last_name': last_name,
            'middle_name': middle_name,
            'role_id': role_id
        }
        return render_template('users/new.html', user=user, roles=load_roles())
    mysql.connection.commit()
    cursor.close()
    flash(f"User {login} created successful", 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:user_id>/update', methods=['POST'])
@login_required
def update(user_id):
    login = request.form.get('login') or None
    first_name = request.form.get('first_name') or None
    last_name = request.form.get('last_name') or None
    middle_name = request.form.get('middle_name') or None
    role_id = request.form.get('role_id') or None
    query = '''
    UPDATE lab_py_users SET login=%s, first_name=%s, last_name=%s, middle_name=%s, role_id=%s
    WHERE id=%s;
    '''
    cursor = mysql.connection.cursor(named_tuple=True)
    try:
        cursor.execute(query, (login, first_name, last_name,
                               middle_name, role_id, user_id,))
    except connector.errors.DatabaseError as err:
        flash('Введены некорректные данные. Ошибка сохранения', 'danger')
        user = {
            'id': user_id,
            'login': login,
            'first_name': first_name,
            'last_name': last_name,
            'middle_name': middle_name,
            'role_id': role_id
        }
        return render_template('users/edit.html', user=user, roles=load_roles())
    mysql.connection.commit()
    cursor.close()
    flash(f"User {login} updated successful", 'success')
    return redirect(url_for('users'))


@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete(user_id):
    return redirect(url_for('users'))
