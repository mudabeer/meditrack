from flask import Flask,render_template,request, redirect, session,url_for, jsonify
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

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

@app.route("/editprofile")
@login_required
def editprofile():
    return render_template("editprofile.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    cursor.execute("""SELECT DISTINCT m.name as name,r.reminder_time as time,m.dose as dosage 
                   FROM medicine m JOIN reminder_logs r 
                   WHERE r.day_of_week  = substring(dayname(curdate()),1,2) AND m.user_id = %s"""
                   ,(user_id,))
    todayReminders = cursor.fetchall()

    cursor.execute("""SELECT COUNT(id) as active FROM reminder_logs WHERE medicine_id in
                        (SELECT id FROM medicine WHERE user_id = %s AND status = 'Active')"""
                        ,(user_id,))
    activeSch = cursor.fetchone()
    if not activeSch:
        activeSch = {"active":0}

    cursor.execute("SELECT count(id) as totalMedicine FROM Medicine WHERE  user_id = %s",(user_id,))
    totalMedicine = cursor.fetchone()
    if not totalMedicine:
        totalMedicine = {"totalMedicine":0}

    if not todayReminders:
        todayTotal={"todayReminders": 0}
        upcomingReminders = {"upcomingReminder":0}

        return render_template("dashboard.html",totalMedicine=totalMedicine,todayTotal=todayTotal,upcomingReminders=upcomingReminders,activeSch=activeSch,home="active")
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

        

        return render_template("dashboard.html",todayReminders=todayReminders,todayTotal=todayTotal,totalMedicine=totalMedicine,upcomingReminders=upcomingReminders,activeSch=activeSch,home="active")

@app.route("/medicine", methods=["GET","POST"])
@login_required
def medicine():
        if request.method == "POST":
            data = request.get_json()

            id = int(data["id"])
            status = data["status"]

            cursor.execute("SELECT * FROM reminders_table WHERE user_id = %s",(session["user_id"],))
            reminders = cursor.fetchall()
            reminderTime = reminders[id]["reminder_time"]
            days = reminders[id]["day_of_week"].split(",")
            values = ( session["user_id"],reminderTime,*days)
            print(values)
            if(not status):
                cursor.execute(f"""UPDATE reminder_logs 
                                set status = 'inactive' 
                               WHERE medicine_id in (
                               SELECT id FROM medicine WHERE user_id = %s)
                            AND reminder_time = %s AND day_of_week in ({','.join(['%s'] * len(days))})""",
                           values)
                
            else:
                cursor.execute(f"""UPDATE reminder_logs 
                                set status = 'active' WHERE medicine_id in 
                            (SELECT id FROM medicine WHERE user_id = %s)
                            AND reminder_time = %s AND day_of_week in ({','.join(['%s'] * len(days))})""",
                            values)
            
            conn.commit()

            return redirect("/medicine")
        else:

            now = datetime.now()
            user_id = session["user_id"]
            cursor.execute("SELECT * FROM reminders_table WHERE user_id = %s",(user_id,))
            medicines = cursor.fetchall()
            if not medicines :
                return render_template("medicine.html",medicine="active",now=now)
            else:
                numMedicine = len(medicines)
                return render_template("medicine.html",medicines=medicines,medicine="active",now=now,numMedicine=numMedicine)

@app.route("/addtime",methods=["GET","POST"])
@login_required
def addtime():
    if request.method == "POST":
        medicine_name = request.form.get("medicine_name")
        if not medicine_name:
            return render_template("addtime.html",message="invalid medicine_name",alert=True)

        hours = request.form.getlist("hour")
        mintues = request.form.getlist("mintue")
        if not hours or not mintues:
            return render_template("addtime.html",message="Invalid time",alert=True)
        times = []
        for i in range(len(hours)):
            if not hours[i]:
                return render_template("addtime.html",message="invalid hour {i}",alert=True)
            if not mintues[i]:
                return render_template("addtime.html",message="invalid mintues {i}",alert=True)
            times.append(f"{hours[i]}:{mintues[i]}:00")

        dosage = request.form.get("dosage")
        if not dosage:
            return render_template("addtime.html",message="invalid dosage",alert=True)

        days = request.form.getlist("day")
        if len(days)  < 0:
            return render_template("addtime.html",message="select at least one day",alert=True)
        
        user_id = session["user_id"]

        cursor.execute("SELECT * FROM medicine WHERE name = %s AND user_id = %s",(medicine_name,user_id))
        row = cursor.fetchall()

        if len(row) > 0:
            return render_template("addtime.html",message="medicine already exist",alert=True)
        
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
    days = ["su","mo","tu","we","th","fr","sa"]
    values = [0,0,0,0,0,0,0]
    active_per_day = [0,0,0,0,0,0,0]
    inactive_per_day = [0,0,0,0,0,0,0]
    totalAct = 0
    totalInact = 0
    medicineDistri = {}
    nameMedicineDistri = []
    totalMedicineDistri = []
    

    for i in range(len(days)):
        cursor.execute("""SELECT COUNT(medicine_id) as total FROM reminder_logs WHERE day_of_week = %s AND medicine_id in 
                       (SELECT id FROM medicine WHERE user_id = %s)""",(days[i],session["user_id"]))
        data = cursor.fetchone()
        if data:
            values[i] = data["total"]
    
        cursor.execute("""SELECT COUNT(id) as active FROM reminder_logs WHERE day_of_week = %s AND status = 'active' AND  medicine_id in
                        (SELECT id FROM medicine WHERE user_id = %s)""",(days[i],session["user_id"],))
        activeSch = cursor.fetchone()
        if activeSch:
            active_per_day[i] = activeSch["active"]

        cursor.execute("""SELECT COUNT(id) as inactive FROM reminder_logs WHERE day_of_week = %s AND status = 'inactive' AND medicine_id in
                        (SELECT id FROM medicine WHERE user_id = %s )""",(days[i],session["user_id"],))
        inactiveSch = cursor.fetchone()
        if inactiveSch:
            inactive_per_day[i] = inactiveSch["inactive"]

        cursor.execute("SELECT m.name as name, count(*) as total FROM medicine m JOIN reminder_logs r ON m.id = r.medicine_id GROUP BY m.name")
        medicineDistri = cursor.fetchall()

    for medicine in medicineDistri:
        nameMedicineDistri.append(str(medicine["name"]))
        print( medicine["name"])
        totalMedicineDistri.append(medicine["total"])
        print(medicine["total"])


    for i in range(len(active_per_day)):
        totalAct += active_per_day[i]
        totalInact += inactive_per_day[i]
        

    return render_template("analysis.html",analysis="active",values=values,days=days,active_per_day=active_per_day,inactive_per_day=inactive_per_day,totalAct=totalAct,totalInact=totalInact,nameMedicineDistri=nameMedicineDistri,totalMedicineDistri=totalMedicineDistri)

@app.route("/profile")
@login_required
def profile():
    cursor.execute("SELECT * FROM users WHERE id = %s",(session["user_id"],))
    user = cursor.fetchall()

    return render_template("profile.html",profile="active",user=user[0])

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
            session["user_id"] = user[0]["id"]
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