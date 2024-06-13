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
        total_audits = 0
        dict_data = {
            "pending_audits" : 0,
            "submitted_audits" : 0,
            "revert_audits":0,
            "rejected_audits":0,
            "approved_audits":0,
            "total_audits" : 0
        }
        dict_data["date_range"] = date_range
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
            if user.role == "auditor":
                query["auditor_name"] = user.name
            print(query)    
            audit_data = AuditData.objects(__raw__=query).order_by('-createdDate')
            if audit_data:
                for status_type in ["Pending", "Approved", "Revert","Submitted","Rejected"]:
                    dict_data[f"{status_type.lower()}_audits"] = sum(
                        1 for audit in audit_data
                        if audit.status == status_type
                    )
            total_audits = dict_data["pending_audits"] + dict_data["submitted_audits"] + dict_data["revert_audits"] + dict_data["rejected_audits"] + dict_data["approved_audits"]
            dict_data["total_audits"] = total_audits
            dict_data["pending_audits"] = dict_data["pending_audits"] + dict_data["submitted_audits"]
            dict_data["revert_audits"] = dict_data["revert_audits"] + dict_data["rejected_audits"]
            del dict_data["submitted_audits"]
            del dict_data["rejected_audits"]
        if module == "business":            
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
            if user.role == "auditor":
                query["ceq_auditor_name"] = user.name
            print("query",query)    
            audit_data = BusinessAudit.objects(__raw__=query).order_by('-date_of_visit')
            if audit_data:
                status_types = ["pending", "approved", "revert", "submitted", "rejected"]
                for status_type in status_types:
                    dict_data[f"{status_type}_audits"] = sum(
                        1 for audit in audit_data
                        if audit.status.lower() == status_type
                    )
                total_audits = dict_data["pending_audits"] + dict_data["submitted_audits"] + dict_data["revert_audits"] + dict_data["rejected_audits"] + dict_data["approved_audits"]
                dict_data["total_audits"] = total_audits
                dict_data["pending_audits"] = dict_data["pending_audits"] + dict_data["submitted_audits"]
                dict_data["revert_audits"] = dict_data["revert_audits"] + dict_data["rejected_audits"]
                del dict_data["submitted_audits"]
                del dict_data["rejected_audits"]

        return jsonify(dict_data)          





