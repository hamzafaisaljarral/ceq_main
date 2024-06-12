from dateutil import parser
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from mongoengine import DoesNotExist

from ceq_user.database.models import User, Category
from ceq_user.resources.errors import unauthorized
from consumer.report import calculate_compliance, \
    calculate_compliance_graph, calculate_compliance_for_shared_zone, \
    get_top_error_codes_by_region, get_error_descriptions, get_top_error_codes_for_shared_zone, \
    total_audits_by_region, get_top_5_error_codes, \
    calculate_category_error_stats, audited_data_for_technicians_region_wise, get_images_data, last_six_month_category_non_compliance


class RegionComplianceReport(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        compliance = calculate_compliance(start_date, end_date)

        response = {
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

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        compliance = calculate_compliance_for_shared_zone(start_date, end_date)
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

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
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

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        print(start_date_str, end_date_str)

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        results = get_top_error_codes_for_shared_zone(start_date, end_date)
        region_error_info = {}

        for result in results:
            region = result['region']
            description = get_error_descriptions(result['violation_code'])
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
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        results = get_top_5_error_codes(start_date, end_date)
        region_error_info = []

        for result in results:
            description = get_error_descriptions(result['violation_code'])
            error_info = {
                'violation_code': result['violation_code'],
                'description': description.get(result['violation_code'], 'Description not found'),
                'error_percentage': round(result['error_percentage'])
            }
            region_error_info.append(error_info)

        return jsonify({'non_compliance_other_contributor': region_error_info})


class CategoryNonComplianceContributor(Resource):
    @jwt_required()
    def get(self):
        try:
           user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
           return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
           return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        categories = [cat.name for cat in Category.objects.only('name')]
        results = calculate_category_error_stats( start_date, end_date, categories)

        return jsonify({'category results': results})


class AuditedTechnicians(Resource):
    @jwt_required()
    def get(self):
        try:
           user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
           return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
           return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        print(start_date_str, end_date_str)

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        result = audited_data_for_technicians_region_wise(start_date,end_date)
        print("es", result)
        final_output = []
        for result in result:
            region = result['region']
            compliance_count = 0
            non_compliance_count = 0
            non_cooperative_count = 0

            for detail in result['compliance_details']:
                if detail['type'] == 'Compliance':
                    compliance_count += detail['count']
                elif detail['type'] == 'Non-Compliance':
                    non_compliance_count += detail['count']
                    non_cooperative_count += detail[
                        'count']  # Assuming all non-compliance under CEQV27 are non-cooperative

            final_output.append({
                "region": region,
                "compliance_count": compliance_count,
                "non_compliance_count": non_compliance_count,
                "non_cooperative_count": non_cooperative_count
            })

        return jsonify({'category_results': final_output})


class ComplianceandNonComplianceImages(Resource):
    @jwt_required()
    def get(self):
        try:
           user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
           return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
           return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        region = request.args.get('region')

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        result = get_images_data(start_date,end_date, region)

        return jsonify({'image_url': result})


class NonComplianceCategoryLastSixMonths(Resource):
    @jwt_required()
    def get(self):
        try:
            user = User.objects.get(id=get_jwt_identity()['id'])
        except DoesNotExist:
            return unauthorized()
        if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
            return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        region = request.args.get('region')

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        result = last_six_month_category_non_compliance(start_date, end_date)

        return jsonify({'total_category_error_count': result})
