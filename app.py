from flask import Flask, render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from forms import SignupForm, LoginForm, ProductForm
from models import db, User, Product, Category
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import uuid

# -------------------- LOAD ENV -------------------- #
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

# -------------------- DATABASE CONFIG -------------------- #
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# -------------------- UPLOAD CONFIG -------------------- #
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB limit
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# -------------------- INITIALIZE -------------------- #
db.init_app(app)
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()


# -------------------- HELPER: SAVE IMAGE -------------------- #
def save_image(image_file):
    """Save uploaded image and return filename."""
    if image_file:
        filename = secure_filename(image_file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        image_file.save(file_path)
        return unique_name
    return None


# -------------------- ROUTES -------------------- #

@app.route('/')
def home():
    categories = Category.query.all()
    products = Product.query.all()
    username = session.get('username', 'Guest')
    return render_template('index.html', products=products, categories=categories, username=username)


# -------------------- AUTH -------------------- #
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
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


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# -------------------- ADMIN PANEL -------------------- #
@app.route('/admin')
def admin():
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    products = Product.query.all()
    categories = Category.query.all()
    return render_template('admin.html', products=products, categories=categories)


@app.route('/add_category', methods=['GET', 'POST'])
def add_category():
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    if request.method == 'POST':
        name = request.form.get('name')
        if Category.query.filter_by(name=name).first():
            flash('Category already exists.', 'warning')
        else:
            db.session.add(Category(name=name))
            db.session.commit()
            flash('Category added successfully!', 'success')
        return redirect(url_for('add_category'))

    categories = Category.query.all()
    return render_template('add_category.html', categories=categories)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    form = ProductForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        image_file = form.image.data
        image_filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.root_path, 'static/uploads', image_filename)
        image_file.save(image_path)

        new_product = Product(
            name=form.name.data,
            price=float(form.price.data),
            description=form.description.data,
            image_filename=image_filename,
            category_id=form.category.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('admin'))

    return render_template('add_product.html', form=form)



@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]

    if form.validate_on_submit():
        product.name = form.name.data
        product.price = float(form.price.data)
        product.description = form.description.data
        product.category_id = form.category.data

        if form.image.data:
            image_filename = save_image(form.image.data)
            product.image_filename = image_filename

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin'))

    return render_template('edit_product.html', form=form, product=product)


@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if not session.get('is_admin'):
        flash('Access denied! Admins only.', 'danger')
        return redirect(url_for('home'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin'))


# -------------------- PRODUCT DISPLAY -------------------- #
@app.route('/products/<int:category_id>')
def products_by_category(category_id):
    category = Category.query.get_or_404(category_id)
    products = Product.query.filter_by(category_id=category.id).all()
    username = session.get('username', 'Guest')
    return render_template('products.html', category=category, products=products, username=username)


# -------------------- CART SYSTEM -------------------- #

# -------------------- CART SYSTEM -------------------- #

def get_cart():
    """Return the current cart from session or empty dict."""
    return session.get('cart', {})

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    cart = get_cart()

    if str(product_id) in cart:
        cart[str(product_id)]['quantity'] += 1
    else:
        cart[str(product_id)] = {
            'name': product.name,
            'price': product.price,
            'image': product.image_filename,
            'quantity': 1
        }

    session['cart'] = cart
    flash(f'Added {product.name} to cart!', 'success')
    return redirect(request.referrer or url_for('home'))


@app.route('/cart')
def cart():
    cart = get_cart()
    total = sum(item['price'] * item['quantity'] for item in cart.values())
    return render_template('cart.html', cart=cart, total=total)


@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    cart = get_cart()
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]
        session['cart'] = cart
        flash('Item removed from cart.', 'info')
    else:
        flash('Item not found in cart.', 'warning')

    return redirect(url_for('cart'))


@app.route('/update_cart/<int:product_id>', methods=['POST'])
def update_cart(product_id):
    cart = get_cart()
    product_id = str(product_id)

    if product_id in cart:
        quantity = int(request.form.get('quantity', 1))
        cart[product_id]['quantity'] = quantity if quantity > 0 else 1
        session['cart'] = cart
        flash('Cart updated successfully.', 'success')

    return redirect(url_for('cart'))



# -------------------- RUN APP -------------------- #
if __name__ == "__main__":
    app.run(debug=True)
