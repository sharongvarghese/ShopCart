from flask import Flask,render_template,redirect,url_for,flash
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SignupForm
from models import db,User  # import db and models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize db with app
db.init_app(app)

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
        email = form.email.data
        username = form.username.data
        password = form.password.data

        existing_user = User.query.filter((User.email == email)).first()

        if existing_user:
            flash('User already exists.- please log in.', 'danger')
            # return redirect(url_for('login'))
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(email=email, username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('home'))

    return render_template('signup.html', form=form)   


app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

if __name__ == "__main__":
    app.run(debug=True)
