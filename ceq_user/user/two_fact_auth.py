import random
import string
import smtplib
from datetime import datetime as nowtime
import datetime
import requests
from flask import request, jsonify
from flask_restful import Resource
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ceq_user.database.models import User



# Endpoint to request OTP
class RequestOTP(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        try:
            user = User.objects.get(username=username)
        except DoesNotExist:
            return {'msg': 'User not found'}, 404
        otp_code = generate_otp()
        user.otp_code = otp_code
        user.otp_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        user.save()
        send_otp_email(user.email, otp_code)
        return {'msg': 'OTP sent to email'}, 200



# Endpoint to verify OTP
class VerifyOTP(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        otp_code = data.get('otp_code')
 
        try:
            user = User.objects.get(username=username)
        except DoesNotExist:
            return {'msg': 'User not found'}, 404
 
        if user.otp_code != otp_code or datetime.datetime.utcnow() > user.otp_expiry:
            return {'msg': 'Invalid or expired OTP code'}, 401
 
        user.otp_code = None
        user.otp_expiry = None
        user.save()
 
        return {'msg': 'OTP verified successfully'}, 200
 
 
 
def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))


 
def send_otp_email(to_email, otp_code):
    smtp_server = '10.237.234.218'
    smtp_port = 25
    from_email = 'CEQ Portal <360things@ies.etisalat.ae>'
 
    subject = 'Your OTP Code'
    body = f'Your OTP code is {otp_code}. It expires in 2 minutes.'
 
    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
 
    # Attach the OTP code to the email body
    msg.attach(MIMEText(body, 'plain'))
 
    try:
        # Establish connection to the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        # Send the email
        server.send_message(msg)
        # Close the SMTP server connection
        server.quit()
        print("OTP email sent successfully")
    except Exception as e:
        print(f"Failed to send OTP email: {str(e)}")