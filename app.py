from flask import Flask, render_template, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from forms import SignupForm, LoginForm, ProductForm
from models import db, User, Product
from flask_migrate import Migrate
from flask_login import login_required
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
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
        session['user_id'] = form.user.id
        session['username'] = form.user.username
        session['is_admin'] = True if form.user.username == os.getenv('ADMIN') else False
    
        flash('Login successful!', 'success')
        return redirect(url_for('home'))
    
    return render_template('login.html', form=form)

@app.route('/admin')
def admin():
    # Check if admin is logged in
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))
    products = Product.query.all()    
    return render_template('admin.html', products=products)

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    if form.validate_on_submit():
        # category = Category.query.filter_by(name=form.category.data).first()
        # if not category:
        #     category = Category(name=form.category.data)
        #     db.session.add(category)
        #     db.session.commit()
        
        new_product = Product(
            name=form.name.data,
            price=float(form.price.data),
            description=form.description.data,
            image_url=form.image_url.data,
            category=form.category.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin'))    

    return render_template('add_product.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))



if __name__ == "__main__":
    app.run(debug=True)
