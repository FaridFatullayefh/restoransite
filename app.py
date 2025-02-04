from flask import Flask, render_template, request, redirect, url_for, session,jsonify
from flask_sqlalchemy import SQLAlchemy
import random,smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
app = Flask(__name__)
app.secret_key = 'ShjGBSXJsybwFbr'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False) 
    verified = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)  

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)  

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(120), nullable=False) 

    def __repr__(self):
        return f"<Message {self.subject}>"

class Rezervasyon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    mobile = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time = db.Column(db.String(20), nullable=False)
    guest = db.Column(db.Integer, nullable=False)
    payment = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="Beklemede")  
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    
    if Admin.query.count() == 0:
        admin = Admin(username='admin', password=generate_password_hash('admin'))
        db.session.add(admin)
        db.session.commit()

def save_reservation(name, email, mobile, date, time, guest, payment):
    reservation = Rezervasyon(name=name, email=email, mobile=mobile, date=date, time=time, guest=guest, payment=payment)
    db.session.add(reservation)
    db.session.commit()
def send_verification_email(user_email, verification_code):
    sender_email = "jnhhf3008@gmail.com"
    sender_password = "dmem rleg fsoq hvuf"
    receiver_email = user_email

    subject = "Doğrulama Kodu"
    body = f"Doğrulama kodunuz: {verification_code}"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
    except Exception as e:
        print(f"Hata: {e}")

@app.route("/index")
def index():
    return render_template("index.html")
@app.route("/")
def index2():
    return render_template("index.html")

@app.route('/booking', methods=['GET', 'POST'])
def booking():
    if 'user_id' not in session:  
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id']) 

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time'] 
        guest = int(request.form['guest'])
        payment = guest * 2  

        rezervasyon = Rezervasyon(
            name=user.first_name, 
            email=user.email,      
            mobile=user.phone,      
            date=date,
            time=time,
            guest=guest,
            payment=payment,
            status="Ödeme Bekliyor" 
        )

        db.session.add(rezervasyon)
        db.session.commit()

        session['rezervasyon_id'] = rezervasyon.id  

        return redirect(url_for('payment')) 

    return render_template('booking.html', user=user) 

@app.route('/payment', methods=['GET', 'POST'])
def payment():
    rezervasyon_id = session.get('rezervasyon_id')
    if not rezervasyon_id:
        return redirect(url_for('booking')) 

    rezervasyon = Rezervasyon.query.get(rezervasyon_id)

    if request.method == 'POST':
        rezervasyon.status = "Beklemede"
        db.session.commit()

        return redirect(url_for('status'))  

    return render_template('payment.html', rezervasyon=rezervasyon, static_card="1234-5678-9876-5432")

@app.route('/status')
def status():
    rezervasyon_id = session.get('rezervasyon_id')
    if not rezervasyon_id:
        return redirect(url_for('booking'))

    rezervasyon = Rezervasyon.query.get(rezervasyon_id)

    return render_template('status.html', reservation=rezervasyon)

@app.route('/admin')
def admin():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('admin_login'))
    
    rezervasyonlar = Rezervasyon.query.filter(Rezervasyon.status.in_(['Beklemede', 'Onaylandı', 'Reddedildi'])).all()
    
    return render_template('admin.html', rezervasyonlar=rezervasyonlar)

@app.route('/admin/approve/<int:id>')
def approve(id):
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('admin_login'))
    
    rezervasyon = Rezervasyon.query.get(id)
    rezervasyon.status = "Onaylandı"
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:id>')
def reject(id):
   
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('admin_login')) 
    rezervasyon = Rezervasyon.query.get(id)
    rezervasyon.status = "Reddedildi"
    db.session.commit()
    return redirect(url_for('admin'))

@app.route("/team")
def team():
    return render_template("team.html")

@app.route("/menu")
def menu():
    return render_template("menu.html")

from werkzeug.security import generate_password_hash,check_password_hash 
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']

        hashed_password = generate_password_hash(password)

        new_user = User(first_name=first_name, last_name=last_name, phone=phone, email=email, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        verification_code = random.randint(100000, 999999)
        send_verification_email(email, verification_code)

        session['verification_code'] = verification_code
        session['email'] = email

        return redirect(url_for('verify_email'))

    return render_template('register.html')

@app.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    if request.method == 'POST':
        entered_code = request.form['verification_code']
        correct_code = session.get('verification_code')

        if entered_code == str(correct_code):
            user = User.query.filter_by(email=session['email']).first()
            if user:
                user.verified = 1  
                db.session.commit() 
                return redirect(url_for('login'))
            else:
                return "İstifadəçi Tapılmadı !", 404 
        else:
            return "Doğrulama kodu hatalı!"

    return render_template('verify_email.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:  
        return redirect(url_for('login'))

    user = User.query.filter_by(id=session['user_id']).first()

    if user:
        return render_template('profile.html', user=user)
    else:
        return "Kullanıcı bulunamadı", 404  

from werkzeug.security import check_password_hash 

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password): 
            if user.verified == 1: 
                session['user_id'] = user.id
                session['user_email'] = user.email
                return redirect(url_for('index')) 
            else:
                return "Hesabınız Təsdiqlənməyib"
        else:
            return render_template("invalid.html")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        subject = request.form['subject']
        message = request.form['message']
        
        if 'user_id' in session:  
            user = User.query.get(session['user_id']) 
            email = user.email  
        else:
            email = "Qonaq" 

        new_message = Message(subject=subject, message=message, email=email)
        db.session.add(new_message)
        db.session.commit()

        return redirect(url_for('index')) 

    return render_template('contact.html') 


from werkzeug.security import check_password_hash
@app.route('/admin-contact')
def admin_contact():
    if 'admin_logged_in' not in session or not session['admin_logged_in']:
        return redirect(url_for('admin_login')) 
        
    messages = Message.query.all()
    return render_template('admin_contact.html', messages=messages)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and check_password_hash(admin.password, password):  
            session['admin_id'] = admin.id
            session['admin_logged_in'] = True 
            return redirect(url_for('admin')) 

        else:
            return render_template("invalid_admin.html") 
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin_login'))

if __name__ == "__main__":
    app.run(debug=True)
