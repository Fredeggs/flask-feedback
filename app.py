from crypt import methods
import email
from flask import Flask, render_template, redirect, session, flash
from flask_debugtoolbar import DebugToolbarExtension
from models import Feedback, connect_db, db, User
from sqlalchemy.exc import IntegrityError
from forms import RegisterForm, LoginForm, FeedbackForm

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql:///feedback_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ECHO"] = True
app.config["SECRET_KEY"] = "abc123"
app.config["DEBUG_TB_INTERCEPT_REDIRECTS"] = False


connect_db(app)
db.create_all()

toolbar = DebugToolbarExtension(app)


@app.route("/")
def get_index():
    return redirect("/register")


@app.route("/register", methods=["GET", "POST"])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(username, password, email, first_name, last_name)

        db.session.add(new_user)
        try:
            db.session.commit()
        except IntegrityError:
            form.username.errors.append("Username taken. Please pick another")
            return render_template("register.html", form=form)
        session["username"] = new_user.username
        flash("Welcome! Successfully Created Your Account!", "success")
        return redirect(f"/users/{new_user.username}")
    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.authenticate(username, password)
        if user:
            u = User.query.get(username)
            flash(f"Welcome Back, {u.first_name}!", "primary")
            session["username"] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Invalid username/password"]

    return render_template("login.html", form=form)


@app.route("/users/<username>", methods=["GET", "POST"])
def user_page(username):
    current_user = session["username"]
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    user = User.query.get_or_404(username)
    user_feedback = Feedback.query.filter_by(username=username).all()
    return render_template("user.html", user=user, feedbacks=user_feedback)


@app.route("/users/<username>/delete", methods=["POST"])
def delete_user(username):
    current_user = session["username"]
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    if username != current_user:
        flash("You are not permitted to go there!", "danger")
        return redirect(f"/users/{current_user}")
    user = User.query.get_or_404(username)
    session.pop("username")
    db.session.delete(user)
    db.session.commit()
    flash("We are sorry to see you go!", "primary")
    return redirect("/login")


@app.route("/users/<username>/add", methods=["GET", "POST"])
def add_feedback(username):
    current_user = session["username"]
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    if username != current_user:
        flash("You are not permitted to go there!", "danger")
        return redirect(f"/users/{current_user}")
    form = FeedbackForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        new_feedback = Feedback(
            title=title, content=content, username=session["username"]
        )
        db.session.add(new_feedback)
        db.session.commit()
        flash("Feedback Created!", "success")
        return redirect(f"/users/{username}")
    return render_template("add-feedback.html", form=form)


@app.route("/feedback/<feedback_id>/update", methods=["GET", "POST"])
def edit_feedback(feedback_id):
    current_user = session["username"]
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.username != current_user:
        flash("You are not permitted to go there!", "danger")
        return redirect(f"/users/{current_user}")
    form = FeedbackForm(obj=feedback)
    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data
        db.session.add(feedback)
        db.session.commit()
        flash("Feedback Updated!", "success")
        return redirect(f"/users/{feedback.username}")
    return render_template("edit-feedback.html", form=form)


@app.route("/feedback/<feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    current_user = session["username"]
    if "username" not in session:
        flash("Please login first!", "danger")
        return redirect("/login")
    feedback = Feedback.query.get_or_404(feedback_id)
    if feedback.username != current_user:
        flash("You are not permitted to go there!", "danger")
        return redirect(f"/users/{current_user}")
    db.session.delete(feedback)
    db.session.commit()
    return redirect(f"/users/{current_user}")


@app.route("/logout")
def logout_user():
    session.pop("username")
    flash("Goodbye!", "primary")
    return redirect("/login")
