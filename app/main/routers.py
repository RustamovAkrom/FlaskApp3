from flask import Blueprint, render_template


main = Blueprint("main", __name__)


@main.route("/")
@main.route("/home")
def index():
    return render_template("main/index.html")


@main.route("/about")
def about():
    return render_template("main/about.html")