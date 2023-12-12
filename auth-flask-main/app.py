from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_migrate import Migrate
from flask_login import LoginManager, login_required, current_user, UserMixin
from email_validator import validate_email, EmailNotValidError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'secret_key'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))  # Добавляем поле для роли пользователя

    def __init__(self, username, password, role='user'):
        self.username = username
        self.set_password(password)
        self.role = role

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

        
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
    

class Statement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_text = db.Column(db.Text)
    date = db.Column(db.Date)
    user_username = db.Column(db.String, db.ForeignKey('user.username'))
    user = relationship('User', backref='statements')
    title_id = db.Column(db.Integer, db.ForeignKey('title.id'))
    title = relationship('Title', backref='statements')
    def __repr__(self):
        return f"<Statement {self.id}>"
    

class Title(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_name = db.Column(db.String(128))
    full_text_title = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship('User', backref='titles')
    def __repr__(self):
        return f"<Title {self.id}>"


with app.app_context():
    db.create_all()


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/admin')
def admin_page():
    user = User.query.filter_by(username=session.get('username')).first()
    if user:
        users = User.query.all()
        titles = Title.query.all()
        statements = Statement.query.all()
        return render_template('admin_page.html', statements=statements, users=users, titles=titles)
    else:
        return redirect ('/login')
    

@app.route('/admin/add_user', methods=['POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/admin')
    

@app.route('/admin/delete_user', methods=['POST'])
def delete_user():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user_to_delete = User.query.get(user_id)
        if user_to_delete:
            db.session.delete(user_to_delete)
            db.session.commit()
        return redirect('/admin')


@app.route('/admin/delete_title', methods=['POST'])
def delete_title():
    if request.method == 'POST':
        title_id = request.form['title_id']
        title_to_delete = Title.query.get(title_id)
        if title_to_delete:
            db.session.delete(title_to_delete)
            db.session.commit()
        return redirect('/admin')
    

@app.route('/admin/add_title', methods=['POST'])
def add_title():
    if request.method == 'POST':
        title_name = request.form['title_name']
        user_id = request.form['user_id']
        user = User.query.get(user_id)
        if user:
            new_title = Title(title_name=title_name, user=user)
            db.session.add(new_title)
            db.session.commit()
        return redirect('/admin')


@app.route('/admin/delete_statement', methods=['POST'])
def delete_statement():
    if request.method == 'POST':
        statement_id = request.form['statement_id']
        statement_to_delete = Statement.query.get(statement_id)
        if statement_to_delete:
            db.session.delete(statement_to_delete)
            db.session.commit()
        return redirect('/admin')

@app.route('/admin/add_statement', methods=['POST'])
def add_statement():
    if request.method == 'POST':
        name = request.form['name']
        full_text = request.form['full_text']
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        title_id = request.form['title_id']
        user_id = request.form['user_id']
        title = Title.query.get(title_id)
        user = User.query.get(user_id)
        if title and user:
            new_statement = Statement(
                name=name,
                full_text=full_text,
                date=date,
                title=title,
                user=user
            )
            db.session.add(new_statement)
            db.session.commit()
        return redirect('/admin')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get('password')
        username = request.form.get('username')
        if not username or not password:
            return render_template('register.html', error_message='Пожалуйста, заполните все поля')
        try:
            valid = validate_email(username)
            username = valid.email
        except EmailNotValidError:
            return render_template('register.html', error_message='Неверный формат email')
        new_user = User(password=password, username=username, role='user')
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = user.username
            return redirect('/account')
    return render_template('login.html', error='Invalid user')


@app.route('/account', methods=['GET', 'POST'])
def account():
    user = User.query.filter_by(username=session.get('username')).first()
    if user:
        titles = Title.query.all()  
        if request.method == 'POST':
            title_name = request.form['title_name']
            full_text_title = request.form['full_text']
            new_title = Title(title_name=title_name, full_text_title=full_text_title, user=user)  
            db.session.add(new_title)
            db.session.commit()
            titles = Title.query.all()  
        return render_template('account.html', user=user, titles=titles)  
    return redirect('/login')


@app.route('/title_statements/<int:title_id>', methods=['GET', 'POST'])
def title_statements(title_id):
    username = session.get('username')  
    title = Title.query.get(title_id)  
    if username and title:
        statements = Statement.query.filter_by(title_id=title.id).all()  
        if request.method == 'POST':
            full_text = request.form['full_text']
            # Получение текущей даты и времени
            текущая_дата = datetime.now().date()
            new_statement = Statement(
                full_text=full_text,
                date=текущая_дата,
                title_id=title.id,
                user_username=username  
            )
            db.session.add(new_statement)
            db.session.commit()
            statements = Statement.query.filter_by(title_id=title.id).all()  
        return render_template('title_statements.html', user=username, title=title, statements=statements, full_text_title=title.full_text_title)
    return redirect('/login')


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
