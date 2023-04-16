from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, TextAreaField, SubmitField, EmailField, BooleanField, \
    IntegerField, FileField
from wtforms.validators import DataRequired


class RegisterForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password_again = PasswordField('Repeat password', validators=[DataRequired()])
    nickname = StringField('Nickname', validators=[DataRequired()])
    file_pfp = FileField('profile picture (optional)')
    ignore_pfp = BooleanField('delete file (file will be deleted when submitting)')
    about = TextAreaField("tell others about yourself")
    submit = SubmitField('accept')


class EditUserForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('New password')
    password_again = PasswordField('Repeat password')
    nickname = StringField('Nickname', validators=[DataRequired()])
    file_pfp = FileField("profile picture (ignore if you don't want to change)")
    ignore_pfp = BooleanField('delete file (file will be deleted when submitting)')
    about = TextAreaField("tell others about yourself")
    submit = SubmitField('accept')


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('accept')


class NewsForm(FlaskForm):
    title = StringField('title', validators=[DataRequired()])
    about = TextAreaField('about', validators=[DataRequired()])
    file_1 = FileField('image 1 (optional)')
    file_2 = FileField('image 2 (optional)')
    file_3 = FileField('image 3 (optional)')

    file_1_ignore = BooleanField('delete file (file will be deleted when submitting)')
    file_2_ignore = BooleanField('delete file (file will be deleted when submitting)')
    file_3_ignore = BooleanField('delete file (file will be deleted when submitting)')

    tags = StringField('#tag_1 #tag_2', default='')
    submit = SubmitField('accept')


class DeleteForm(FlaskForm):
    assure = BooleanField('Are you sure?', validators=[DataRequired()])
    submit = SubmitField('accept')


class CommentForm(FlaskForm):
    text = TextAreaField('comment', validators=[DataRequired()])
    submit = SubmitField('accept')


