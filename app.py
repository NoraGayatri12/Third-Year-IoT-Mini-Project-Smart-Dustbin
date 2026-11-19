from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_mail import Mail, Message
from datetime import datetime, timedelta

# -------------------- APP CONFIG --------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'smartdustbinsecret'

# MySQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:mysqlpassword7.0.0.1/smart_dustbin'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'

# -------------------- INIT --------------------

db = SQLAlchemy(app)
mail = Mail(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -------------------- MODELS --------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), nullable=False)

class Dustbin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bin_id = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    level = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# -------------------- USER LOADER --------------------

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- EMAIL FUNCTION --------------------

def send_email(to, subject, message):
    try:
        msg = Message(subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[to])
        msg.body = message
        mail.send(msg)
    except Exception as e:
        print("Email error:", e)

# -------------------- ROUTES --------------------

@app.route('/')
def home():
    return redirect(url_for('login'))

# -------------------- SIGNUP --------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user = User(
            username=request.form['username'],
            password=request.form['password'],
            role=request.form['role'],
            email=request.form['email']
        )

        if User.query.filter_by(username=user.username).first():
            flash("User already exists")
            return redirect(url_for('signup'))

        db.session.add(user)
        db.session.commit()

        flash("Signup successful")
        return redirect(url_for('login'))

    return render_template('signup.html')

# -------------------- LOGIN --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(
            username=request.form['username'],
            password=request.form['password']
        ).first()

        if user:
            login_user(user)
            return redirect(url_for('dashboard'))

        flash("Invalid login ❌")

    return render_template('login.html')

# -------------------- LOGOUT --------------------

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# -------------------- DASHBOARD --------------------

@app.route('/dashboard')
@login_required
def dashboard():
    bins = Dustbin.query.order_by(Dustbin.timestamp.desc()).all()
    return render_template('dashboard.html', bins=bins)

# -------------------- NODEMCU API --------------------

@app.route('/update', methods=['POST'])
def update():
    data = request.get_json()

    bin_id = data.get('bin_id')
    location = data.get('location')
    level = float(data.get('level', 0))

    status = "FULL" if level >= 80 else "NORMAL"

    entry = Dustbin(
        bin_id=bin_id,
        location=location,
        level=level,
        status=status
    )

    db.session.add(entry)
    db.session.commit()

    # ---------------- ALERT ----------------

    if status == "FULL":
        cleaners = User.query.filter_by(role="CLEANER").all()

        for c in cleaners:
            send_email(
                c.email,
                "Dustbin Full Alert",
                f"Dustbin {bin_id} at {location} is 80% full."
            )

        old = Dustbin.query.filter_by(bin_id=bin_id).order_by(Dustbin.timestamp.asc()).first()

        if old and (datetime.utcnow() - old.timestamp) > timedelta(hours=2):
            hods = User.query.filter_by(role="HOD").all()

            for h in hods:
                send_email(
                    h.email,
                    "URGENT: Dustbin Not Cleaned",
                    f"Dustbin {bin_id} not cleaned for 2 hours!"
                )

    return jsonify({"message": "OK"})

# -------------------- MAIN --------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)