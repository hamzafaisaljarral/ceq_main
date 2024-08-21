import random
import string
import smtplib
import datetime
import requests
from datetime import datetime as nowtime
from flask import request, jsonify
from flask_restful import Resource
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mongoengine.errors import DoesNotExist
from ceq_user.database.models import User
from ceq_user.resources.errors import unauthorized, not_found, ldap_issue
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from ceq_user import blacklist  # Import blacklist from __init__.py
 
class LogoutApi(Resource):
    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]  # JWT ID, a unique identifier for a token
        print("Adding jti to blacklist:", jti)
        blacklist.add(jti)
        return jsonify({'msg': 'Successfully logged out'})


class CEQLoginApi(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        # Perform the external login request
        response = requests.post('https://10.106.22.167:8400/api/auth/login', verify=False,
                                 data={"username": username, "password": password})
        if response.status_code == 500:
            return ldap_issue()
        if response.status_code == 400:
            return unauthorized()
        # Get the response data
        data = response.json()
        try:
            # Fetch the user from the local database
            user = User.objects.get(username=data.get('username'))
        except DoesNotExist:
            return not_found()
        if User.check_user_status(user.username):
            expiry = datetime.timedelta(days=1)
            payload = {
                'id': str(user.id),
                'display_name': data.get('displayName'),
                'email': data.get('email'),
                'username': str(user.username),
                'role': str(user.role)
            }
            supervisor_username = None
            if user.supervisor:
                try:
                    # Fetch the supervisor details
                    supervisor = User.objects.get(id=user.supervisor.id)
                    supervisor_username = supervisor.name
                except DoesNotExist:
                    supervisor_username = None
            # Create JWT tokens
            access_token = create_access_token(identity=payload, expires_delta=expiry)
            refresh_token = create_refresh_token(identity=str(user.id))
            # Update user's login details
            user.login_count += 1
            user.last_login = nowtime.utcnow()
            user.save()
            # Return the token and user info
            return jsonify({
                'result': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'logged_in_as': f"{user.email}",
                    'supervisor_username': supervisor_username
                }
            })
        else:
            return not_found()







class CEQLoginApi1(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        response = requests.post('https://10.106.22.167:8400/api/auth/login', verify=False,
                                 data={"username": username, "password": password})
        if response.status_code == 500:
            return {"result":"Invalid"}, 500
        if response.status_code == 400:
            return {"result":"Invalid"}, 400
        data = response.json()
        try:
            user = User.objects.get(username=data.get('username'))
        except DoesNotExist:
            return {"result":"Invalid"}, 400
        if User.check_user_status(user.username):
            otp_code = generate_otp()
            user.otp_code = otp_code
            user.otp_expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=2)
            user.save()
            send_otp_email(user.email, otp_code)
            return jsonify({"result":"Valid", "username":user.username})
        else:
            return {"result":"Invalid"}, 400
            



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
        if User.check_user_status(user.username):         
            expiry = datetime.timedelta(days=1)
            payload = {
                'id': str(user.id),
                'display_name': str(user.name),
                'email': str(user.email),
                'username': str(user.username),
                'role': str(user.role),
                'permission':str(user.permission),
            }
            supervisor_username = None
            if user.supervisor:
                try:
                    # Fetch the supervisor details
                    supervisor = User.objects.get(id=user.supervisor.id)
                    supervisor_username = supervisor.name
                except DoesNotExist:
                    supervisor_username = None
            # Create JWT tokens
            access_token = create_access_token(identity=payload, expires_delta=expiry)
            refresh_token = create_refresh_token(identity=str(user.id))
            # Update user's login details
            user.login_count += 1
            user.last_login = nowtime.utcnow()
            user.otp_code = None
            user.otp_expiry = None
            user.save()
            # Return the token and user info
            return jsonify({
                'result': {
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'username': f"{user.username}",
                    'logged_in_as': f"{user.email}",
                    'supervisor_username': supervisor_username
                }
            })
            
        else:
            return not_found()

 

 
        
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