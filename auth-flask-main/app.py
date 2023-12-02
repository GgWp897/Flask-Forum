from flask import Flask, request, render_template, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from datetime import datetime
from flask_migrate import Migrate 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self, username, password):
        self.username = username
        self.password = password

    def check_password(self, password):
        return self.password == password
    

class Statement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = relationship('User', backref='titles')

    def __repr__(self):
        return f"<Title {self.id}>"


with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username, password = request.form['username'], request.form['password']
        new_user = User(username=username, password=password)
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
            new_title = Title(title_name=title_name, user=user)  
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
            name = request.form['name']
            full_text = request.form['full_text']
            date_str = request.form['date']  
            date = datetime.strptime(date_str, '%Y-%m-%d').date()  

            new_statement = Statement(
                name=name,
                full_text=full_text,
                date=date,
                title_id=title.id,
                user_username=username  
            )

            db.session.add(new_statement)
            db.session.commit()
            statements = Statement.query.filter_by(title_id=title.id).all()  

        return render_template('title_statements.html', user=username, title=title, statements=statements)
    return redirect('/login')




@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
