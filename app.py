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

cursor = conn.cursor(dictionary=True, buffered=True)

days = ["su","mo","tu","we","th","fr","sa"]

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]["id"]
    cursor.execute("""SELECT m.name as name,r.reminder_time as time,m.dose as dosage 
                   FROM medicine m JOIN reminder_logs r 
                   WHERE r.day_of_week  = substring(dayname(curdate()),1,2) AND m.user_id = %s"""
                   ,(user_id,))
    todayReminders = cursor.fetchall()

    cursor.execute("SELECT count(id) as totalMedicine FROM Medicine WHERE  user_id = %s",(user_id,))
    totalMedicine = cursor.fetchone()

    if not todayReminders:
        return render_template("dashboard.html",totalMedicine=totalMedicine[0])
    else:
        cursor.execute("""SELECT count(id) as upcomingReminder FROM reminder_logs WHERE medicine_id in  
                       (SELECT id FROM medicine WHERE user_id = %s) 
                       AND day_of_week = substring(dayname(curdate()),1,2) AND reminder_time > curtime();"""
                       ,(user_id,))
        upcomingReminders = cursor.fetchone()

        cursor.execute("""SELECT count(id) as todayReminders FROM reminder_logs WHERE medicine_id in 
                       (SELECT id FROM medicine WHERE user_id = %s) 
                       AND day_of_week = substring(dayname(curdate()),1,2)"""
                       ,(user_id,))
        todayTotal = cursor.fetchone()

        cursor.execute("""SELECT COUNT(id) as active FROM reminder_logs WHERE medicine_id in
                        (SELECT id FROM medicine WHERE user_id = %s AND status = 'Active')"""
                        ,(user_id,))
        activeSch = cursor.fetchone()

        return render_template("dashboard.html",todayReminders=todayReminders,todayTotal=todayTotal,totalMedicine=totalMedicine,upcomingReminders=upcomingReminders,activeSch=activeSch)

@app.route("/medicine", methods=["GET","POST"])
@login_required
def medicine():
        user_id = session["user_id"]["id"]
        cursor.execute("SELECT m.name,r.reminder_time,GROUP_CONCAT(DISTINCT r2.day_of_week ORDER BY r2.day_of_week) AS day_of_week FROM medicine m JOIN reminder_logs r on m.id = r.medicine_id JOIN reminder_logs r2 ON m.id = r2.medicine_id WHERE m.user_id = %s GROUP BY m.id,r.reminder_time ",(user_id,))
        medicines = cursor.fetchall()
        if not medicines :
            return render_template("medicine.html")
        else:
            return render_template("medicine.html",medicines=medicines)

@app.route("/addtime",methods=["GET","POST"])
@login_required
def addtime():
    if request.method == "POST":
        medicine_name = request.form.get("medicine_name")
        if not medicine_name:
            return render_template("medicine.html",message="invalid medicine_name",alert=True)

        hours = request.form.getlist("hour")
        mintues = request.form.getlist("mintue")
        times = []
        for i in range(len(hours)):
            if not hours[i]:
                return render_template("medicine.html",message="invalid hour {i}",alert=True)
            if not mintues[i]:
                return render_template("medicine.html",message="invalid mintues {i}",alert=True)
            times.append(f"{hours[i]}:{mintues[i]}:00")

        dosage = request.form.get("dosage")
        if not dosage:
            return render_template("medicine.html",message="invalid dosage",alert=True)

        days = request.form.getlist("day")
        if len(days)  < 0:
            return render_template("medicine.html",message="select at least one day",alert=True)
        
        user_id = session["user_id"]["id"]

        cursor.execute("SELECT * FROM medicine WHERE name = %s AND user_id = %s",(medicine_name,user_id))
        row = cursor.fetchall()

        if len(row) > 0:
            return render_template("medicine.html",message="medicine already exist",alert=True)
        
        qurey = "INSERT INTO medicine (name,dose,user_id) VALUES (%s,%s,%s)"
        values = (medicine_name,dosage,user_id)
        cursor.execute(qurey,values)
        conn.commit()

        cursor.execute("SELECT * FROM medicine WHERE name = %s AND user_id = %s",(medicine_name,user_id))
        medicine = cursor.fetchall()

        for day in days:
            for time in times:
                print(time,day)
                qurey = "iNSERT INTO reminder_logs (medicine_id,reminder_time,day_of_week) VALUES (%s,%s,%s)"
                values = (medicine[0]["id"],time,day)
                cursor.execute(qurey,values)
                conn.commit()
                print("succesFUll")
        return redirect("/medicine")
    else:
        return render_template("addtime.html")

@app.route("/analysis")
@login_required
def analysis():
    return render_template("analysis.html")

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/")
def index():
    session.clear()
    return render_template("index.html",show_navbar=True,show_footer=True)

@app.route("/login", methods=["GET","POST"])
def login():
    session.clear()
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
            return redirect("/dashboard")
    else:
        return render_template("login.html",show_navbar=False,show_footer=False)

@app.route("/register", methods=["GET", "POST"])
def register():
    session.clear()
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