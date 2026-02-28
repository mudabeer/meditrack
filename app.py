from flask import Flask,render_template,request, redirect

app = Flask(__name__)

# configuration


@app.route("/")
def index():
    return render_template("index.html",show_navbar=True,show_footer=True)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html",show_navbar=False,show_footer=False)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html",show_navbar=False,show_footer=False)

    
@app.route("/forgotPassword", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html",show_navbar=False,show_footer=False)

if __name__ == "__main__":
    app.run(debug=True)