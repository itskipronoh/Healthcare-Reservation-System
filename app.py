from datetime import datetime
from flask import Flask,render_template,url_for,redirect,request,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin,login_user,LoginManager,login_required,logout_user,current_user
from sqlalchemy.sql import func
from flask_mail import Mail
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
from itsdangerous.serializer import Serializer
from sqlalchemy.orm import relationship

load_dotenv()
DB_NAME = "database.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
# Access the environment variables
mail_username = os.getenv('MAIL_USERNAME')
mail_password = os.getenv('MAIL_PASSWORD')
secret_key = os.getenv('SECRET_KEY')

app.config['SECRET_KEY'] = secret_key

# Initialize Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = mail_username
app.config['MAIL_PASSWORD'] = mail_password
app.config['MAIL_MAX_EMAILS '] = None
app.config['MAIL_SUPPRESS_SEND '] = app.testing

db = SQLAlchemy(app)
mail = Mail(app)
# Set up the application context
app.app_context().push()

# Now you can use the database within the application context
db.create_all()

ms = ['Married','Single','Divorced']
bg = ['A+','A-','B+','B-','AB+','AB-','O+','O-']

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    user = User.query.get(int(id) if id is not None else None)
    return user


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), nullable=False)
    school_id = db.Column(db.String(20),unique=True, nullable=False)
    email = db.Column(db.String(120),unique=True, nullable=False)
    user_profile = db.Column(db.String(20), nullable=False,default='default.png')
    password = db.Column(db.String(30),nullable=False)
    patient = db.relationship('Profile', backref='patient',lazy=True)
    role = db.Column(db.String(10))

    def __init__(self, school_id,username,email, password, role):
        self.school_id = school_id
        self.username = username
        self.email = email
        self.password = password
        self.role = role

    def __repr__(self):
        return f'User("{self.school_id}","{self.email}","{self.user_profile}")'
    
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date_registered = db.Column(db.DateTime(), nullable=False, default=datetime.now)
    marital_status = db.Column(db.String(120), nullable=False)
    phonenumber = db.Column(db.String(13), unique=True, nullable=False)
    address = db.Column(db.String(20), nullable=False)
    postcode = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(30), nullable=False)
    area = db.Column(db.String(20), nullable=False)
    blood_type = db.Column(db.String(5))
    country = db.Column(db.String(20), nullable=False)
    state = db.Column(db.String(20), nullable=False)
    height = db.Column(db.Integer, default=0)
    weight = db.Column(db.Integer, default=0)
    blood_type = db.Column(db.String(10))
    user = relationship("User", backref="profile", uselist=False)
    appointment_status = db.Column(db.String(15), default='booked')  # Add appointment status field
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f'Profile("{self.name}", "{self.email}", "{self.date_registered}")'        

# Initialize the URL serializer for password reset tokens using secrets

serializer = Serializer(app.config['SECRET_KEY'])


@app.route('/profile',methods=['POST','GET'])
@login_required
def profile():
    if current_user.role == 'patient':
        user = User.query.get(current_user.id)
        profile_created = user.patient
        # Check whether a Patient has created their own profile or not and redirect to appropriate page accordingly
        if request.method == 'POST':
            marital_status = request.form.get('marital_status')
            address = request.form.get('address')
            phonenumber = request.form.get('phonenumber')
            postcode = request.form.get('postcode')
            city = request.form.get('city')
            area = request.form.get('area')
            country = request.form.get('country')
            state = request.form.get('state')
            height = request.form.get('height')
            weight = request.form.get('weight')
            blood_type = request.form.get('blood_type')

            
            if marital_status not in ms:
                flash('The Marital status is invalid!', category='error')
            elif blood_type not in bg:
                flash('The Blood group is invalid!', category='error')

            else:
                new_profile = Profile(marital_status=marital_status,
                                address=address,
                                height=height,
                                phonenumber=phonenumber,
                                postcode=postcode,
                                city=city,
                                area=area,
                                country=country,
                                state=state,
                                weight=weight,
                                blood_type=blood_type,
                                patient_id = current_user.id)
                try:
                    db.session.add(new_profile)
                    db.session.commit()
                    flash('Appointment was created successfully!',category='success')
                    return redirect(url_for('home'))
                except:
                    flash('There seems to be an error booking your appointment. Please try again later',category='error')
        return render_template('profile.html',user=current_user, ms=ms, profile_created=profile_created)

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == 'POST':
        school_id = request.form.get('school_id')
        password = request.form.get('password')
        user = User.query.filter_by(school_id=school_id).first()
        if user:
            if check_password_hash(user.password,password):                
                login_user(user,remember=True)
                if current_user.role == 'doctor':
                    flash(f'Welcome back {current_user.username}!', category='success')
                    return redirect(url_for('admin'))
                flash(f'Welcome back {current_user.username}!', category='success')
                return redirect(url_for('home'))                                                 
            else:
                flash('Wrong username or password!', category='error')
        flash('The School id doesn\'t exist! Please try again', category='error')
    return render_template('login.html',user=current_user)


@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/')
@login_required
def home():
    if current_user.role == 'patient':
        user = User.query.get(current_user.id)
        appointments = user.patient
        return render_template('home.html', appointments=appointments)
    return redirect(url_for('login'))

from datetime import datetime

from datetime import datetime

