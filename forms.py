from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed 
from models import Category



class SignupForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        from models import User
        existing_user = User.query.filter_by(email=email.data).first()
        if existing_user:
            raise ValidationError('This email is already registered. Please login.')
      
      
        
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

    def validate_email(self, email):
        from models import User
        self.user = User.query.filter_by(email=email.data).first()
        if not self.user:
            raise ValidationError('No account found with this email. Please sign up.')

    def validate_password(self, password):
        from werkzeug.security import check_password_hash
        # Use self.user from validate_email
        if self.user and not check_password_hash(self.user.password, password.data):
            raise ValidationError('Incorrect password. Please try again.')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    price = StringField('Price', validators=[DataRequired()])
    description = StringField('Description')
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Add Product')

    def validate_price(self, price):
        try:
            float(price.data)
        except ValueError:
            raise ValidationError('Please enter a valid price.')

            

