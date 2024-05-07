from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from mongoengine import DoesNotExist

from ceq_user.database.models import User
from ceq_user.resources.errors import unauthorized
from consumer.report import get_date_from_days, total_audits, errors_by_region, calculate_compliance, \
    calculate_compliance_graph, calculate_compliance_for_shared_zone, \
    get_top_error_codes_by_region, get_error_descriptions, get_top_error_codes_for_shared_zone, \
    total_audits_from_shared_zone, total_audits_by_region, get_top_5_error_codes


class RegionComplianceReport(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        days = request.args.get('days', 7)
        if int(days) not in [7, 15, 30, 90]:
            return jsonify({'error': 'Days must be one of [7, 15, 30, 90]'}), 400

        start_date, end_date = get_date_from_days(int(days))
        compliance = calculate_compliance(start_date, end_date)

        response = {
            'date_range': f"{days} days ending on {datetime.now().strftime('%Y-%m-%d')}",
            'compliance_by_region': compliance
        }
        return jsonify(response)


class RegionComplianceReportGraph(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        # Get the current date and time
        compliance = calculate_compliance_graph()

        response = {
            'compliance_by_region': compliance
        }
        return jsonify(response)


class RegionComplianceReportSharedZone(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        days = request.args.get('days', 7)
        if int(days) not in [7, 15, 30, 90]:
            return jsonify({'error': 'Days must be one of [7, 15, 30, 90]'}), 400

        start_date, end_date = get_date_from_days(int(days))
        compliance = calculate_compliance_for_shared_zone(start_date, end_date)
        print(compliance)
        response = {
            'compliance_for_shared_zone': compliance,
        }
        return jsonify(response)


class RegionNonComplianceTopContributor(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        days = request.args.get('days', 7)
        if int(days) not in [7, 15, 30, 90]:
            return jsonify({'error': 'Days must be one of [7, 15, 30, 90]'}), 400

        start_date, end_date = get_date_from_days(int(days))
        results = get_top_error_codes_by_region(start_date, end_date)
        region_error_info = {}

        for result in results:
            region = result['_id']
            top_errors = result.get('top_5_errors', [])
            total_audits_in_region = total_audits_by_region(start_date, end_date, region) # Use region directly

            for error in top_errors:
                error_codes = [e['violation_code'] for e in top_errors]
                descriptions = get_error_descriptions(error_codes)

                for error in top_errors:
                    error['description'] = descriptions.get(error['violation_code'], 'Description not found')
                    total_audits_count = total_audits_in_region.get(region, 0)  # Extract the count from the dictionary
                    error['percentage'] = round(
                        (error['count'] / total_audits_count) * 100) if total_audits_count > 0 else 0

            region_error_info[region] = top_errors

        return jsonify({'non_compliance_top_contributor': region_error_info})
    

class SharedzoneNonComplianceTopContributor(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        days = request.args.get('days', 7)
        if int(days) not in [7, 15, 30, 90]:
            return jsonify({'error': 'Days must be one of [7, 15, 30, 90]'}), 400

        start_date, end_date = get_date_from_days(int(days))
        results = get_top_error_codes_for_shared_zone()
        print(results)
        region_error_info = {}

        for result in results:
            region = result['region']
            description = get_error_descriptions(result['violation_code'])
            print("desc",description)
            error_info = {
                'violation_code': result['violation_code'],
                'description': description.get(result['violation_code'], 'Description not found'),
                'error_percentage': round(result['error_percentage'])
            }
            if region not in region_error_info:
                region_error_info[region] = []
            region_error_info[region].append(error_info)

        return jsonify({'non_compliance_top_contributor': region_error_info})


class OtherNonComplianceTopContributor(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        days = request.args.get('days', 7)
        if int(days) not in [7, 15, 30, 90]:
            return jsonify({'error': 'Days must be one of [7, 15, 30, 90]'}), 400

        start_date, end_date = get_date_from_days(int(days))
        results = get_top_5_error_codes(start_date, end_date)
        print(results)
        region_error_info = []

        for result in results:
            description = get_error_descriptions(result['violation_code'])
            print("desc", description)
            error_info = {
                'violation_code': result['violation_code'],
                'description': description.get(result['violation_code'], 'Description not found'),
                'error_percentage': round(result['error_percentage'])
            }
            region_error_info.append(error_info)

        return jsonify({'non_compliance_other_contributor': region_error_info})




