from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from datetime import date
from flask_gravatar import Gravatar
from functools import wraps
# from dotenv import load_dotenv
import mimetypes
import os

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

# load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("APP_SECRET_KEY_day_69")
app.config['CKEDITOR_PKG_TYPE'] = 'full-all'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("XAVIER_BLOG_URL", "sqlite:///blog.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy()
db.init_app(app)
bootstrap = Bootstrap5(app)
ckeditor = CKEditor(app)
gravatar = Gravatar(app, size=100, rating='g', default='retro', force_default=False, force_lower=False, use_ssl=False,
                    base_url=None)

# create login_manager object and initialize
login_manager = LoginManager()
login_manager.init_app(app)

# ------------------------------------ DATABASE MODELS start ------------------------------------ #


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = relationship("BlogPost", backref="users", lazy=True)
    comments = relationship("Comments", backref="users", lazy=True)


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.Integer, ForeignKey("users.id"), nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comments", backref="blog_posts", lazy=True)


class Comments(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, ForeignKey("users.id"))
    post_id = db.Column(db.Integer, ForeignKey("blog_posts.id"))

# with app.app_context():
#     db.create_all()

# ------------------------------------- DATABASE MODELS end --------------------------------------- #


# ------------------------------ DECORATORS start ------------------------------- #
# create decorator to restrict access of certain pages ONLY to the administrator user, by comparing his ID
# The user must be authenticated first in order for the decorator to work, so we need to add the @login_required
# decorator from flask-login above the @admin_only
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function
# ------------------------------ DECORATORS end --------------------------------- #


# define user_loader function
@login_manager.user_loader
def load_user(user_id):
    # find user in database by id with the User() class and call the "find_user_by_id" method, passing the "user_id" as
    # required argument, as integer (to match the database Integer id field)
    # return User().find_user_by_id(int(user_id))
    return User.query.get(int(user_id))


@app.route('/')
def get_all_posts():
    posts = db.session.execute(db.select(BlogPost)).scalars().all()
    return render_template("index.html", all_posts=posts, logged_in=current_user.is_authenticated, user=current_user)


@app.route("/post/<int:post_id>", methods=["POST", "GET"])
def show_post(post_id):
    form = CommentForm()
    requested_post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login in order to comment")
            return redirect(url_for("login"))
        comment = Comments(
            text=form.comment.data,
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(comment)
        db.session.commit()
        return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated,
                               user=current_user, form=form)
    return render_template("post.html", post=requested_post, logged_in=current_user.is_authenticated, user=current_user,
                           form=form)


@app.route("/about")
def about():
    return render_template("about.html", logged_in=current_user.is_authenticated)


@app.route("/contact")
def contact():
    return render_template("contact.html", logged_in=current_user.is_authenticated)


# WHEN USING BOOTSTRAP-FLASK (render_form) TO GET DATA WE MUST USE:  request.form["input_name"]
# request.form.get("") is only used for getting data from html forms.
@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if request.method == "POST" and form.validate_on_submit():
        # Check if the email entered in form already exists in database, if so, flash and redirect to login page
        try:
            db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one()
            flash("An account already exists with that email. Try to Login instead")
            return redirect(url_for("login"))
        except NoResultFound:
            pass
        # Create new user. Get the email, password and name filled in the html form
        # # Code below yields "unexpected argument" error (due to UserMixin), so I'll try it as the code below that
        # new_user = User(email=self.email, password=self.password, name=self.name)
        new_user = User()
        new_user.email = form.email.data
        # password is hashed here by using "generate_password_hash()"
        new_user.password = generate_password_hash(form.password.data, method="pbkdf2:sha256", salt_length=8)
        new_user.name = form.name.data
        db.session.add(new_user)
        db.session.commit()
        # locate the newly created user in the database searching by email address, using the User class, then calling
        # the find_user_by_email() method, passing the email from the form as the required argument
        try:
            new_user = db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar_one()
        except NoResultFound:
            return "Email not found"
        # pass the located new_user to the login_user in order to sign in
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if request.method == "POST" and form.validate_on_submit():
        # get the email and password from the filled html form
        email = form.email.data
        password = form.password.data
        # find user by email
        try:
            user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one()
        except NoResultFound:
            user = "Email not found"

        if user == "Email not found":
            # if user by email is not found (from variable above), flash this message and return to login page
            flash("That email does not exist")
            return redirect(url_for("login"))
        elif not check_password_hash(user.password, password):
            # if hashed password is not equal to newly hashed password entered by user, then flash msg and redirect
            flash("Password is incorrect")
            return redirect(url_for("login"))
        else:
            # if both "if" and "elif" above are false, then let the user login and redirect to secrets page
            login_user(user)
            return redirect(url_for("get_all_posts"))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    # another class imported from flask_login, to logout from the user acct.
    logout_user()
    return redirect(url_for("get_all_posts"))


@app.route("/edit_post/<int:post_id>", methods=["POST", "GET"])
@login_required
@admin_only
def edit_post(post_id):
    edit_post_true = True
    post = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        # below the author is merely populated in the html page, it will serve to other purpose, nor be updated
        # author=post.author,
        img_url=post.img_url,
        body=post.body
    )
    # ONCE THE "edit.form()" IS FILLED WITH DATA, TO RETRIEVE IT FROM THE edit_form() WE MUST USE .data AT THE END
    if request.method == "POST" and edit_form.validate_on_submit():
        post_to_update = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
        post_to_update.title = edit_form.title.data
        post_to_update.subtitle = edit_form.subtitle.data
        post_to_update.body = edit_form.body.data
        post_to_update.img_url = edit_form.img_url.data
        db.session.commit()

        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=edit_form, logged_in=current_user.is_authenticated,
                           edit_post_true=edit_post_true)


# REMEMBER THAT WHEN GETTING DATA FROM FORMS, YOU MUST DO SO BY ADDING .data IN ORDER TO OBTAIN IT
@app.route("/new-post", methods=["POST", "GET"])
@login_required
@admin_only
def make_post():
    form = CreatePostForm()
    if request.method == "POST" and form.validate_on_submit():
        new_blog = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            date=date.today().strftime("%B %d, %Y"),
            body=form.body.data,
            author=current_user.id,
            img_url=form.img_url.data
        )
        db.session.add(new_blog)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form, logged_in=current_user.is_authenticated)


@app.route("/delete/<int:post_id>")
@login_required
@admin_only
def delete_post(post_id):
    post_to_delete = db.session.execute(db.select(BlogPost).filter_by(id=post_id)).scalar_one()
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for("get_all_posts"))


if __name__ == "__main__":
    app.run()
    # app.run(debug=True)
    # app.run(host='127.0.0.1', port=5000)
