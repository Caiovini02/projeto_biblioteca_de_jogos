from flask import redirect, render_template, url_for

from projeto import app



@app.route("/")
def homepage():
    return render_template("homepage.html")
