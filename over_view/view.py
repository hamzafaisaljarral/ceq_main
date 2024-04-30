# -*- coding: utf-8 -*-
from ceq_user.database.models import User, AuditData, Violations,BusinessAudit
from ceq_user.resources.errors import unauthorized
from flask import request, jsonify, current_app
from flask_restful import Resource, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from mongoengine import DoesNotExist
from bson import ObjectId
import json
from datetime import datetime, timedelta, time


class OverViewReport(Resource):
    @jwt_required()    
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return {'message': 'Unauthorized'}, 401
 
        data = request.get_json()
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        region = data.get('region')
        status = data.get('status')
        module = data.get('module')  # use get_json() instead of request.form
 
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None
 
        # Compose a readable date range string for output
        date_range = f"{start_date_str} to {end_date_str}" if start_date_str and end_date_str else "Not specified"
 
        dict_data = {
            "module": module,
            "date_range": date_range,
            "pending_audits": 0,
            "approved_audits": 0,
            "Rejected_audits": 0,
            "total_audits": 0
        } 
        query = {} 
        if module == "consumer":
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
            if user.role not in ["audit", "supervisor", "admin"] and user.permission not in ["consumer", "all"]:
                return {"message": "Unauthorized access"}, 401 
            audit_data = AuditData.objects(__raw__=query).order_by('-createdDate')
            if audit_data:
                for status_type in ["Pending", "Approved", "Rejected"]:
                    dict_data[f"{status_type.lower()}_audits"] = sum(
                        1 for audit in audit_data
                        if audit.status == status_type and (audit.auditor_name == user.name or user.role == "supervisor")
                    )
 
                total_audits = len(audit_data)
                dict_data["total_audits"] = total_audits
        if module == "Business":            
            customer_name = data.get("customer_name")
            account_no = data.get("account_no")
            compliance = data.get("compliance")
            if start_date and end_date:
                query['date_of_visit'] = {'$gte': start_date, '$lte': end_date}
            elif start_date:
                query['date_of_visit'] = {'$gte': start_date}
            elif end_date:
                query['date_of_visit'] = {'$lte': end_date}
            if region:
                query['region'] = region
            if user.role not in ["audit", "supervisor", "admin"] and user.permission not in ["business", "all"]:
                return {"message": "Unauthorized access"}, 401 
            audit_data = BusinessAudit.objects(__raw__=query).order_by('-date_of_visit')
            if audit_data:
                for status_type in ["Pending", "Approved", "Rejected"]:
                    dict_data[f"{status_type.lower()}_audits"] = sum(
                        1 for audit in audit_data
                        if audit.status == status_type and (audit.auditor_name == user.name or user.role == "supervisor")
                    )
                total_audits = len(audit_data)
            dict_data["total_audits"] = total_audits
        return jsonify(dict_data)          





