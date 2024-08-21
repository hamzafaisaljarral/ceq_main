# -*- coding: utf-8 -*-
from ceq_user.database.models import User, NewFdh, FdhViolations, Visit
from ceq_user.resources.errors import unauthorized
from flask import request, jsonify, current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from mongoengine import DoesNotExist
from bson import ObjectId
from datetime import datetime, timedelta, time
import uuid
import json
import math
import os



class CreateFdh(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        try:
            fdh_data = request.form.to_dict()
            fdh_document = NewFdh()
            fdh_document.datetime = datetime.now()
            visited_history_data = fdh_data.get("visits", "[]")
            try:
                visited_history_list = json.loads(visited_history_data)
                visits = []
                for visit in visited_history_list:
                    images_for_visit = []
                    files = request.files.getlist(f'visit_images_{visit["visit_time"]}')
                    for file in files:
                        if file:
                            unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
                            file_path = os.path.join("/app/static/fdh/", unique_filename)
                            file.save(file_path)  # Save file to server
                            images_for_visit.append("https://ossdev.etisalat.ae:8437/static/fdh/" + unique_filename)
                    visit['images'] = images_for_visit
                    visit['visiter_name'] = user.name
                    violations_data = visit.get('violations', [])
                    visit_violations = []
                    for violation in violations_data:
                        visit_violations.append(FdhViolations(**violation))
                    visit['violations'] = visit_violations
                    visits.append(Visit(**visit))
                fdh_document.visits = visits
            except json.JSONDecodeError:
                return {"message": "Invalid JSON format for visits"}, 400
            for field, value in fdh_data.items():
                if field != 'visits':
                    setattr(fdh_document, field, value)
            fdh_document.save()
            return {'message': 'FDH record created successfully', 'fdh_id': str(fdh_document.id)}, 201
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500




class DeleteVisit(Resource):
    @jwt_required()
    def delete(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        visited_id = request.args.get("visited_id")
        if not visited_id:
            return {"message": "visited_id parameter is required"}, 400
        try:
            # Find the FDH document containing the visit with the given visited_id
            fdh_document = NewFdh.objects(visits__visited_id=visited_id).first()
            if not fdh_document:
                return {"message": "Visit not found"}
            # Remove the visit from the visits list
            fdh_document.update(pull__visits__visited_id=visited_id)
            return {"message": "Visit deleted successfully"}, 200
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500



  

class GetFdhVisits(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        fdh_id = request.args.get("fdh_id")
        if not fdh_id:
            return {"message": "fdh_id parameter is required"}, 400
        try:
            fdh_document = NewFdh.objects.get(id=fdh_id)
            visits_data = []
            for visit in fdh_document.visits:
                visit_data = {
                    "fdh_id": str(fdh_document.id),
                    "region": fdh_document.region,
                    "eid": fdh_document.eid,
                    "visit_date": visit.visit_time.isoformat(),
                    "visit_by": visit.visiter_name,
                    "visited_id":visit.visited_id
                }
                visits_data.append(visit_data)
            return {"visits": visits_data}, 200
        except DoesNotExist:
            return {"message": "FDH record not found"}, 404
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500




class GetFdhViolations(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        visited_id = request.args.get("visited_id")
        if not visited_id:
            return {"message": "visited_id parameter is required"}, 400
        try:
            # Find the visit by visited_id across all FDH documents
            fdh_document = NewFdh.objects(visits__visited_id=visited_id).first()
            if not fdh_document:
                return {"message": "Visit not found"}, 404
            visit = next((v for v in fdh_document.visits if v.visited_id == visited_id), None)
            if not visit:
                return {"message": "Visit not found"}, 404
            visit_data = {
                "visited_id":visit.visited_id,
                "violations": [
                    {
                        "category_code": v.category_code,
                        "violation_code": v.violation_code,
                        "violation_type": v.violation_type,
                        "severity": v.severity,
                        "description": v.description,
                        "remarks": v.remarks
                    } for v in visit.violations
                ],
                "images": visit.images
            }
            return {"visit": visit_data}, 200
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500

        
class FdhDetails(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if (user.role not in ["supervisor", "auditor", "admin"]) and (user.permission not in ["consumer", "all"]):
            return {"message": "Unauthorized access"}, 401
        try:            
            fdh_id = ObjectId(request.args.get('fdh_id'))
            fdh_data = NewFdh.objects(id=fdh_id).first()
            if fdh_data is None:
                return {"message": "FDH Id Not Found"}
            fdh_json = json.loads(fdh_data.to_json())                                            
            return jsonify(fdh_json)  
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving fdh'}, 500
        
        
  
       
        
                        
class FdhList(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if (user.role not in ["supervisor", "admin"]) and (user.permission not in ["consumer", "all"]):
            return {"message": "Unauthorized access"}, 401
        try:            
            query = {}
            filters = request.json
            region = filters.get("region")
            olt = filters.get("olt")
            master_eid_no = filters.get("master_eid_no")
            Type = filters.get("type")
            sub_type = filters.get("sub_type")
            fdh_no = filters.get("fdh_no")   
            page = int(filters.get('page', 1))  
            per_page = int(filters.get('per_page', 12))
            
            if region:
                query["region"] = region
            if olt:
                query["olt"] = olt
            if master_eid_no:
                query["eid"] = master_eid_no                              
            if Type:
                query["main_type"] = Type   
            if sub_type:
                query["sub_type"] = sub_type
            if fdh_no:
                query["fdh_number"] = fdh_no
            fdh_d = NewFdh.objects(__raw__=query).order_by('datetime')
            print(f"Audit Data Count: {fdh_d.count()}")
            total_records = fdh_d.count()
            total_pages = math.ceil(total_records / per_page)  
            # Apply pagination after counting total records
            fdh_data = fdh_d.skip((page - 1) * per_page).limit(per_page)
            res = []
            for fdh in fdh_data:
                fdh_json = json.loads(fdh.to_json()) 
                res.append(fdh_json)      
                
            return jsonify({
                    'audits': res,
                    'total_pages': total_pages,
                    'current_page': page,
                })                                                    
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audit'}, 500         
        
        
class DeleteFdh(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role != "audit" and (user.permission not in ["consumer", "all"]):
            return {"message": "'error': 'Unauthorized access'"}, 401       
        try:
            id = ObjectId(request.args.get('fdh_id'))
            fdh_document = NewFdh.objects(id=id).first()
            if fdh_document is None:
                return {'message': 'FDH ID Not Found'}
            if fdh_document: 
                fdh_document.delete()
                return {"message": "FDH with ID deleted successfully"}, 200
            else:
                return {"message": "FDH with ID not found"}
        except Exception as e:
            print("Exception: ", e)
            return {"message": "Error: {}".format(str(e))}, 500        
        
   
class DeleteImage(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message":"'error': 'Unauthorized access'"}, 401
        try:
            image_path = str(request.json.get('image_url'))
            fdh_id = ObjectId(request.args.get("fdh_id"))
            fdh_data = NewFdh.objects(id=fdh_id).first()
            if fdh_data is None:
                return {'message': 'fdh ID Not Found'}
            base_url = "/app/static/fdh/"
            img = image_path.replace("https://ossdev.etisalat.ae:8437/static/fdh/","")
            exact_path = base_url + img
            exist = check_file_exit(exact_path) 
            if exist:
                image_file=None
                send_image_to_server(image_file,exact_path)
                fdh_data.images.remove(image_path)
            else:    
                return {'message': 'file does not exist'}                      
            fdh_data.save()
            return {"message": "Specific image deleted and path updated for Audit with ID {}".format(fdh_id)}, 200
        except Exception as e:
            print("Exception: ", e)
            return {"message": "Error: {}".format(str(e))}, 500        


 
class UpdateFdh(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except User.DoesNotExist:
            return {"message": "Unauthorized"}, 401
 
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
 
        try:
            fdh_id = request.args.get("fdh_id")
            fdh_document = NewFdh.objects.get(id=fdh_id)
        except NewFdh.DoesNotExist:
            return {"message": "FDH record not found"}, 404
 
        try:
            fdh_data = request.form.to_dict()
 
            # Handle visit_datetime
            visit_datetime_str = fdh_data.get("visit_datetime")
            if not visit_datetime_str:
                return {"message": "visit_datetime parameter is required"}, 400
            try:
                visit_datetime = datetime.strptime(visit_datetime_str, '%d/%m/%Y, %I:%M:%S %p')
            except ValueError:
                return {"message": "Invalid date format. Expected format is 'DD/MM/YYYY, HH:MM:SS AM/PM'"}, 400
 
            # Handle violations
            violations_data = fdh_data.get("violations", "[]")
            try:
                violations_list = json.loads(violations_data)
            except json.JSONDecodeError:
                return {"message": "Invalid JSON format for violations"}, 400
 
            violations = []
            for violation in violations_list:
                try:
                    violations.append(FdhViolations(**violation))
                except TypeError as e:
                    return {"message": f"Error in violation data: {str(e)}"}, 400
 
            # Handle visit images
            images_for_visit = []
            files = request.files.getlist("images")
            for file in files:
                if file:
                    unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file.filename)
                    file_path = os.path.join("/app/static/fdh/", unique_filename)
                    file.save(file_path)
                    images_for_visit.append("https://ossdev.etisalat.ae:8437/static/fdh/" + unique_filename)
 
            # Update document fields, retaining existing data if not provided
            fields_to_update = ['fdh_health', 'fdh_number', 'eid', 'olt', 'last_uplifted_date', 'uplifting_frequency', 
                                'region', 'latitude', 'longitude', 'sub_type', 'severity', 'action_proposed', 
                                'expansion_required', 'datetime', 'network_details', 'size_score', 'inspection_date', 
                                'visit_required', 'size', 'utilization', 'network_health_index', 'health_index_slab', 
                                'faults', 'health_index', 'main_type', 'physical_health_index', 'utilization_score', 
                                'utilization_slab', 'faults_slab', 'name', 'uplift_required', 'fdh_id', 'comment']
            
            for field in fields_to_update:
                if field in fdh_data:
                    setattr(fdh_document, field, fdh_data[field])
                elif field in ["size_score","fdh_number","size_score","network_health_index",
                               "size","health_index","utilization_score"]:
                     setattr(fdh_document, field, 0)  
                else:
                    setattr(fdh_document, field, "")
                         
            setattr(fdh_document,"datetime",datetime.now())
            # Add the updated visit
            visit_data = {
                'visit_time': visit_datetime,
                'visiter_name': user.name,
                'images': images_for_visit,
                'violations': violations,
                'visited_id': str(uuid.uuid4()) + str(fdh_id)
            }
            fdh_document.visits.append(Visit(**visit_data))
 
            fdh_document.save()
 
            return {'message': 'FDH record updated successfully', 'fdh_id': str(fdh_document.id)}, 200
 
        except Exception as e:
            return {"message": f"Error: {str(e)}"}, 500


class FdhMap(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if (user.role not in ["supervisor", "admin"]) and (user.permission not in ["consumer", "all"]):
            return {"message": "Unauthorized access"}, 401
        try:            
            query = {}
            filters = request.json
            region = filters.get("region")
            olt = filters.get("olt")
            master_eid_no = filters.get("master_eid_no")
            Type = filters.get("type")
            sub_type = filters.get("sub_type")
            fdh_no = filters.get("fdh_no")   
           
            if region:
                query["region"] = region
            if olt:
                query["olt"] = olt
            if master_eid_no:
                query["eid"] = master_eid_no                              
            if Type:
                query["main_type"] = Type   
            if sub_type:
                query["sub_type"] = sub_type
            if fdh_no:
                query["fdh_number"] = fdh_no
            fdh_data = NewFdh.objects(__raw__=query).order_by('datetime')
            res = []
            for fdh in fdh_data:
                fdh_json = json.loads(fdh.to_json()) 
                res.append(fdh_json)      
                
            return res                                                 
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audit'}, 500         
        






        
def send_image_to_server(image_file, file_path):
    try:
        if image_file is None:
            print("File data is not available")
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File at {file_path} has been removed")
            else:
                print(f"No file found at {file_path} to remove")
        else:
            print("File data is available")
            print("file_path ", file_path)
            with open(file_path, 'wb') as f:
                f.write(image_file.read())
            print(f"File saved successfully at {file_path}")
        return {'message': 'Image processed successfully'}
    except Exception as e:
        return {'error': str(e)}              
    
## This Function i used to check given file path is available or not     
def check_file_exit(file_path):
    try:
        if os.path.exists(file_path):
            return True
        else:
            return False
    except Exception as e:
        return {'error': str(e)}  
    
    
    