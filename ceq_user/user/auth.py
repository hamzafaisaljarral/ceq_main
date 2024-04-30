from datetime import datetime as nowtime
import datetime

import requests
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import create_access_token, create_refresh_token

from ceq_user.database.models import User


from ceq_user.resources.errors import unauthorized, not_found, ldap_issue


class CEQLoginApi(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        response = requests.post('https://10.106.22.167:8400/api/auth/login', verify=False,
                                 data={"username": username, "password": password})
        if response.status_code == 500:
            return ldap_issue()
        if response.status_code == 400:
            return unauthorized()
        else:
            data = response.json()
            print(data)
            print(type(data.get('username')))
            user = User.objects.get(username=data.get('username'))
            if User.check_user_status(user.username):
                expiry = datetime.timedelta(days=5)
                payload = {
                    'id': str(user.id),
                    'display_name': data.get('displayName'),
                    'email': data.get('email'),
                    'username': str(user.username),
                    'role': str(user.role)
                }
                # Return the token to the user
                access_token = create_access_token(identity=payload, expires_delta=expiry)
                refresh_token = create_refresh_token(identity=str(user.id))
                user.login_count += 1
                user.last_login = nowtime.utcnow()
                user.save()
                return jsonify({
                    'result': {'access_token': access_token,
                                           'refresh_token': refresh_token,
                                           'logged_in_as': f"{user.email}"}})
            else:
                return not_found()