class AuditDashboardMonth(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized() 
        current_date = datetime.now().date()
        current_date = datetime.combine(current_date, time.min)
        print(current_date,"date now")
        module = request.json.get("module")
        region = request.json.get("region")
        # Calculate the start date for six months ago
        month_ago = current_date - timedelta(days=30)
        month_ago = datetime.combine(month_ago, time.min)
        month_data = {}
        start_date = month_ago.strftime("%Y-%m-%d")
        end_date= current_date.strftime("%Y-%m-%d")
        start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None
        date_range = f"{start_date} to {end_date}" if start_date and end_date else "Not specified"
        month_data["date_range"] = date_range
        # Iterate over each month within the last six months
        query = {}
        if module == "consumer":
            if region:
                query['region'] = region
            query['createdDate'] = {'$gte': month_ago,'$lte': current_date}
            audit_data = AuditData.objects(__raw__=query).order_by('-createdDate')
            if audit_data:
                for status_type in ["Pending", "Approved", "Rejected"]:
                    month_data[f"{status_type.lower()}_audits"] = sum(
                         1 for audit in audit_data
                        if audit.status == status_type and (audit.auditor_name == user.name or user.role == "supervisor")
                    )
                total_audits = len(audit_data)
                if total_audits > 0:
                    month_data["pending_percentage"] = "{:.1f}%".format((month_data["pending_audits"] / total_audits) * 100)
                    month_data["approved_percentage"] = "{:.1f}%".format((month_data["approved_audits"] / total_audits) * 100)
                    month_data["Rejected_percentage"] = "{:.1f}%".format((month_data["rejected_audits"] / total_audits) * 100)
            month_data["total_audits"] = total_audits
        elif module == "business":
            if region:
                query['region'] = region
            query['date_of_visit'] = {'$gte': month_ago,'$lte': current_date}
            audit_data = BusinessAudit.objects(__raw__=query).order_by('-date_of_visit')
            if audit_data:
                for status_type in ["Pending", "Approved", "Rejected"]:
                    month_data[f"{status_type.lower()}_audits"] = sum(
                        1 for audit in audit_data
                        if audit.status == status_type and (audit.auditor_name == user.name or user.role == "supervisor")
                    )
                total_audits = len(audit_data)
                if total_audits > 0:
                    month_data["pending_percentage"] = "{:.1f}%".format((month_data["pending_audits"] / total_audits) * 100)
                    month_data["approved_percentage"] = "{:.1f}%".format((month_data["approved_audits"] / total_audits) * 100)
                    month_data["Rejected_percentage"] = "{:.1f}%".format((month_data["rejected_audits"] / total_audits) * 100)
            month_data["total_audits"] = total_audits
        return jsonify(month_data)


class AuditDashboardQuarter(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized() 
        module = request.json.get("module")
        region = request.json.get("region")
        year = request.json.get("year")
        years_data = {}
        query = {}
        if module == "consumer":
            for Q in ["Q1","Q2","Q3","Q4"]:
                data = {}
                if Q == "Q1":
                    start_date = datetime(year, 1, 1)
                    end_date = datetime(year, 3,31)
                elif Q =="Q2":
                    start_date = datetime(year, 4, 1)
                    end_date = datetime(year, 6,30)
                elif Q =="Q3":
                    start_date = datetime(year, 7, 1)
                    end_date = datetime(year, 9,30)
                elif Q =="Q4":
                    start_date = datetime(year, 10, 1)
                    end_date = datetime(year, 12,31)
                if region:
                    query['region'] = region
                query['createdDate'] = {'$gte': start_date,'$lte': end_date}
                print(query)
                audit_data = AuditData.objects(__raw__=query).order_by('-createdDate')
                print(audit_data.count())
                if audit_data:
                    for status_type in ["Pending", "Approved", "Rejected"]:
                        data[f"{status_type.lower()}_audits"] = sum(
                            1 for audit in audit_data
                            if audit.status == status_type)
                    total_audits = len(audit_data)
                    if total_audits > 0:
                        data["pending_percentage"] = "{:.1f}%".format((data["pending_audits"] / total_audits) * 100)
                        data["approved_percentage"] = "{:.1f}%".format((data["approved_audits"] / total_audits) * 100)
                        data["Rejected_percentage"] = "{:.1f}%".format((data["rejected_audits"] / total_audits) * 100)
                    data["total_audits"] = total_audits
                    start_date = start_date.date()
                    end_date = end_date.date()
                    date_range = f"{start_date} to {end_date}" if start_date and end_date else "Not specified"
                    data["date_range"] = date_range
                    years_data[Q] = data
        elif module == "business":
            for Q in ["Q1","Q2","Q3","Q4"]:
                data = {}
                if Q == "Q1":
                    start_date = datetime(year, 1, 1)
                    end_date = datetime(year, 3,31)
                elif Q =="Q2":
                    start_date = datetime(year, 4, 1)
                    end_date = datetime(year, 6,30)
                elif Q =="Q3":
                    start_date = datetime(year, 7, 1)
                    end_date = datetime(year, 9,30)
                elif Q =="Q4":
                    start_date = datetime(year, 10, 1)
                    end_date = datetime(year, 12,31)
                if region:
                    query['region'] = region
                query['date_of_visit'] = {'$gte': start_date,'$lte': end_date}
                audit_data = BusinessAudit.objects(__raw__=query).order_by('-date_of_visit')
                if audit_data:
                    for status_type in ["Pending", "Approved", "Rejected"]:
                        data[f"{status_type.lower()}_audits"] = sum(
                        1 for audit in audit_data
                        if audit.status == status_type and (audit.auditor_name == user.name or user.role == "supervisor")
                    )
                    total_audits = len(audit_data)
                    if total_audits > 0:
                        data["pending_percentage"] = "{:.1f}%".format((data["pending_audits"] / total_audits) * 100)
                        data["approved_percentage"] = "{:.1f}%".format((data["approved_audits"] / total_audits) * 100)
                        data["Rejected_percentage"] = "{:.1f}%".format((data["rejected_audits"] / total_audits) * 100)
                    data["total_audits"] = total_audits
                    start_date = start_date.date()
                    end_date = end_date.date()
                    date_range = f"{start_date} to {end_date}" if start_date and end_date else "Not specified"
                    data["date_range"] = date_range
                    years_data[Q] = data
        return jsonify(years_data)
        
