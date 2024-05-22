from ceq_user.database.models import User, BusinessAudit 
from ceq_user.resources.errors import unauthorized
from flask import request, jsonify, send_file
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine import DoesNotExist
from werkzeug.utils import secure_filename
from datetime import datetime
from bson import ObjectId
import pandas as pd
import paramiko
import uuid
import json
import os
import math
import csv


class CreateBusinessAudit(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and (user.permission not in ["business", "all"]):
            return {"message": "Unauthorized access"}, 401
        try:
            image_files = request.files
            audit_data = request.form
            audit_document = BusinessAudit()
            date_time = datetime.now()
            # Assign audit document fields from request data
            audit_document.ceq_auditor_name = user.username
            # Assign other fields from request data
            for key in request.form:
                setattr(audit_document, key, request.form.get(key))
            setattr(audit_document, "date_of_visit", date_time)
            # Process image files
            for image_key in image_files:
                if image_key in ["photo1", "photo2", "photo3", "photo4", "photo5", "photo6", "signature"]:
                    file_data = image_files[image_key]
                    if file_data and file_data.filename != '':
                        unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file_data.filename)
                        file_path = os.path.join("/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/", unique_filename)
                        send_image_to_server(file_data, file_path)
                        setattr(audit_document, image_key, "https://ossdev.etisalat.ae:8400/public/uploads/ceq/" + unique_filename)
            # Save the new audit document
            audit_document.save()
            return {'message': 'Audit record created successfully',
                    'audit_id':str(audit_document.id)}, 201
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500



