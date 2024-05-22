# -*- coding: utf-8 -*-
from ceq_user.database.models import User, AuditData, Category, ErrorCode, Violations, Technicians
from ceq_user.resources.errors import unauthorized
from flask import request, jsonify, current_app, send_file
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from mongoengine import DoesNotExist
from mongoengine.queryset.visitor import Q
from bson import ObjectId
import json
from datetime import datetime, timedelta
import base64
import csv
import math
import os
import io
import uuid
import paramiko


# This api is used to return hello world
class Test(Resource):
    def get(self):
        return jsonify({"message": "hellow world "})


class DeleteConsumerAudit(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role != "supervisor" and user.permission not in ["consumer", "all"]:
            return {"message":"'error': 'Unauthorized access'"}, 401        
        try:
            id_audit = ObjectId(request.args.get('audit_id'))
            # Retrieve audit data by audit_id
            audit_document = AuditData.objects(id=id_audit).first()
            if audit_document is None:
                return {'message': 'Audit ID Not Found'}, 404
            if audit_document:
                audit_data = json.loads(audit_document.to_json())
                for key in ['audit_signature', 'audited_staff_signature']:
                    if key in audit_data:
                        image_file=None
                        path = audit_data[key]
                        split_path = path.split('ceq/')
                        file_name = split_path[-1]
                        exact_path= "/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/" + file_name
                        send_image_to_server(image_file, file_path= exact_path)
                if "ceqvs" in audit_data:
                    for obj in audit_data["ceqvs"]:
                        if "violations" in obj:
                            for violation in obj["violations"]:
                                if "image" in violation:
                                    image_file=None
                                    path = violation["image"]
                                    split_path = path.split('ceq/')
                                    file_name = split_path[-1]
                                    exact_path= "/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/" + file_name
                                    send_image_to_server(image_file, file_path= exact_path)
                audit_document.delete()
                return {"message": "Audit with ID deleted successfully"}, 200
            else:
                return {"message": "Audit with ID not found"}, 404
        except Exception as e:
            print("Exception: ", e)
            return {"message": "Error: {}".format(str(e))}, 500

      
class GetConsumerAudit(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        try:  
            audit_id = ObjectId(request.args.get('audit_id'))
            audit_data = AuditData.objects(id=audit_id).first()
            if audit_data is None:
                return {"message" : "Audit Id Not Found"}, 404
            audit = json.loads(audit_data.to_json())
            date_fields = ["createdDate", "expiryDate", "signature_date", "lastmodified", "auditDate"]
            for field in date_fields:
                if field in audit:
                    date_value = audit[field]
                    try:
                        if isinstance(date_value, dict) and "$date" in date_value:
                            unix_timestamp = date_value["$date"]
                            audit[field] = datetime.fromtimestamp(unix_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        elif isinstance(date_value, str):
                            try:
                                audit[field] = datetime.strptime(date_value, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                try:
                                    audit[field] = datetime.strptime(date_value, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    try:
                                        audit[field] = datetime.strptime(date_value, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S')
                                    except ValueError:
                                        pass  # Keep the original value if parsing fails
                        elif isinstance(date_value, datetime):
                            audit[field] = date_value.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        return (f"Error parsing date for field {field}: {date_value}, Error: {e}")
            return jsonify(audit)
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audit'}, 500
        
 
class GetConsumerAuditList(Resource):
    @jwt_required()    
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return {'message': 'Unauthorized'}, 401
        if user.role not in ["auditor", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {'message': 'Unauthorized access'}, 401
        try:
            data = request.get_json()
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 12))
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            region = data.get('region')
            status = data.get('status')
 
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
            query = {}
            if start_date and end_date:
                query['createdDate'] = {'$gte': start_date, '$lte': end_date}
            elif start_date:
                query['createdDate'] = {'$gte': start_date}
            elif end_date:
                query['createdDate'] = {'$lte': end_date}
            if region:
                query['region'] = region
            if status:
                query['status'] = status
            if user.role != "supervisor" and user.role != "admin":
                query["auditor_name"] = user.name
            audit_data = AuditData.objects(__raw__=query).order_by('-createdDate')
            total_records = audit_data.count()
            total_pages = math.ceil(total_records / per_page)  
            # Apply pagination after counting total records
            audit_data = audit_data.skip((page - 1) * per_page).limit(per_page)
            if audit_data:
                audit_list = []
                for audit_d in audit_data:
                    audit = json.loads(audit_d.to_json())
                    date_fields = ["createdDate", "expiryDate", "signature_date", "lastmodified", "auditDate"]
                    for field in date_fields:
                        if field in audit:
                            date_value = audit[field]
                            try:
                                if isinstance(date_value, dict) and "$date" in date_value:
                                    unix_timestamp = date_value["$date"]
                                    audit[field] = datetime.fromtimestamp(unix_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                                elif isinstance(date_value, str):
                                    try:
                                        audit[field] = datetime.strptime(date_value, '%d/%m/%Y %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                                    except ValueError:
                                        try:
                                            audit[field] = datetime.strptime(date_value, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M:%S')
                                        except ValueError:
                                            try:
                                                audit[field] = datetime.strptime(date_value, '%d/%m/%Y').strftime('%Y-%m-%d %H:%M:%S')
                                            except ValueError:
                                                pass  # Keep the original value if parsing fails
                                elif isinstance(date_value, datetime):
                                    audit[field] = date_value.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                return (f"Error parsing date for field {field}: {date_value}, Error: {e}")
                    audit_list.append(audit)
                return jsonify({
                    'audits': audit_list,
                    'total_pages': total_pages,
                    'current_page': page,
                })
            else:
                return {'message': 'No audits found with provided filters'}, 404
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audits'}, 500
        
       
class AllTeams(Resource):
    def get(self):
        try:
            teams_list = AuditData.objects().distinct("team")
            teams_list = list(teams_list)
            return {"teams": teams_list}, 200
        except DoesNotExist:
            return {"message": "No teams found"}, 404
        except Exception as e:
            return {"message": "An error occurred while retrieving teams", "error": str(e)}, 500


class CreateConsumerAudit(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401      
        try:
            if user.role == "supervisor":
                supervisor_name = user.username
            elif user.role != "supervisor":                 
                supervisor_name = user.supervisor.id if user.supervisor else None 
                if not None:
                    sup_id = ObjectId(supervisor_name)
                    user_data = User.objects(id=sup_id).first()
                    if user_data:
                        supervisor_name = user_data.name
            # Access form data
            data = request.form
            ceqs_data = data.get('ceqvs')
            form2_data = json.loads(ceqs_data)
            current_date = datetime.now()
            expiry_date = current_date + timedelta(days=3)
            audit_data = AuditData(
                auditor_name = user.name,
                supervisor_contact=data.get('supervisor_contact'),
                tech_pt=data.get('tech_pt'),
                vehicle_number=data.get('vehicle_number'),
                tech_skills=data.get('tech_skills'),
                sr_manager=data.get('sr_manager'),
                tech_fullname=data.get('tech_fullname'),
                region=data.get('region'),
                vendor=data.get('vendor'),
                director=data.get('director'),
                auditor_id=data.get('auditor_id'),
                sr_number=data.get('sr_number'),
                tech_ein=data.get('tech_ein'),
                team=data.get('team'),
                duty_manager=data.get('duty_manager'),
                supervisor=supervisor_name,
                shortdescription=data.get('shortdescription'),
                tech_contact=data.get('tech_contact'),
                controller=data.get('controller'),
                group_head=data.get('group_head'),
                user_action=data.get('user_action'),
                status=data.get('status'),
                lastmodified=datetime.now(),
                expiryDate=expiry_date,
                ceqvs=[],
                auditDate=data.get('auditDate'),
                permission=data.get('permission'),
                createdDate=current_date,
                signature_date=current_date,
                auditedDateTime=data.get('auditedDateTime'),
                name=data.get('name'),
                supervisor_id=data.get('supervisor_id'),
                superviser_comment = data.get('superviser_comment')
            )   
            image_file = request.files 
            ceqv_images = []
            ceq_obj = []
            for obj in form2_data:
                if "image" in obj:
                    ceqv_images.append(obj["image"])  
            for image_key, file_data in image_file.items():
                unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file_data.filename)                
                file_path = os.path.join("/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/", str(unique_filename))
                if file_data and file_data.filename.strip():
                    if image_key == "audited_staff_signature":
                        print("######", file_data.filename)
                        audit_data.audited_staff_signature = f"https://ossdev.etisalat.ae:8400/public/uploads/ceq/{unique_filename}"
                        send_image_to_server(file_data, file_path)
                    elif image_key == "audit_signature":
                        print("@@@@@@", file_data.filename)
                        audit_data.audit_signature = f"https://ossdev.etisalat.ae:8400/public/uploads/ceq/{unique_filename}"
                        send_image_to_server(file_data, file_path)
                if image_key in ceqv_images:
                    for obj in form2_data:
                        if "image" in obj:
                            if image_key == obj["image"]:
                                if file_data is not None:
                                    obj["image"] = "https://ossdev.etisalat.ae:8400/public/uploads/ceq/"+str(unique_filename)
                                    send_image_to_server(file_data, file_path)

            violations = [Violations(**violation) for violation in form2_data]
            audit_data.ceqvs =  violations
            audit_data.save()
            audit_id = str(audit_data.id)
            audit = "audit created" 
            return jsonify({'message': audit, "audit_id":audit_id})

        except Exception as e:
            # file.close()
            print("Exception:", e)
            return {'message': "error:{}".format(e)} , 500
        

class UpdateConsumerAudit(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        
        audit_id = ObjectId(request.args.get("audit_id"))
        audit_data = AuditData.objects(id=audit_id).first()
        image_file = request.files
        if audit_data is None:
            return {"message": "Audit not found"}, 404
        try:
            if audit_data:
                file_remove = []
                audit_json = json.loads(audit_data.to_json())
                for key in ['audit_signature', 'audited_staff_signature']:
                    if key in audit_json:
                        file_remove.append(audit_json[key])                      
                if "ceqvs" in audit_json:
                    for img in audit_json['ceqvs']:
                        if "image" in img:
                            file_remove.append(img["image"])
                file_data = None      
                print("file removel data ",file_remove)              
                data = request.form
                ceqs_data = data.get('ceqvs')
                form2_data = json.loads(ceqs_data)
                current_date = datetime.now()
                expiry_date = current_date + timedelta(days=3)
                # Update audit data
                audit_data.update(
                    set__auditor_name = audit_data.auditor_name,
                    set__supervisor_contact=data.get('supervisor_contact'),
                    set__tech_pt=data.get('tech_pt'),
                    set__vehicle_number=data.get('vehicle_number'),
                    set__tech_skills=data.get('tech_skills'),
                    set__sr_manager=data.get('sr_manager'),
                    set__tech_fullname=data.get('tech_fullname'),
                    set__region=data.get('region'),
                    set__vendor=data.get('vendor'),
                    set__director=data.get('director'),
                    set__auditor_id=data.get('auditor_id'),
                    set__sr_number=data.get('sr_number'),
                    set__tech_ein=data.get('tech_ein'),
                    set__team=data.get('team'),
                    set__duty_manager=data.get('duty_manager'),
                    set__shortdescription=data.get('shortdescription'),
                    set__tech_contact=data.get('tech_contact'),
                    set__controller=data.get('controller'),
                    set__group_head=data.get('group_head'),
                    set__user_action=data.get('user_action'),
                    set__status=data.get('status'),
                    set__lastmodified=datetime.now(),
                    set__expiryDate=expiry_date,
                    set__ceqvs=[],
                    set__auditDate=data.get('auditDate'),
                    set__permission=data.get('permission'),
                    set__createdDate=current_date,
                    set__signature_date=current_date,
                    set__auditedDateTime=data.get('auditedDateTime'),
                    set__name=data.get('name'),
                    set__supervisor_id=data.get("supervisor_id"),
                    set__superviser_comment=data.get("superviser_comment")
               )
                ceqv_images = []                    
                for obj in form2_data:
                    if "image" in obj:
                        ceqv_images.append(obj["image"])   
                        
                if "audited_staff_signature"  not in audit_json: 
                    if "audited_staff_signature"  in audit_data:
                        audit_data.audited_staff_signature = audit_json.audited_staff_signature  
                        
                if "audit_signature"  not in audit_json: 
                    if "audit_signature"  in audit_data:
                        audit_data.audit_signature = audit_json.audit_signature  
                for obj in form2_data:
                    if "category_code" in obj and "violation_code" in obj:                    
                        if "image" not in obj:
                            if "ceqvs" in audit_data:
                                for ext in audit_data["ceqvs"]:
                                    if (ext["category_code"]== obj["category_code"]) and (ext["violation_code"] == obj["violation_code"]):
                                        if "image" in ext:
                                            obj["image"] = ext["image"]                                      
                                    
                for image_key, file_data in request.files.items():
                    unique_filename = str(uuid.uuid4()) + '_' + file_data.filename
                    file_path = os.path.join("/app1/DSCE/APIGateway/ceq_files/", str(unique_filename))
                    if image_key in ['audited_staff_signature', 'audit_signature']:
                        if image_key == 'audited_staff_signature':
                            if file_data is None or file_data.filename == '':
                                if "audited_staff_signature" in audit_json:
                                    audit_data.update(set__audited_staff_signature=audit_json["audited_staff_signature"])                                    
                            else:  
                                audit_data.update(set__audited_staff_signature= "https://ossdev.etisalat.ae:8400/public/uploads/ceq/"+str(unique_filename))
                                send_image_to_server(file_data,file_path)
                        elif image_key == 'audit_signature':
                            if file_data is None or file_data.filename == '':
                                if "audit_signature" in audit_json:
                                    audit_data.update(set__audit_signature=audit_json["audit_signature"]) 
                            else:    
                                audit_data.update(set__audit_signature="https://ossdev.etisalat.ae:8400/public/uploads/ceq/"+str(unique_filename))
                                send_image_to_server(file_data,file_path)        
                    if image_key in ceqv_images:
                        for obj in form2_data:
                            if "image" in obj:
                                if image_key == obj["image"]:
                                    if file_data is None or file_data.filename == '':
                                        if "ceqvs" in audit_json:
                                            for ext in audit_json['ceqvs']:
                                                if obj["violation_code"] == ext["violation_code"]:
                                                   obj["image"] = ext["image"]                                                                                        
                                    else:            
                                        obj["image"] = "https://ossdev.etisalat.ae:8400/public/uploads/ceq/"+str(unique_filename) 
                                        send_image_to_server(file_data,file_path)         
                audit_data.ceqvs.clear()                    
                violations = [Violations(**violation) for violation in form2_data]
                audit_data.ceqvs =  violations
                # Save the updated audit data
                audit_data.save()
                return jsonify({'message': 'Audit updated successfully'})
        except Exception as e:
            print("Exception:", e)
            return {'message' : 'Error occurred while retrieving audits'}, 500

        
class DeleteConsumerImage(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message":"'error': 'Unauthorized access'"}, 401
        try:
            img = str(request.json.get('image_path'))
            image_path = "https://ossdev.etisalat.ae:8400/public/uploads/ceq/" + img
            audit_id = ObjectId(request.args.get("audit_id"))
            audit_data = AuditData.objects(id=audit_id).first()
            if audit_data is None:
                return {'message': 'Audit ID Not Found'}, 404
            image_file = None
            # Delete images and update paths for specific image paths
            exact_path = "/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/"+img
            flag = True            
            if  "audited_staff_signature" in audit_data:
                if audit_data["audited_staff_signature"] == exact_path:
                    flag = False
                    send_image_to_server(image_file,file_path= exact_path) 
                    audit_data["audited_staff_signature"] = ""                
            if  "audit_signature" in audit_data:
                if audit_data["audit_signature"] == exact_path:
                    flag = False
                    send_image_to_server(image_file,file_path= exact_path) 
                    audit_data["audit_signature"] = ""            
            if "ceqvs" in audit_data:
                for obj in audit_data["ceqvs"]:
                    if "image" in obj and obj["image"] == image_path:
                        flag = False                           
                        image_file = None
                        exact_path= "/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/" + img
                        send_image_to_server(image_file,file_path= exact_path)      
                        obj["image"] = ""
            if flag:
                exist = check_file_exit(exact_path) 
                if exist != True:
                    return {'message': 'file does not exist'}, 404                             
            # Save modified audit data
            print(audit_data)
            audit_data.save()
            return {"message": "Specific image deleted and path updated for Audit with ID {}".format(audit_id)}, 200
        except Exception as e:
            print("Exception: ", e)
            return {"message": "Error: {}".format(str(e))}, 500


class AddErrorCategory(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, required=True, help='Category name is required')
        parser.add_argument('error_codes', type=list, location='json', required=False)
        args = parser.parse_args()
        name = args.get('name')
        error_codes = args.get('error_codes')
        category = Category(name=name)
        if error_codes is not None:
            for ec in error_codes:
                error_code = ErrorCode(code=ec['code'], description=ec['description'])
                category.error_codes.append(error_code)
 
        category.save()
        return {'message': 'Category added successfully', 'category_id': str(category.id)}, 201
    
    
class GetAllCategories(Resource):
    def get(self):
        categories = Category.objects().all()
        categories_data = []
        categories_list =["Processes & Policies", "Personal Behavior",
                          "Technicians Appearance", "Field Work Standards",
                          "Vehicles", "Tools & Devices"]
        for category in categories:
            if category.name in categories_list:
                category_data = {
                    'id': str(category.id),
                    'name': category.name,
                    'error_codes': [{
                        'code': ec.code,
                        'description': ec.description
                    } for ec in category.error_codes]
                }
                categories_data.append(category_data)
 
        return {'categories': categories_data}, 200
   
   
class TechnicianDetails(Resource):
    def get(self):
        try:
            tech_pt_number = request.args.get("tech_pt")
            technician = Technicians.objects(tech_pt=tech_pt_number).first()
            if not technician:
                return {'message': 'Technician not found'}, 404
            return json.loads(technician.to_json()), 200
        except Exception as e:
            print("Failed to retrieve technician details due to:", e)
            return {'message': 'Failed to retrieve technician details'}, 500   
      
        
        
class SearchTechnicians(Resource):
    def get(self):
        try:
            search_query = request.args.get('query')
            if search_query:
                # Search for documents where any field matches the search query
                technicians = Technicians.objects.filter(
                    Q(emp_no__icontains=search_query) |
                    Q(email_user_id__icontains=search_query) |
                    Q(tech_pt__icontains=search_query) |
                    Q(section__icontains=search_query) |
                    Q(region__icontains=search_query) |
                    Q(group__icontains=search_query) |
                    Q(mobile_no__icontains=search_query) |
                    Q(designation__icontains=search_query) |
                    Q(technician_name__icontains=search_query) |
                    Q(field_supervisor_pt__icontains=search_query) |
                    Q(field_supervisor__icontains=search_query)
                )
            else:
                technicians = Technicians.objects.all()
            print(list(technicians))    
            serialized_data = [json.loads(technician.to_json()) for technician in technicians]
            return {'technicians': serialized_data}, 200
        except Exception as e:
            print("Failed to search technicians due to:", e)
            return {'message': 'Failed to search technicians'}, 500
        

class AddTechnician(Resource):
    def post(self):
        try:
            data = request.get_json()
            required_fields = ['emp_no', 'email_user_id', 'tech_pt', 'section', 'region', 'group', 'mobile_no',
                               'designation', 'technician_name', 'field_supervisor_pt', 'field_supervisor']
            if not all(field in data for field in required_fields):
                return {'message': 'Missing required fields'}, 400
            technician = Technicians(
                emp_no=str(data.get('emp_no', '')),
                email_user_id=str(data.get('email_user_id', '')),
                tech_pt=str(data.get('tech_pt', '')),
                section=str(data.get('section', '')),
                region=str(data.get('region', '')),
                group=str(data.get('group', '')),
                mobile_no=str(data.get('mobile_no', '')),
                designation=str(data.get('designation', '')),
                technician_name=str(data.get('technician_name', '')),
                field_supervisor_pt=str(data.get('field_supervisor_pt', '')),
                field_supervisor=str(data.get('field_supervisor', ''))
            )
            technician.save()
            return {'message': 'Technician added successfully'}, 201
        except Exception as e:
            print("Failed to add technician due to:", e)
            return {'message': 'Failed to add technician'}, 500


class UpdateTechnician(Resource):
    def post(self):
        try:
            # Assuming the request data is in JSON format
            data = request.get_json()
            tech_pt_number = request.args.get("pt_number")
            # Retrieve the technician to update
            technician = Technicians.objects(tech_pt=tech_pt_number).first()
            if not technician:
                return {'message': 'Technician not found'}, 404
 
            # Update the technician fields
            technician.emp_no = str(data.get('emp_no', technician.emp_no))
            technician.email_user_id = str(data.get('email_user_id', technician.email_user_id))
            technician.tech_pt = str(data.get('tech_pt', technician.tech_pt))
            technician.section = str(data.get('section', technician.section))
            technician.region = str(data.get('region', technician.region))
            technician.group = str(data.get('group', technician.group))
            technician.mobile_no = str(data.get('mobile_no', technician.mobile_no))
            technician.designation = str(data.get('designation', technician.designation))
            technician.technician_name = str(data.get('technician_name', technician.technician_name))
            technician.field_supervisor_pt = str(data.get('field_supervisor_pt', technician.field_supervisor_pt))
            technician.field_supervisor = str(data.get('field_supervisor', technician.field_supervisor))
            technician.save()
            return {'message': 'Technician updated successfully'}, 200
        except Exception as e:
            print("Failed to update technician due to:", e)
            return {'message': 'Failed to update technician'}, 500
 

class DeleteTechnician(Resource):
    def get(self):
        try:
            tech_pt_number = request.args.get("tech_pt")
            technician = Technicians.objects(tech_pt=tech_pt_number).first()
            if not technician:
                return {'message': 'Technician not found'}, 404
            technician.delete()
            return {'message': 'Technician deleted successfully'}, 200
        except Exception as e:
            print("Failed to delete technician due to:", e)
            return {'message': 'Failed to delete technician'}, 500

  



class UploadCSV(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"]:
            return {"message": "Unauthorized access"}, 401
        if 'file' not in request.files:
            return {"error": "No file uploaded"}, 400
        file = request.files.get('file')
        if not file:
            return {"error": "No file selected"}, 400
        if not file.filename.endswith('.csv'):
            return {"error": "Only CSV files are allowed"}, 400
        try:
            csv_data = file.read().decode('utf-8')
            csv_stream = io.StringIO(csv_data)
            reader = csv.DictReader(csv_stream)
            for row in reader:
                print(row)
                # sr_number = AuditData.objects(sr_number=row.get("sr_number")).first()
                # auditor_name = AuditData.objects(auditor_name=row.get("auditor_name")).first()
                # pt_number = AuditData.objects(sr_number=row.get("tech_pt")).first()
                # if sr_number:
                #     print("already exit ",sr_number)
                #     continue  # Skip record if sr_number already exists
                # if not auditor_name:
                #     print("does not exit ",auditor_name)
                #     continue  # Skip record if auditor_name does not exist
                # if pt_number:
                #     continue
                current_date = datetime.now()
                expiry_date = current_date + timedelta(days=3)
                audit_data = AuditData(
                    auditDate=row.get("auditDate"),
                    auditor_id=row.get("auditor_id"),
                    auditor_name=row.get("auditor_name"),
                    controller=row.get("controller"),
                    createdDate=row.get("auditDate"),
                    expiryDate=expiry_date,
                    director=row.get("director"),
                    duty_manager=row.get("duty_manager"),
                    group_head=row.get("group_head"),
                    region=row.get("region"),
                    shortdescription=row.get("shortdescription"),
                    sr_manager=row.get("sr_manager"),
                    sr_number=row.get("sr_number"),
                    status=row.get("status"),
                    superviser_comment=row.get("superviser_comment"),
                    supervisor=row.get("supervisor"),
                    supervisor_contact=row.get("supervisor_contact"),
                    supervisor_id=row.get("supervisor_id"),
                    team=row.get("team"),
                    tech_contact=row.get("tech_contact"),
                    tech_ein=row.get("tech_ein"),
                    tech_fullname=row.get("tech_fullname"),
                    tech_pt=row.get("tech_pt"),
                    tech_skills=row.get("tech_skills"),
                    user_action=row.get("user_action"),
                    vehicle_number=row.get("vehicle_number"),
                    vendor=row.get("vendor"),
                    ceqvs=[]
                )
                for key, value in row.items():
                    if key.startswith("ceqv_"):
                        ceqv_index = int(key.split("_")[1])
                        ceqv_field = key.split("_")[2]
                        if ceqv_field == "category":
                            ceqv_field = "category_code"
                        if len(audit_data.ceqvs) < ceqv_index:
                            audit_data.ceqvs.append({})
                        audit_data.ceqvs[ceqv_index - 1][ceqv_field] = value
                        audit_data.ceqvs[ceqv_index - 1]["violation_code"] = "CEQV{}".format(key[5:7])
                if audit_data.ceqvs:
                    violations = [Violations(**violation) for violation in audit_data.ceqvs]
                    audit_data.ceqvs = violations
                    audit_data.save()
                print("audit_data ",audit_data)
            return {"message": "CSV data processed successfully"}, 200
        except Exception as e:
            return {"error": str(e)}, 500



class ExportCSV(Resource):
    def get(self):
        try:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            region = request.args.get('region')
            check_ceq = []
            for i in range(1,60):
                d = {}
                d[f"ceqv_{i}_category_code"] = ""
                d[f"ceqv_{i}_description"] = ""
                d[f"ceqv_{i}_remarks"] = ""
                d[f"ceqv_{i}_severity"] = ""
                check_ceq.append(d)
            query = {}
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
            if start_date and end_date:
                query['createdDate'] = {'$gte': start_date, '$lte': end_date}
            elif start_date:
                query['createdDate'] = {'$gte': start_date}
            elif end_date:
                query['createdDate'] = {'$lte': end_date}
            if region:
                query['region'] = region
            audit_data = AuditData.objects(__raw__=query).order_by('-createdDate')
            csv_data = []
            if audit_data:
                for row in audit_data:
                    data = json.loads(row.to_json())
                    # Define a function to handle missing fields
                    def get_field_value(key):
                        return data.get(key, "") if data else ""
                    flattened_data = {
                        "auditDate": get_field_value("createdDate"),
                        "auditedDateTime": get_field_value("auditedDateTime"),
                        "auditor_id": get_field_value("auditor_id"),
                        "auditor_name": get_field_value("auditor_name"),
                        "controller": get_field_value("controller"),
                        "createdDate": get_field_value("createdDate"),
                        "director": get_field_value("director"),
                        "duty_manager": get_field_value("duty_manager"),
                        "group_head": get_field_value("group_head"),
                        "region": get_field_value("region"),
                        "shortdescription": get_field_value("shortdescription"),
                        "sr_manager": get_field_value("sr_manager"),
                        "sr_number": get_field_value("sr_number"),
                        "status": get_field_value("status"),
                        "superviser_comment": get_field_value("superviser_comment"),
                        "supervisor": get_field_value("supervisor"),
                        "supervisor_contact": get_field_value("supervisor_contact"),
                        "supervisor_id": get_field_value("supervisor_id"),
                        "team": get_field_value("team"),
                        "tech_contact": get_field_value("tech_contact"),
                        "tech_ein": get_field_value("tech_ein"),
                        "tech_fullname": get_field_value("tech_fullname"),
                        "tech_pt": get_field_value("tech_pt"),
                        "tech_skills": get_field_value("tech_skills"),
                        "user_action": get_field_value("user_action"),
                        "vehicle_number": get_field_value("vehicle_number"),
                        "vendor": get_field_value("vendor")
                    }

                    date_fields = ["createdDate", "expiryDate", "signature_date", "lastmodified", "auditDate"]
                    for field in date_fields:
                        if field in flattened_data:
                            if field == "auditDate" and "auditDate" in flattened_data:
                                if "$date" in flattened_data["auditDate"]:
                                    unix_timestamp = flattened_data[field]["$date"]
                                    flattened_data[field] = datetime.fromtimestamp(unix_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                            else:
                                unix_timestamp = flattened_data[field]["$date"]
                                flattened_data[field] = datetime.fromtimestamp(unix_timestamp / 1000).strftime('%Y-%m-%d %H:%M:%S')
                                flattened_data[field]

                    for i, ceqv in enumerate(data.get("ceqvs", [])):
                        flattened_data.update({
                            f"ceqv_{i+1}_category_code": ceqv.get("category_code", ""),
                            f"ceqv_{i+1}_description": ceqv.get("description", ""),
                            f"ceqv_{i+1}_remarks": ceqv.get("remarks", ""),
                            f"ceqv_{i+1}_severity": ceqv.get("severity", "")
                        })
                    for f in check_ceq:
                        for key in f.keys():
                            if key not in flattened_data:
                                flattened_data[key] = ""
                    csv_data.append(flattened_data)
            # Write the data to a CSV file
            csv_file_path = 'exported_data.csv'
            with open(csv_file_path, 'w', newline='') as file:
                fieldnames = csv_data[0].keys() if csv_data else []
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                for row in csv_data:
                    writer.writerow(row)
            # Return the CSV file for download
            return send_file(csv_file_path, as_attachment=True)
        except Exception as e:
            print(e)
            return {"error": str(e)}, 500



# Function to send image data to the other server using Paramiko
def send_image_to_server(image_file,file_path,):
    try:
        # Connect to the remote server via SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect('10.106.22.167', username='admin', password='zxcvbnm,./')  # Replace with actual credentials
        # Transfer the image file to the remote server
        sftp_client = ssh_client.open_sftp()
        if image_file == None:
           sftp_client.remove(file_path)
        else:
            sftp_client.putfo(image_file, file_path)  # Replace with the destination path on the server
        sftp_client.close()
        # Close the SSH connection
        ssh_client.close()
        return {'message': 'Image uploaded successfully'}
    except Exception as e:
        return {'error': str(e)}    

  
## This Function i used to check given file path is available or not     
def check_file_exit(file_path):
    try:
        # Connect to the remote server via SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect('10.106.22.167', username='admin', password='zxcvbnm,./')  # Replace with actual credentials
        # Check if the image exists on the server
        sftp_client = ssh_client.open_sftp()
        try:
            sftp_client.stat(file_path)
            exist = True
        except FileNotFoundError:
            exist =  False
        return exist
    except Exception as e:
        return {'error': str(e)}     

