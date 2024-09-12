import os
import tensorflow as tf
import numpy as np
import cv2
from flask import Flask, render_template, request, Response, session, flash, jsonify, redirect, url_for
import firebase_admin
from firebase_admin import credentials, firestore
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime
from twilio.rest import Client


cred = credentials.Certificate("serviceaccountkey.json")
firebase_admin.initialize_app(cred)


db = firestore.client()

app = Flask(__name__)
app.secret_key = "123"

gmail_user = "rayhon@student.tce.edu"  
gmail_password = "#kayasamo"  

global phone

account_sid = "ACa472bb316876a31e7155af195ab0757a"
auth_token = "9859309aaa176cd20050dc25254e6bc5"
twilio_phone_number = "+13137571331"


twilio_client = Client(account_sid, auth_token)

global coordinates 

"""
def send_twilio_sms(body, to_phone_number):
      message = client.messages.create(
                body="Fire detected! Please evacuate immediately.",
                from_=twilio_phone_number,
                to="+91"+to_phone_number
            )
"""
def send_email(subject, body, mail, password, image_path):
    sender_email = f"{gmail_user}"  
    recipient_email = f"{mail}"  

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

   
    with open(image_path, 'rb') as img_file:
        image_data = img_file.read()
        image = MIMEImage(image_data, name='fire_image.jpg')
        msg.attach(image)

    
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
    #send_twilio_sms(f"Fire detected! Please evacuate immediately. {image_path}", phone)

def save_frame_as_image(frame, image_path):
    cv2.imwrite(image_path, frame)


if not os.path.exists('uploads'):
    os.makedirs('uploads')


loaded_model = tf.keras.models.load_model("fire_detector")

def preprocess_frame(frame, target_size=(196, 196)):
    # Resize the frame to the target size
    resized_frame = cv2.resize(frame, target_size)
    # Normalize the pixel values (optional)
    resized_frame = resized_frame / 255.0
    # Expand dimensions to match your model input shape
    resized_frame = np.expand_dims(resized_frame, axis=0)
    return resized_frame

def update_firebase_document(mail, new_message):
    document_ref = db.collection("users").document(mail)
    doc = document_ref.get()
    
    if doc.exists:
        user_data = doc.to_dict()
        current_messages = user_data.get('messages', [])
    else:
        current_messages = []

    current_messages.append(new_message)

    document_ref.update({'messages': current_messages, 'message_sent': True, 'timestamp': datetime.now()})

