from flask import Flask,render_template,redirect,url_for,flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SignupForm, LoginForm
from models import db,User  # import db and models
from flask_migrate import Migrate

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with app
db.init_app(app)
migrate = Migrate(app, db)

# Create tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)   

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # At this point, email exists and password is correct
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    
    # If validation fails, the form will contain inline errors automatically
    return render_template('login.html', form=form)

if __name__ == "__main__":
    app.run(debug=True)
