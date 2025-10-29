from flask import Flask, render_template, redirect, url_for, flash, session, request
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from forms import SignupForm, LoginForm, ProductForm, CheckoutForm
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

@app.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    
    # Check if any products exist in this category
    products_in_category = Product.query.filter_by(category_id=category_id).count()
    
    if products_in_category > 0:
        flash(f"⚠️ You can’t delete '{category.name}' because it contains {products_in_category} product(s).", "warning")
        return redirect(url_for('add_category'))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f"✅ Category '{category.name}' deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash("❌ Something went wrong while deleting the category.", "danger")
    
    return redirect(url_for('add_category'))



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



# -------------------- PRODUCT DETAIL PAGE -------------------- #
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """Display full details of a selected product."""
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id
    ).limit(4).all()
    return render_template(
        'product_detail.html',
        product=product,
        related_products=related_products
    )


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
        action = request.form.get('action')
        if action == 'increase':
            cart[product_id]['quantity'] += 1
        elif action == 'decrease' and cart[product_id]['quantity'] > 1:
            cart[product_id]['quantity'] -= 1

        session['cart'] = cart

    return redirect(url_for('cart'))

@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)
    flash('Cart cleared successfully.', 'info')
    return redirect(url_for('cart'))    



# -------------------- CHECKOUT & ORDER PROCESSING -------------------- #

from flask import render_template, redirect, url_for, session, flash, request
from models import Order, OrderItem, db
from forms import CheckoutForm

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    cart = session.get("cart", {})
    if not cart:
        flash("Your cart is empty!", "warning")
        return redirect(url_for("home"))

    form = CheckoutForm()
    total = sum(item["price"] * item["quantity"] for item in cart.values())

    if form.validate_on_submit():
        # Save Order
        order = Order(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            landmark=form.landmark.data,
            city=form.city.data,
            pincode=form.pincode.data,
            total_amount=total
        )
        db.session.add(order)
        db.session.commit()  # Save to get order.id

        # Save each cart item
        for product_id, item in cart.items():
            order_item = OrderItem(
                order_id=order.id,
                product_id=int(product_id),
                product_name=item["name"],
                quantity=item["quantity"],
                price=item["price"],
                subtotal=item["price"] * item["quantity"],
                image=item.get("image")
            )
            db.session.add(order_item)

        db.session.commit()

        # Clear cart
        session.pop("cart", None)

        flash("Order saved successfully! Redirecting to payment...", "success")
        return " Payment Section Under maintenance"

    return render_template("checkout.html", form=form, cart=cart, total=total)

@app.route("/admin/orders")
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template("admin_orders.html", orders=orders)

@app.route("/admin/update_order/<int:order_id>", methods=["POST"])
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    order.status = new_status
    db.session.commit()
    flash(f"Order #{order.id} status updated to {new_status}.", "success")
    return redirect(url_for("admin_orders"))


@app.route("/admin/delete_order/<int:order_id>", methods=["POST"])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    flash(f"Order #{order.id} deleted successfully.", "warning")
    return redirect(url_for("admin_orders"))



@app.route('/payment_page')
def payment_page():
    order_data = session.get('order_data')
    if not order_data:
        flash('No order data found. Please checkout again.', 'warning')
        return redirect(url_for('checkout'))

    return "under maintenance"

# -------------------- RUN APP -------------------- #
if __name__ == "__main__":
    app.run(debug=True)