def generate_frames(ip_address, mail, password):
    video_stream_url = f"http://{ip_address}/video"
    cap = cv2.VideoCapture(video_stream_url)

    if not cap.isOpened():
        yield b'Failed to open video stream.'
    frame_count = 0
    skip_frames = 5  
    while True:
        ret, frame = cap.read()

        if not ret:
            break
        
        frame = cv2.resize(frame, (640, 480))  # Set your preferred resolution

        if frame_count % skip_frames == 0:
            img = preprocess_frame(frame)

            predictions = loaded_model.predict(img)

            threshold = 0.5  
            detected_anomaly = "Anomaly Detected" if predictions[0][0] > threshold else "No Anomaly Detected"

            if detected_anomaly == "Anomaly Detected":
                save_frame_as_image(frame, 'fire_image.jpg')

                document_ref = db.collection("messages").document(mail)

                if not document_ref.get().exists:
                    document_ref.set({'messages': []})

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                document_ref.update({
                    'messages': firestore.ArrayUnion([{
                        'subject': 'Fire Detected',
                        'body': 'Fire detected! Please evacuate immediately.{}'.format(mail),
                        'timestamp': timestamp
                    }])
                })

                send_email("Fire Detected", "Fire detected! Please evacuate immediately.", mail, password, 'fire_image.jpg')

            cv2.putText(frame, detected_anomaly, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            ret, buffer = cv2.imencode('.jpg', frame , [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        frame_count += 1


def generate_frames1(video_file_path, mail, password):
    cap = cv2.VideoCapture(video_file_path)

    if not cap.isOpened():
        yield b'Failed to open video file.'

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        img = preprocess_frame(frame)

        predictions = loaded_model.predict(img)

        threshold = 0.5  
        detected_anomaly = "Anomaly Detected" if predictions[0][0] > threshold else "No Anomaly Detected"

        if detected_anomaly == "Anomaly Detected":
            save_frame_as_image(frame, 'fire_image.jpg')

            document_ref = db.collection("messages").document(mail)

            if not document_ref.get().exists:
                document_ref.set({'messages': []})

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            document_ref.update({
                'messages': firestore.ArrayUnion([{
                    'subject': 'Fire Detected',
                    'body': 'Fire detected! Please evacuate immediately.{}'.format(mail),
                    'timestamp': timestamp
                }])
            })
            print(mail)
            send_email("Fire Detected", "Fire detected! Please evacuate immediately.", mail, password, 'fire_image.jpg')

        cv2.putText(frame, detected_anomaly, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route("/", methods=['GET', 'POST'])
def home_page():
    if request.method == 'POST':
        name = request.form.get('name')
        mail = request.form.get('mail')
        phone = request.form.get('phone')  
        password = request.form.get('password')
        user_ref = db.collection('users').document()
        user_ref.set({
            'name': name,
            'mail': mail,
            'password': password,
            'contact': phone
        })
        return render_template("login.html", name=name, phone=phone)
    else:
        return render_template("register.html")

@app.route("/login", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        mail = request.form.get('mail')
        password = request.form.get('password')
        user_ref = db.collection("users").where("mail", "==", mail).limit(1)
        users = user_ref.stream()
        for user in users:
            user_data = user.to_dict()
            password_check = user_data.get("password")
            if password == password_check:
                msg = "logged in successfully as {} and id is {}".format(mail, password)
                session['mail'] = mail
                session['password'] = password
                flash(msg, category="success")
                devices_ref = db.collection("devices").document(mail)
                devices_data = devices_ref.get().to_dict()
                print(devices_data)
                return render_template("detect.html",mail=mail,password=password,devices=devices_data)
        flash("invalid username", "danger")
        return render_template("login.html")
    else:
        return render_template("login.html")

uploads_dir = 'uploads'
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)

@app.route("/detect", methods=['POST'])
def detect():
    if 'ip_address' in request.form and 'mail' in session:
        selected_option = request.form['ip_address']

        device_name, ip_address = selected_option.split('--')

        return Response(generate_frames(ip_address, session.get('mail'), session.get('password')),
                        mimetype='multipart/x-mixed-replace; boundary=frame')


    return render_template("detect.html", text="No IP address provided")

@app.route("/detect1", methods=['POST'])
def detect1():
    if 'upload_file' in request.files and 'mail' in session:
        video_file = request.files['upload_file']
        video_file_path = os.path.join('uploads', video_file.filename)
        video_file.save(video_file_path)

        return Response(generate_frames1(video_file_path, session.get('mail'), session.get('password')),
                        mimetype='multipart/x-mixed-replace; boundary=frame')
    return render_template("detect.html", text="No Input file provided")


@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session.pop("mail", None)
    session.pop("password", None)
    return render_template("login.html")

@app.route("/notification", methods=['GET', 'POST'])
def notification():
    msg = None  
    if 'mail' in session:
        print("mail is found")
        document_ref = db.collection("messages").document(session.get('mail'))
        doc = document_ref.get()
        print("doc")
        if doc.exists:
            msg = doc.to_dict().get('messages', [])
            print("mess")
            print(msg)

    return render_template("notification.html", msg=msg if msg is not None else [])

@app.route("/locate",methods=['GET','POST'])
def map_locate():
    if 'mail' in session:
        return render_template("map.html")
    else:
        return render_template("login.html")

@app.route('/device')
def device():
    if 'mail' in  session:
        lat = request.args.get('lat')
        lng = request.args.get('lng')
        return render_template('device.html', mail=session['mail'],lat=lat, lng=lng)
    else:
        return render_template("login.html")

@app.route("/add_device", methods=['GET', 'POST'])
def add_device():
    if request.method == "POST":
        mail = request.form.get('mail')
        latitude = request.form.get('lat')
        longitude = request.form.get('lng')
        ip_address=request.form.get('ip_address')
        name=request.form.get('name')
        doc_ref = db.collection("devices").document(mail)

        if not doc_ref.get().exists:
            doc_ref.set({f"$mail": []})

        allocated_devices = doc_ref.get().to_dict().get('$mail', [])
        for device in allocated_devices:
            if device['latitude'] == latitude and device['longitude'] == longitude:
                msg = "Device already allocated at these coordinates"
                flash(msg, category="danger")
                return render_template("device.html")

        all_devices_ref = db.collection("devices")
        all_devices = all_devices_ref.stream()

        for user_device in all_devices:
            user_device_data = user_device.to_dict().get('$mail', [])
            for device in user_device_data:
                if device['latitude'] == latitude and device['longitude'] == longitude:
                    msg = "Other users are also allocated at these coordinates"
                    flash(msg, category="warning")
                    break

        doc_ref.update({
            f'$mail': firestore.ArrayUnion([{
                'latitude': latitude,
                'longitude': longitude,
                'ip_address':ip_address,
                'name':name,
                'ram': 10,
                'allocated': True  
            }])
        })
        msg = "Successfully device is allocated"
        flash(msg, category="success")
        return render_template("device.html")


if __name__ == "__main__":
    app.run(host='0.0.0.0',port=5000,debug=True)
