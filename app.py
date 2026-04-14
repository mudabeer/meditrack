from flask import Flask,render_template,request, redirect, session,url_for, jsonify
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv
import os
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")


app = Flask(__name__)
app.secret_key = "worldDomination@12"

# Profile image upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

socketio = SocketIO(app)

scheduler = BackgroundScheduler()
atexit.register(lambda: scheduler.shutdown())

@socketio.on('connect')
def handle_connect():
    if 'user_id' in session:
        user_id = session['user_id']
        join_room(str(user_id))
    print("Client connected")

@socketio.on('toggle_status')
def handle_toggle(data):
    print("Received:", data)

    # update DB here
    id = data['id']
    status = data['status']

    # broadcast to all clients
    emit('status_updated', data, broadcast=True)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def check_reminders():
    with app.app_context():
        now = datetime.now()
        current_time = now.strftime('%H:%M:%S')
        current_day = now.strftime('%a').lower()[:2]
        
        cursor.execute("""
            SELECT r.medicine_id, m.user_id, m.name as medicine_name
            FROM reminder_logs r
            JOIN medicine m ON r.medicine_id = m.id
            WHERE r.reminder_time = %s AND r.day_of_week LIKE %s AND r.status = 'active'
        """, (current_time, f'%{current_day}%'))
        reminders = cursor.fetchall()
        
        for reminder in reminders:
            user_id = reminder['user_id']
            medicine_name = reminder['medicine_name']
            socketio.emit('reminder_notification', {'message': f'Time to take {medicine_name}!', 'medicine': medicine_name}, room=str(user_id))

# configuration
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

cursor = conn.cursor(dictionary=True, buffered=True)

days = ["su","mo","tu","we","th","fr","sa"]

scheduler.add_job(check_reminders, 'interval', minutes=1)
scheduler.start()

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/editprofile", methods=["GET", "POST"])
@login_required
def editprofile():
    if request.method == "POST":
        if 'profilePic' not in request.files:
            return render_template("editprofile.html", alert=True, message="No file part")

        file = request.files['profilePic']
        if file.filename == '':
            return render_template("editprofile.html", alert=True, message="No selected file")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # store relative path in DB for use in templates
            relative_path = os.path.join('static', 'uploads', filename)
            cursor.execute("UPDATE users SET profile_pic = %s WHERE id = %s", (relative_path, session['user_id']))
            conn.commit()

            return redirect(url_for('profile'))

        return render_template("editprofile.html", alert=True, message="Invalid file type")

    return render_template("editprofile.html")

