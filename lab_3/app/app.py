from flask import Flask, render_template, url_for, request, session, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_debugtoolbar import DebugToolbarExtension
import os


login_man = LoginManager()

app = Flask(__name__)
application = app
app.secret_key = os.urandom(24)
toolbar = DebugToolbarExtension(app)


login_man.init_app(app)
login_man.login_view = 'login'
login_man.login_message = 'need authorization'
login_man.login_message_category = 'danger'


class User(UserMixin):
    def __init__(self, id, login, password):
        super().__init__()
        self.id = id
        self.login = login
        self.password = password


users_db = [{'id': '1', 'login': 'user', 'password': '0000'}]


@login_man.user_loader
def load_user(user_id):
    for user in users_db:
        if user['id'] == user_id:
            return User(**user)
    return None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_data = dict(request.form)
        if user_data['login'] and user_data['pass']:
            for user in users_db:
                if user_data['login'] == user['login'] and user_data['pass'] == user['password']:
                    user_object = User(**user)
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
