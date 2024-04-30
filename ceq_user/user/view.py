import json

from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine.errors import DoesNotExist
from mongoengine import Q
from ceq_user.database.models import User, Technicians
from bson import ObjectId
from ceq_user.resources.errors import unauthorized, not_found
import pandas as pd


class CEQAddUserAPI(Resource):
    def post(self):
        try:
            data = request.get_json()
            role = data.get('role')
            # user_obj = ""
            # if role != 'supervisor':
            #     # Assuming Supervisor model is defined elsewhere
            #     supervisor_id = data.get('supervisor')
            #     user_obj = User.objects.get(username=supervisor_id)
            #     if user_obj.role != 'supervisor':
            #         return {'message': 'Supervisor not found'}, 404
            new_user = User(
                status=data.get('status'),
                username=data.get('username'),
                email=data.get('email'),
                role=role,
                permission=data.get('permission'),
                # supervisor=user_obj,
                name=data.get('name')
            )
            new_user.save()
            return 'User added successfully', 201
        except DoesNotExist:
            return {'message': 'Supervisor not found'}, 404
        except Exception as e:
            print(e)  # Log the error for debugging purposes
            return {'message': 'An error occurred while adding the user', 'error': str(e)}, 500


class CEQAddNewUserAPI(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return not_found()

        if user.role == "admin":
            data = request.get_json()
            new_user = User(status=data['status'], username=data['username'], email=data['email'], role=data['role'],  
                            permission = data['permission'], superviser = data["superviser"], name=data["name"])

            new_user.save()
            return 'User added successfully', 201
        else:
            return unauthorized()



class CEQUpdateUserAPI(Resource):
   
    @jwt_required()
    def post(self):
        
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return not_found()
 
        if user.role == "admin":
            try:
                id = request.json.get('id')
                obj_id = ObjectId(id)
                user_to_update = User.objects.get(id=obj_id)    
                if user_to_update is None:
                    return "user id not found", 404            
                # Retrieve supervisor if provided
                supervisor_name = request.json.get('supervisor')
                try:
                    if supervisor_name:
                        supervisor_obj = User.objects.get(username = supervisor_name)
                        if supervisor_obj["role"] != "supervisor":
                           supervisor_obj = None 
                    else: 
                        supervisor_obj = None
                except DoesNotExist:
                    return "supervisor user name not found", 404
                user_to_update.supervisor = supervisor_obj            
                user_to_update.username = request.json.get('username')
                user_to_update.email = request.json.get('email')
                user_to_update.status = request.json.get('status')
                user_to_update.role = request.json.get('role')
                user_to_update.name = request.json.get('name')
                user_to_update.permission = request.json.get('permission')
                
                user_to_update.save()
            except DoesNotExist:
                return not_found()
            return 'User updated successfully', 201
        else:
            print("error")
            return unauthorized()



class CEQViewAllUserAPI(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return not_found()

        # if user.role == "superadmin":
        users = User.objects().order_by("-id")
        users_json = json.loads(users.to_json())
        return jsonify(users_json)
        # else:
        # return unauthorized()


class CEQDeleteUserAPI(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return not_found()

        if user.role == "admin":
            try:
                User.objects(username=data['username']).delete()
            except DoesNotExist:
                return not_found()
            return 'User deleted successfully', 201
        else:
            return unauthorized()


class CEQUpdateUserStatusAPI(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return not_found()

        if user.role == "admin":
            try:
                user = User.objects.get(username=request.json.get('username'))
                user.update(status=request.json.get('status'))
            except DoesNotExist:
                return not_found()
            return 'User status updated successfully', 201
        else:
            return unauthorized()
        
class SearchUsers(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return not_found()
        except Exception as e:
            return {"message": "An error occurred while fetching user information", "error": str(e)}, 500
        query = request.args.get('q') 
        search_query = (Q(username__icontains=query) |
                        Q(email__icontains=query) |
                        Q(name__icontains=query)|
                        Q(role__icontains=query)|
                        Q(status__icontains=query)|
                        Q(permission__icontains=query))
                
        try:
            users = User.objects(search_query).order_by("-id")
            users_json = json.loads(users.to_json())
            return jsonify(users_json)
        except Exception as e:
            return {"message": "An error occurred while searching for users", "error": str(e)}, 5000        

class TechnicianFileUpload(Resource):
    def post(self):
        if 'file' not in request.files:
            return {'message': 'No file part'}, 400
        file = request.files['file']
        if not file.filename.endswith(('.xls', '.xlsx')):
            return {'message': 'Unsupported file format'}, 400
        df = pd.read_excel(file)

        for _, row in df.iterrows():
            try:
                # Convert potentially non-string fields to strings explicitly
                technician = Technicians(
                    emp_no=str(row.get('Emp No.', '')),  # default '' if not present
                    email_user_id=str(row.get('Tech Mail/User ID', '')),
                    tech_pt=str(row.get('Tech PT', '')),
                    section=str(row.get('Section', '')),
                    region=str(row.get('Region', '')),
                    group=str(row.get('Group', '')),
                    mobile_no=str(row.get('Mobile No.', '')),  # Ensuring this is always a string
                    designation=str(row.get('Designation (Prestige/Consumer)', '')),
                    technician_name=str(row.get('Technician Name', '')),
                    field_supervisor_pt=str(row.get('Field Supervisor PT', '')),
                    field_supervisor=str(row.get('Field Supervisor', ''))
                )
                technician.save()
            except Exception as e:
                print("Failed to save a technician due to:", e)
                return {'message': f'Error processing file: {str(e)}'}, 500

        return {'message': 'File processed and saved successfully'}, 200