from flask_wtf import FlaskForm
import wtforms
from wtforms.validators import DataRequired, Email, EqualTo


class RegistrationForm(FlaskForm):
    first_name = wtforms.StringField("First Name", validators=[DataRequired(), ])
    last_name = wtforms.StringField("Last Name", validators=(DataRequired(), ))
    username = wtforms.StringField("Username", validators=[DataRequired(), ])
    email = wtforms.StringField("Email", validators=[DataRequired(), Email(), ])
    password = wtforms.PasswordField("Password", validators=[DataRequired(), ])
    confirm_password = wtforms.PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password"), ])
    submit = wtforms.SubmitField("Sign Up")


class LoginForm(FlaskForm):
    username = wtforms.StringField("Username", validators=[DataRequired()])
    password = wtforms.PasswordField("Password", validators=[DataRequired()])
    submit = wtforms.SubmitField("Sign In")