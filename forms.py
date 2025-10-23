from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import check_password_hash



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
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account found with this email. Please sign up.')

    def validate_password(self, password):
        from models import User
        user = User.query.filter_by(email=self.email.data).first()
        if user and not check_password_hash(user.password, password.data):
            raise ValidationError('Incorrect password. Please try again.')
        