@app.route('/book_appointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    if current_user.role == 'patient':
        user = User.query.get(current_user.id)
        appointments = user.patient

        # Check if the Profile table is filled (i.e., user has appointments)
        if not appointments:
            return redirect(url_for('profile'))

        if request.method == 'POST':
            appointment_id = request.form.get('appointment_id')
            selected_appointment = Profile.query.get(appointment_id)

            if selected_appointment:
                # Check if the selected appointment status is 'approved'
                if selected_appointment.appointment_status == 'approved':
                    # Update the date_registered field with the current date and time
                    selected_appointment.date_registered = datetime.utcnow()

                    # Update the status to 'booked'
                    selected_appointment.appointment_status = 'booked'

                    try:
                        db.session.commit()
                        flash('Appointment booked successfully!', category='success')
                    except:
                        flash('There was a problem booking the appointment', category='error')
                else:
                    flash('Appointment can only be booked if it is approved', category='error')
            else:
                flash('Invalid appointment ID', category='error')

        return render_template('book_appointment.html', appointments=appointments)
    return redirect(url_for('login'))





@app.route('/delete/<int:id>')
def delete(id):
    print("Received id:", id)
    appointment_to_delete = Profile.query.get_or_404(id)
    print("Appointment to delete:", appointment_to_delete)

    try:
        db.session.delete(appointment_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        flash('There was a problem deleting the appointment', category='error')

    
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        school_id = request.form.get('school_id')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.query.filter_by(email=email).first()
        s_id = User.query.filter_by(school_id=school_id).first()

        # Check if the school_id contains special letters for patients
        patient_special_letters = ['lmr', 'nrb', 'mks']
        is_patient = any(special_letter in school_id for special_letter in patient_special_letters)

        if user:
            flash('Account with this email already exists!', category='error')
        if s_id:
            flash('Account with this Username already exists!', category='error')
        if not school_id or not email or not password:
            flash('Sorry we couldn\'t sign you in!', category='error')
        elif role.lower() not in ['patient', 'doctor']:
            flash('Invalid role!', category='error')
        elif role.lower() == 'patient' and not is_patient:
            flash('Invalid school ID for patients!', category='error')
        else:
            new_user = User(email=email,
                            username=username,
                            school_id=school_id,
                            password=generate_password_hash(password, method='sha256'),
                            role=role)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            return redirect(url_for('login'))

    return render_template("signup.html", user=current_user)


@app.route('/admin')
@login_required
def admin():
    if current_user.role == 'doctor':
        appointments = Profile.query.order_by(Profile.date_registered).all()
        # Calculate the number of appointments
        num_appointments = len(appointments)
         # Calculate the count of users with each blood group
        blood_group_counts = {}
        for appointment in appointments:
            blood_group = appointment.blood_type
            if blood_group in blood_group_counts:
                blood_group_counts[blood_group] += 1
            else:
                blood_group_counts[blood_group] = 1

        return render_template('staff.html', appointments=appointments,
                               num_appointments=num_appointments,
                               blood_group_counts=blood_group_counts,
                               user=current_user)
    else:
        logout_user()
        return redirect(url_for('login'))



@app.route('/takeup/<int:id>')
@login_required
def takeup(id):
    if current_user.role == 'doctor':
        # Get the appointment details from the Profile model
        appointment = Profile.query.get_or_404(id)

        # Check if the appointment is already approved
        if appointment.appointment_status == 'booked':
            # Update the appointment status to approved (or something similar)
            appointment.appointment_status = 'approved'
            
            try:
                # Save the updated appointment status to the database
                db.session.commit()

                # Send email notification to the patient
                # send_email_to_patient(appointment.patient_email, "Appointment Approved", "Your appointment has been approved.")

                flash('Appointment approved successfully!', category='success')
            except:
                flash('There was a problem approving the appointment', category='error')
        else:
            flash('Appointment has already been approved', category='info')

        return redirect(url_for('admin'))
    else:
        return render_template('takeup.html')


@app.route('/account', methods=['GET','POST'])
@login_required
def account():
    if request.method == 'POST':
        school_id = request.form.get('school_id')
        email = request.form.get('email')

        if school_id == current_user.school_id:
            flash('School ID cannot be changed.', category='error')
        elif email != current_user.email:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                flash('If the email doesn\'t exist then It has been updated successfully.', category='warning')
            else:
                current_user.email = email
                current_user.school_id = school_id
                db.session.commit()
                flash('Account has been updated successfully.', category='success')
    return render_template('account.html', user=current_user)
    

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    email_message = None  # Initialize email_message variable
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate the password reset token
            token = serializer.dumps(user.email, salt='reset-password')
            
            # Create the password reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send the password reset email
            email_subject = 'Reset Your Password'
            email_sender = 'noreply@spudispensary.spu.ac.ke'
            email_recipients = user.email
            email_body = f"Please click the link below to reset your password: <a class='btn btn-primary' href='{reset_url}'>Reset URL</a>"
            
            email_message = {
                'subject': email_subject,
                'sender': email_sender,
                'recipients': email_recipients,
                'body': email_body
            }
            
            flash('If the email exists in our database, then password reset instructions have been sent successfully.', category='success')
        
        else:
            flash('Email doesn\'t exist in our database. You can create an account with us',category='error')
    
    return render_template('request-pass-change.html', email_message=email_message)





@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password', max_age=3600)
    except:
        flash('Invalid or expired token. Please request a new password reset.', category='error')
        return redirect(url_for('forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Email address not found.',category='error')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        # Change the user's password
        user.password = generate_password_hash(password)
        db.session.commit()
        
        # Send confirmation email
        email_subject = 'Password Reset Confirmation'
        email_sender = 'noreply@spudispensary.spu.ac.ke'
        email_recipients = user.email
        email_body = "Your password has been reset successfully."
        
        email_message = {
                'subject': email_subject,
                'sender': email_sender,
                'recipients': email_recipients,
                'body': email_body
            }
        flash('Your password has been reset successfully.', category='success')
        return render_template('change-password.html',email_message=email_message)
    
    return render_template('change-password.html')


if __name__ == '__main__':
    app.run(debug=True, port=7070)