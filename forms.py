from flask import Flask
from flask_wtf import FlaskForm
from flask_ckeditor import CKEditor, CKEditorField
from wtforms import StringField, EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, URL, length, Email

app = Flask(__name__)
ckeditor = CKEditor(app)


# WTForm ---------- POSTS
class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    # author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")


# WTForm ---------- REGISTER
class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), length(max=100)])
    name = StringField("Name", validators=[DataRequired(), length(max=100)])
    submit = SubmitField("register")
    # Email validation required an extra install:  pip install email_validator


# WTForm ----------- LOGIN
class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), length(max=100)])
    submit = SubmitField("login")


# WTForm ----------- COMMENT
class CommentForm(FlaskForm):
    comment = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