class AuditDashboardMonth(Resource):
    @jwt_required()
    def post(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized() 
        current_date = datetime.now().date()
        end_date = datetime.combine(current_date, time.min)
        module = request.json.get("module")
        region = request.json.get("region")
        status = request.json.get("status")
        start_date = request.json.get("start_date")
        # Calculate the start date for six months ago
        if start_date != "":
            date_obj = datetime.strptime(start_date,'%Y-%m-%d')
            end_date = datetime.strptime(start_date, '%Y-%m-%d')
            month_ago = date_obj - timedelta(days=30)
            start_date_str = month_ago.strftime('%Y-%m-%d %H:%M:%S')
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
        else:
            month_ago = current_date - timedelta(days=30)
            start_date = datetime.combine(month_ago, time.min)
        month_data = {}
        match_condition = {"createdDate": {"$gte": start_date, "$lte": end_date},"status": {"$in": ["Approved", "Submitted", "Pending", "Rejected", "Revert"]}}
        if region != "":
            match_condition["region"] = region
        # if user.role == "auditor":
        #     match_condition["auditor_name"] = user.name
        if module == "consumer":
            print(start_date,end_date)
            print(type(start_date),type((end_date)))
            records = get_audit_statistics(match_condition)
            print("changes",records)
            for rec in records:
                print(rec["status"])
                if rec["status"] == "Revert/Rejected":
                    month_data["revert_percentage"] = round(rec["percentage"], 2)
                    month_data["revert_count"] = rec["count"]
                if rec["status"] == "Submitted/Pending":
                    month_data["pending_percentage"] = round(rec["percentage"], 2)
                    month_data["pending_count"] = rec["count"]
                if rec["status"] == "Approved":
                    month_data["approved_percentage"] = round(rec["percentage"], 2)
                    month_data["approved_count"] = rec["count"]
        match_condition = {"date_of_visit": {"$gte": start_date, "$lte": end_date},"status": {"$in": ["Approved", "Submitted", "Pending", "Rejected", "Revert"]}}
        if region != "":
            match_condition["region"] = region
        # if user.role == "auditor":
        #     match_condition["ceq_auditor_name"] = user.name
        if module == "business":
            records = get_bussines_statistics(match_condition)
            print(start_date,end_date)
            for rec in records:
                if rec["status"] == "revert/rejected":
                    month_data["revert_percentage"] = round(rec["percentage"], 2)
                    month_data["revert_count"] = rec["count"]
                if rec["status"] == "submitted/pending":
                    month_data["pending_percentage"] = round(rec["percentage"], 2)
                    month_data["pending_count"] = rec["count"]
                if rec["status"] == "approved":
                    month_data["approved_percentage"] = round(rec["percentage"], 2)
                    month_data["approved_count"] = rec["count"]

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
        status = request.json.get("status")
        years_data = {}
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

            match_condition = {"createdDate": {"$gte": start_date, "$lte": end_date},"status": {"$in": ["Approved", "Submitted", "Pending", "Rejected", "Revert"]}}
            if region != "":
                match_condition["region"] = region
            if user.role == "auditor":
                match_condition["auditor_name"] = user.name
            if module == "consumer":
                records = get_audit_statistics(match_condition)
                data = {}
                for rec in records:
                    if rec["status"] == "Revert/Rejected":
                        data["revert_percentage"] = round(rec["percentage"], 2)
                        data["revert_count"] = rec["count"]
                    if rec["status"] == "Submitted/Pending":
                        data["pending_percentage"] = round(rec["percentage"], 2)
                        data["pending_count"] = rec["count"]
                    if rec["status"] == "Approved":
                        data["approved_percentage"] = round(rec["percentage"], 2)
                        data["approved_count"] = rec["count"]
                years_data[Q] = data
            match_condition = {"date_of_visit": {"$gte": start_date, "$lte": end_date},"status": {"$in": ["Approved", "Submitted", "Pending", "Rejected", "Revert"]}}
            if region != "":
                match_condition["region"] = region
            if user.role == "auditor":
                match_condition["ceq_auditor_name"] = user.name
            elif module == "business":
                records = get_bussines_statistics(match_condition)
                data = {}
                for rec in records:
                    if rec["status"] == "revert/rejected":
                        data["revert_percentage"] = round(rec["percentage"], 2)
                        data["revert_count"] = rec["count"]
                    if rec["status"] == "submitted/pending":
                        data["pending_percentage"] = round(rec["percentage"], 2)
                        data["pending_count"] = rec["count"]
                    if rec["status"] == "approved":
                        data["approved_percentage"] = round(rec["percentage"], 2)
                        data["approved_count"] = rec["count"]
                years_data[Q] = data
        return jsonify(years_data)
        


def get_audit_statistics(match_condition):
    pipeline = [
        {"$match": match_condition},
        {"$group": {
            "_id": {
                "$cond": [
                    {"$or": [
                        {"$eq": ["$status", "Approved"]}
                    ]},
                    "Approved",
                    {"$cond": [
                        {"$or": [
                            {"$eq": ["$status", "Rejected"]},
                            {"$eq": ["$status", "Revert"]}
                        ]},
                        "Revert/Rejected",
                        "Submitted/Pending"
                    ]}
                ]
            },
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$count"},
            "statuses": {"$push": {"status": "$_id", "count": "$count"}}
        }},
        {"$unwind": "$statuses"},
        {"$project": {
            "_id": 0,
            "status": "$statuses.status",
            "count": "$statuses.count",
            "percentage": {"$multiply": [{"$divide": ["$statuses.count", "$total"]}, 100]}
        }}
    ]
    result = list(AuditData.objects.aggregate(pipeline))
    return result

    
def get_bussines_statistics(match_condition):
    pipeline = [
        {"$match":match_condition},
        {"$group": {
            "_id": {
                "$cond": [
                    {"$or": [
                        {"$eq": ["$status", "approved"]}
                    ]},
                    "approved",
                    {"$cond": [
                        {"$or": [
                            {"$eq": ["$status", "rejected"]},
                            {"$eq": ["$status", "revert"]}
                        ]},
                        "revert/rejected",
                        "submitted/pending"
                    ]}
                ]
            },
            "count": {"$sum": 1}
        }},
        {"$group": {
            "_id": None,
            "total": {"$sum": "$count"},
            "statuses": {"$push": {"status": "$_id", "count": "$count"}}
        }},
        {"$unwind": "$statuses"},
        {"$project": {
            "_id": 0,
            "status": "$statuses.status",
            "count": "$statuses.count",
            "percentage": {"$multiply": [{"$divide": ["$statuses.count", "$total"]}, 100]}
        }}
    ]
    result = list(BusinessAudit.objects.aggregate(pipeline))
    return result