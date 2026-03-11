from flask import Flask,render_template,request, redirect, session,url_for
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps



app = Flask(__name__)
app.secret_key = "worldDomination@12"

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# configuration
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Mudabeer@2006",
    database="meditrack"
)

cursor = conn.cursor(dictionary=True)


@app.route("/home")
@login_required
def home():
    return render_template("home.html",show_navbar=True,show_footer=True)

@app.route("/")
def index():
    return render_template("index.html",show_navbar=True,show_footer=True)

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        userName = request.form.get("username")
        if not userName:
            return render_template("login.html",message="Invalid username",alert=True)
        
        password = request.form.get("password")
        if not password:
            return render_template("login.html",message="Invalid password",alert=True)

        cursor.execute("SELECT * FROM users WHERE user_name = %s",(userName,))
        user = cursor.fetchall()
        if len(user) != 1 or not check_password_hash(user[0]["password_hash"],password):
            return render_template("login.html",message="Invalid user or password",alert=True)
        else:
            session["user_id"] = user[0]
            return redirect("/home")
    else:
        return render_template("login.html",show_navbar=False,show_footer=False)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        firstName = request.form.get("first_name")
        if not firstName:
            return render_template("register.html",message="Invalid first name",alert=True)
        
        secondName = request.form.get("second-name")
        if not secondName:
            return render_template("register.html",message="Invalid second name",alert=True)
        full_name = firstName + " " + secondName

        user_name = request.form.get("user_name")
        if not user_name:
            return render_template("register.html",message="Invalid user name",alert=True)
        
        email = request.form.get("email")
        emailPattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not email or not re.match(emailPattern, email):
            return render_template("register.html",message="Invalid email",alert=True)

        password = request.form.get("password")
        confirmPassword = request.form.get("confirm-password")
        passwordPattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        if not password or not confirmPassword:
            return render_template("register.html",message="Invalid password",alert=True)
        elif(password != confirmPassword):
            return render_template("register.html",message="password don't match",alert=True)
        elif(not re.match(passwordPattern,password)):
            return render_template("register.html",message="weak password",alert=True)
        else:
            print("password confirmed")

        cursor.execute("SELECT * FROM users WHERE user_name = %s OR email = %s",(user_name,email))      
        user = cursor.fetchall()
        if not len(user) == 0:
            return render_template("register.html",message="username already exist",alert=True)
        
        password_hash = generate_password_hash(password)

        sql = "INSERT INTO users (email,user_name,full_name,password_hash) VALUES (%s, %s, %s, %s)"
        values = (email, user_name, full_name, password_hash)

        cursor.execute(sql, values)

        conn.commit()
        return redirect("/login")
    else:
        return render_template("register.html",show_navbar=False,show_footer=False)

    
@app.route("/forgotPassword", methods=["GET", "POST"])
def forgot_password():
    if request.method == "GET":
        return render_template("forgot_password.html",show_navbar=False,show_footer=False)

if __name__ == "__main__":
    app.run(debug=True)