class UploadExcelBusinessAudit(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role != "supervisor" and (user.permission not in ["business", "all"]):
            return {"message": "'error': 'Unauthorized access'"}, 401        
        try:
            excel_data = request.files['upload_excel']
            if not excel_data:
                return {'message': 'No file provided'}, 400
            try:
                df = pd.read_excel(excel_data)
            except Exception as e:
                return {'message': f'Error reading excel: {str(e)}'}, 400
            records = df.to_dict(orient='records')
            for record in records:
                # Filter out NaN values from record
                record = {k: v for k, v in record.items() if not pd.isna(v)}
                business_audit = BusinessAudit(
                    sn=record.get("SN"),
                    date_of_visit=record.get("Date of Visit "),
                    sr_dkt_no=record.get("SR DKT NO"),
                    region=record.get("REGION"),
                    sub_region=record.get('SUB REGION'),
                    product_group=record.get("PRODUCT GROUP"),
                    sr_type=record.get("SR TYPE"),
                    product_type=record.get("PRODUCT TYPE"),
                    contact_number=str(record.get("CONTACT NUMBER")),
                    ont_type=str(record.get("ONT TYPE")),
                    ont_sn=str(record.get("ONT SN")),
                    olt_code=str(record.get("OLT CODE")),
                    exch_code=record.get("EXCH-CODE"),
                    eid=record.get("EID"),
                    fdh_no=str(record.get("FDH NO")),
                    account_no=str(record.get("ACCOUNT NO")),
                    customer_name=record.get("CUSTOMER NAME"),
                    account_category=record.get("A/C_CATEGORY"),
                    sr_group=record.get("SRGroup"),
                    cbcm_close_date=record.get("CBCM_CLOSE_DATE"),
                    latitude=record.get("LATITUDE"),
                    longitude=record.get("LONGITUDE"),
                    wfm_emp_id=record.get("WFM_EMP_ID"),
                    tech_name=record.get("Tech_Name"),
                    party_id=record.get("PARTY_ID"),
                    wfm_task_id=record.get("WFM_TASK_ID"),
                    wfm_wo_number=record.get("WFM_WO_NUMBER"),
                    team_desc=record.get("TEAM_DESC"),
                    ceq_auditor_name=record.get("CEQ (Auditor Name)"),
                    observations_in_fhd_side=str(record.get("Obervations in FDH Side")),
                    violation_remarks=record.get("Violation Remarks"),
                    violation=record.get("Violation (Yes / No / NA)"),
                    photo1=record.get("PHOTO 1"),
                    photo2=record.get("PHOTO 2"),
                    photo3=record.get("PHOTO 3"),
                    photo4=record.get("PHOTO 4"),
                    photo5=record.get("PHOTO 5"),
                    ceqv01_sub_cable_inst=record.get("CEQV01 Substandard Cable handling and installation"),
                    ceqvo2_sub_inst_ont=record.get("CEQV02 Substandard Installation of ONT"),
                    ceqv03_sub_inst_wastes_left_uncleaned=record.get("CEQV03 Installation Wastes Left Uncleaned"),
                    ceqv04_existing_sub_inst_not_rectified=record.get("CEQV04 Existing Substandard Installation Not Rectified "),
                    ceqv05_sub_inst_cpe=record.get("CEQV05 Substandard Installation of CPE "),
                    ceqv06_sub_labelling=record.get("CEQV06 Substandard Labelling"),
                    sub_cable_inst=record.get("Substandard Cable handling and installation"),
                    sub_inst_ont=str(record.get("CEQV02 Substandard Installation of ONT.1")),
                    sub_inst_wastes_left_uncleaned=record.get(" Installation Wastes Left Uncleaned"),
                    existing_sub_inst_not_rectified=record.get("Existing Substandard Installation Yest Rectified Yesr Escalated to Supervisor"),
                    sub_inst_cpe=str(record.get("Substandard Installation of CPE ")),
                    sub_labelling=str(record.get("Substandard Labelling")),
                    compliance=record.get("COMPLIANCE")
                )
                print("###############")
                business_audit.save()
                print("@@@@@@@@@@@@@@")
            return {'message': 'excel data successfully processed'}, 201
        except Exception as e:  
            print(record)         
            return {"message": "Error: {}".format(str(e))}, 500
        

class BusinessAuditDetails(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if (user.role not in ["supervisor", "auditor", "admin"]) and (user.permission not in ["business", "all"]):
            return {"message": "Unauthorized access"}, 401
        try:            
            audit_id = ObjectId(request.args.get('audit_id'))
            audit_data = BusinessAudit.objects(id=audit_id).first()
            if audit_data is None:
                return {"message": "Audit Id Not Found"}, 404
            if user.role == "auditor":
                if audit_data.ceq_auditor_name != user.username:
                    return {"message": "Unauthorized access to this audit"}, 401
            audit_json = json.loads(audit_data.to_json())
            if "date_of_visit" in audit_json:
                # Convert date_of_visit from Unix timestamp to datetime string
                date_of_visit_unix = audit_json["date_of_visit"]["$date"]
                date_of_visit_str = datetime.fromtimestamp(date_of_visit_unix / 1000).strftime('%Y-%m-%d %H:%M:%S')
                audit_json["date_of_visit"] = date_of_visit_str
            return jsonify(audit_json)
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audit'}, 500
        

class GetBusinessAuditList(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and (user.permission not in ["business", "all"]):
            return {"message": "'error': 'Unauthorized access'"}, 401 
        try:      
            data = request.get_json()
            page = int(data.get('page', 1))
            per_page = int(data.get('per_page', 12))
            start_date_str = data.get('start_date')
            end_date_str = data.get('end_date')
            region = data.get('region')
            status = data.get('status')
            customer_name = data.get("customer_name")
            account_no = data.get("account_no")
            compliance = data.get("compliance")
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
            query = {}
            if start_date and end_date:
                query['date_of_visit'] = {'$gte': start_date, '$lte': end_date}
            elif start_date:
                query['date_of_visit'] = {'$gte': start_date}
            elif end_date:
                query['date_of_visit'] = {'$lte': end_date}
            if region:
                query['region'] = region
            if status:
                query["status"] = status
            if customer_name:
                query['customer_name'] = customer_name  
            if account_no:
                query['account_no'] = account_no                     
            if compliance:
                query['compliance'] = compliance 
            if user.role not in ["supervisor","admin"]:
                query["ceq_auditor_name"] = user.username
            audit_data = BusinessAudit.objects(__raw__=query).order_by('-date_of_visit')
            total_records = audit_data.count()
            total_pages = math.ceil(total_records / per_page)
            audit_data = audit_data.skip((page - 1) * per_page).limit(per_page)
            if audit_data is None:
                return {"message": "Audit's Not Found"}, 404
            respose = []                   
            if audit_data:
                audit_json = json.loads(audit_data.to_json())
                for records in audit_json:
                    if "date_of_visit" in records:
                        # Convert date_of_visit from Unix timestamp to datetime string
                        date_of_visit_unix = records["date_of_visit"]["$date"]
                        date_of_visit_str = datetime.fromtimestamp(date_of_visit_unix / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        records["date_of_visit"] = date_of_visit_str
                        respose.append(records)
                return jsonify({
                    'audits': respose,
                    'total_pages': total_pages,
                    'current_page': page,
                }) 
            else:
                return {'message': 'No audits found with provided filters'}, 404      
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audit'}, 500


class UpdateBusinessAudit(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["auditor", "supervisor", "admin"] and (user.permission not in ["business", "all"]):
            return {"message": "'error': 'Unauthorized access'"}, 401 
        try:
            image_file = request.files 
            # Retrieve audit ID from request args
            audit_id = request.args.get('audit_id')
            if audit_id is None:
                return {'message': 'Audit ID not provided'}, 400
            # Retrieve audit data by audit_id
            audit_document = BusinessAudit.objects(id=audit_id).first()
            if audit_document.ceq_auditor_name != user.username and user.role not in ["supervisor", "admin"]:
                return {"message": "'error': 'Unauthorized user'"}, 401
            if audit_document is None:
                return {'message': 'Audit ID Not Found'}, 404
            # Convert the incoming JSON data to a dictionary
            data = request.form
            # Update the fields of the existing audit_document with the new data
            if "date_of_visit" in audit_document:
                setattr(audit_document, "date_of_visit", audit_document.date_of_visit)
            for key, value in data.items():
                setattr(audit_document, key, value)
            for image_key, file_data in image_file.items():
                if image_key in ["photo1","photo2","photo3","photo4","photo5","photo6"]:
                    if file_data is None or file_data.filename == '':                       
                        setattr(audit_document, image_key, audit_document[image_key])
                    else:                        
                        if audit_document[image_key] != "":
                            print(image_key)
                            path = audit_document[image_key]
                            print(path)
                            split_path = path.split('ceq/')
                            file_name = split_path[-1]
                            exact_path= "/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/" + file_name
                            d_data = None 
                            send_image_to_server(file_data, file_path= exact_path)                                                
                        unique_filename = str(uuid.uuid4()) + '_' + secure_filename(file_data.filename)                
                        file_path = os.path.join("/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/", str(unique_filename))
                        print("file_path ",file_path)
                        send_image_to_server(file_data, file_path)
                        value = "https://ossdev.etisalat.ae:8400/public/uploads/ceq/"+str(unique_filename)
                        print("value  ")
                        setattr(audit_document, image_key, value)
            # Save the updated audit document
            setattr(audit_document, "ceq_auditor_name", audit_document.ceq_auditor_name)
            audit_document.save()
            return {'message': 'Audit record updated successfully'}, 200
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500


class DeleteBusinessAudit(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role != "audit" and (user.permission not in ["business", "all"]):
            return {"message": "'error': 'Unauthorized access'"}, 401       
        try:
            id_audit = ObjectId(request.args.get('audit_id'))
            audit_document = BusinessAudit.objects(id=id_audit).first()
            if audit_document is None:
                return {'message': 'Audit ID Not Found'}, 404
            if audit_document: 
                images = ["photo1", "photo2", "photo3", "photo4", "photo5","photo6"]  
                for img in images:                    
                    if img in audit_document and img != "":
                        path = audit_data[img]
                        split_path = path.split('ceq/')
                        file_name = split_path[-1]
                        exact_path= "/app1/DSCE/PortalGateway/estore_backend/public/uploads/ceq/" + file_name
                        file_data = None
                        send_image_to_server(file_data,file_path= exact_path)
                audit_document.delete()
                return {"message": "Audit with ID deleted successfully"}, 200
            else:
                return {"message": "Audit with ID not found"}, 404
        except Exception as e:
            print("Exception: ", e)
            return {"message": "Error: {}".format(str(e))}, 500


class BusinessAuditors(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"]:
            print(user.role)
            if user.permission not in ["business", "all"]:
                return {"message": "Unauthorized access"}, 401
        try:
            if user.permission == "all"  or "business":
                auditor_list = User.objects(permission='all', role="auditor")
            else:
                auditor_list = User.objects(permission='business', role="auditor")
            if not auditor_list:
                return {"message": "No auditor found"}, 404
            response = [json.loads(auditor.to_json()) for auditor in auditor_list]            
            return jsonify(response)  # Convert the response to JSON
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving auditor list'}, 500


class AssignAudit(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role != "supervisor" and (user.permission not in ["business", "all"]):
            return {"message": "'error': 'Unauthorized access'"}, 401
        audit_id = ObjectId(request.args.get('audit_id'))
        username = request.form.get("auditor_name")             
        try:
            update_audit = User.objects(username=username).first()
            if update_audit is None:
                return {"message": "Audit Name not found"}, 404 
            if update_audit.permission not in ["business", "all"]:
                return {"message": "'error': 'Unauthorized user'"}, 401
        except DoesNotExist:
            return {"message": "User not found"}, 404
        try:
            if update_audit:
                audit_document = BusinessAudit.objects(id=audit_id).first()
                if audit_document is None:
                    return {"message": "Audit Name not found"}, 404   
                if audit_document:
                    audit_document.update(set__ceq_auditor_name=username)
                    return {'message': 'Audit record updated successfully'}, 200  
        except Exception as e:
            return {"message": "Error: {}".format(str(e))}, 500


def send_image_to_server(image_file, file_path):
    try:
        print("image data : ", image_file)
        print("file path : ", file_path)
        # Connect to the remote server via SSH
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect('10.106.22.167', username='admin', password='zxcvbnm,./')  # Replace with actual credentials
        # Transfer the image file to the remote server
        sftp_client = ssh_client.open_sftp()
        if image_file is None:
            sftp_client.remove(file_path)  # Consider checking if file exists before removing
        else:
            # Reset file pointer to the beginning
            image_file.seek(0)
            sftp_client.putfo(image_file, file_path)  # Use putfo for file-like objects
        sftp_client.close()
        ssh_client.close()
        return {'message': 'Image uploaded successfully'}
    except Exception as e:
        print(e)
        return {'error': str(e)}


class BusinessAuditDownload(Resource):
    def get(self):
        try:
            start_date_str = request.args.get('start_date')
            end_date_str = request.args.get('end_date')
            region = request.args.get('region')
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
            query = {}
            if start_date and end_date:
                query['date_of_visit'] = {'$gte': start_date, '$lte': end_date}
            elif start_date:
                query['date_of_visit'] = {'$gte': start_date}
            elif end_date:
                query['date_of_visit'] = {'$lte': end_date}
            if region:
                query['region'] = region
            audit_data = BusinessAudit.objects(__raw__=query).order_by('-date_of_visit')
            total_records = audit_data.count()
            if audit_data is None:
                return {"message": "Audit's Not Found"}, 404
            respose = []
            if audit_data:
                audit_json = json.loads(audit_data.to_json())
                for records in audit_json:
                    if "date_of_visit" in records:
                        # Convert date_of_visit from Unix timestamp to datetime string
                        date_of_visit_unix = records["date_of_visit"]["$date"]
                        date_of_visit_str = datetime.fromtimestamp(date_of_visit_unix / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        records["date_of_visit"] = date_of_visit_str
                        del records["_id"]
                        respose.append(records)
                csv_file_path = 'exported_business_data.csv'
                with open(csv_file_path, 'w', newline='') as file:
                    fieldnames = respose[0].keys() if respose else []
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                    for row in respose:
                        writer.writerow(row)
                # Return the CSV file for download
                return send_file(csv_file_path, as_attachment=True)
            else:
                return {'message': 'No audits found with provided filters'}, 404
        except Exception as e:
            print("Exception: ", e)
            return {'message': 'Error occurred while retrieving audit'}, 500