@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    cursor.execute("""SELECT DISTINCT m.name as name, r.reminder_time as time, m.dose as dosage 
                   FROM medicine m JOIN reminder_logs r ON r.medicine_id = m.id 
                   WHERE r.day_of_week = substring(dayname(curdate()),1,2) 
                     AND m.user_id = %s 
                     AND r.status = 'active'"""
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

            reminder_id = int(data["id"])
            status = data["status"]
            new_status = 'active' if status else 'inactive'

            cursor.execute(
                """UPDATE reminder_logs
                SET status = %s
                WHERE id = %s
                  AND medicine_id IN (SELECT id FROM medicine WHERE user_id = %s)
                """,
                (new_status, reminder_id, session["user_id"])
            )
            conn.commit()

            return jsonify(success=True)
        else:

            now = datetime.now()
            user_id = session["user_id"]
            cursor.execute("""
                SELECT r.id AS reminder_id, m.id AS medicine_id, m.name, m.dose, r.reminder_time, r.day_of_week, r.status
                FROM reminder_logs r
                JOIN medicine m ON r.medicine_id = m.id
                WHERE m.user_id = %s
            """, (user_id,))
            medicines = cursor.fetchall()
            if not medicines:
                return render_template("medicine.html", medicine="active", now=now)
            else:
                numMedicine = len(medicines)
                return render_template("medicine.html", medicines=medicines, medicine="active", now=now, numMedicine=numMedicine)

@app.route("/addtime",methods=["GET","POST"])
@login_required
def addtime():
    user_id = session["user_id"]

    if request.method == "POST":
        action = request.form.get("action", "save")
        medicine_id = request.form.get("medicine_id")
        medicine_name = request.form.get("medicine_name")
        dosage = request.form.get("dosage")

        if not medicine_name:
            return render_template("addtime.html", message="invalid medicine_name", alert=True)
        if not dosage:
            return render_template("addtime.html", message="invalid dosage", alert=True)

        reminder_id = request.form.get("reminder_id")

        if action == "delete" and reminder_id:
            cursor.execute("DELETE FROM reminder_logs WHERE id = %s", (reminder_id,))
            conn.commit()
            return redirect("/medicine")

        if action == "delete" and medicine_id:
            cursor.execute("DELETE FROM reminder_logs WHERE medicine_id = %s", (medicine_id,))
            cursor.execute("DELETE FROM medicine WHERE id = %s AND user_id = %s", (medicine_id, user_id))
            conn.commit()
            return redirect("/medicine")

        if reminder_id:
            # Update the specific reminder log and its medicine metadata
            cursor.execute("UPDATE medicine SET name = %s, dose = %s WHERE id = %s AND user_id = %s", (medicine_name, dosage, medicine_id, user_id))
            cursor.execute("UPDATE reminder_logs SET reminder_time = %s, day_of_week = %s WHERE id = %s", (f"{request.form.get('hour')}:{request.form.get('mintue')}:00", ",".join(request.form.getlist('day')), reminder_id))
            conn.commit()
            return redirect("/medicine")

        if medicine_id:
            cursor.execute("UPDATE medicine SET name = %s, dose = %s WHERE id = %s AND user_id = %s", (medicine_name, dosage, medicine_id, user_id))
            conn.commit()
            return redirect("/medicine")

        hours = request.form.getlist("hour")
        mintues = request.form.getlist("mintue")
        if not hours or not mintues:
            return render_template("addtime.html", message="Invalid time", alert=True)

        times = []
        for i in range(len(hours)):
            if not hours[i] or not mintues[i]:
                return render_template("addtime.html", message=f"invalid time index {i}", alert=True)
            times.append(f"{hours[i]}:{mintues[i]}:00")

        days = request.form.getlist("day")
        if not days:
            return render_template("addtime.html", message="select at least one day", alert=True)

        cursor.execute("SELECT * FROM medicine WHERE name = %s AND user_id = %s", (medicine_name, user_id))
        row = cursor.fetchall()
        if len(row) > 0:
            return render_template("addtime.html", message="medicine already exists", alert=True)

        cursor.execute("INSERT INTO medicine (name,dose,user_id) VALUES (%s,%s,%s)", (medicine_name, dosage, user_id))
        conn.commit()
        cursor.execute("SELECT id FROM medicine WHERE name = %s AND user_id = %s", (medicine_name, user_id))
        medicine = cursor.fetchone()
        print(medicine)
        medicine_id = medicine["id"]

        for day in days:
            for time in times:
                cursor.execute("INSERT INTO reminder_logs (medicine_id,reminder_time,day_of_week) VALUES (%s,%s,%s)", (medicine_id, time, day))
        conn.commit()

        return redirect("/medicine")

    # GET
    medicine_id = request.args.get("medicine_id")
    reminder_id = request.args.get("reminder_id")
    medicine = None
    reminder_days = []
    reminder_times = []

    if reminder_id:
        cursor.execute("""
            SELECT r.id AS reminder_id, r.reminder_time, r.day_of_week, m.id AS medicine_id, m.name, m.dose
            FROM reminder_logs r
            JOIN medicine m ON r.medicine_id = m.id
            WHERE r.id = %s AND m.user_id = %s
        """, (reminder_id, user_id))
        row = cursor.fetchone()
        if row:
            medicine = {"id": row['medicine_id'], "name": row['name'], "dose": row['dose']}
            reminder_times = [str(row['reminder_time'])]
            reminder_days = row['day_of_week'].split(",") if row['day_of_week'] else []

    elif medicine_id:
        cursor.execute("SELECT id,name,dose FROM medicine WHERE id = %s AND user_id = %s", (medicine_id, user_id))
        medicine = cursor.fetchone()
        if medicine:
            cursor.execute("SELECT reminder_time, day_of_week FROM reminder_logs WHERE medicine_id = %s", (medicine_id,))
            reminders = cursor.fetchall()
            reminder_days = [r["day_of_week"] for r in reminders]
            reminder_times = [str(r["reminder_time"]) for r in reminders]

    return render_template("addtime.html", medicine=medicine, reminder_id=reminder_id, reminder_days=reminder_days, reminder_times=reminder_times)

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