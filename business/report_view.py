from dateutil import parser
from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta

from mongoengine import DoesNotExist

from ceq_user.database.models import User, Category
from ceq_user.resources.errors import unauthorized
from business.report import compliance_business_check, count_error_codes, overall_compliance_check, \
    calculate_account_category_percentages, calculate_monthly_compliance, count_error_codes_monthwise, \
    business_name_with_non_compliance, get_images_with_compliance


class RegionComplianceBusinessReport(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        compliance = compliance_business_check(start_date, end_date)

        response = {
            'compliance_by_region': compliance
        }
        return jsonify(response)


class OverallBusinessReport(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        compliance = overall_compliance_check(start_date, end_date)

        response = {
            'overall': compliance
        }
        return jsonify(response)


class CategoryBusinessReport(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        non_compliance = count_error_codes(start_date, end_date)

        response = {
            'non_compliance_by_category': non_compliance
        }
        return jsonify(response)


class AccountCategory(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        account_category = calculate_account_category_percentages(start_date, end_date)

        response = {
            'account_category': account_category
        }
        return jsonify(response)


class RegionWisePastData(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        account_category = calculate_monthly_compliance(start_date, end_date)

        response = {
            'account_category': account_category
        }
        return jsonify(response)


class BusinessReportGraph(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        non_compliance = count_error_codes(start_date, end_date)

        response = {
            'non_compliance_by_category': non_compliance
        }
        return jsonify(response)


class NonComplianceContributerVistor(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        non_compliance_business = business_name_with_non_compliance(start_date, end_date)

        response = {
            'non_compliance_by_business': non_compliance_business
        }
        return jsonify(response)


class NonComplianceContributerSixMonths(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #     user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #     return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #     return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        if start_date_str is None or end_date_str is None:
            return jsonify({'error': 'Missing start_date or end_date parameter'}), 400

        try:
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400

        non_compliance_month_wise = count_error_codes_monthwise(start_date, end_date)

        response = {
            'non_compliance_month_wise': non_compliance_month_wise
        }
        return jsonify(response)


class BusinessComplianceandNonComplianceImages(Resource):
    # @jwt_required()
    def get(self):
        # try:
        #    user = User.objects.get(id=get_jwt_identity()['id'])
        # except DoesNotExist:
        #    return unauthorized()
        # if user.role not in ["supervisor", "admin"] and user.permission not in ["consumer", "all"]:
        #    return {"message": "Unauthorized access"}, 401
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        region = request.args.get('region')

        try:
            # Convert date strings to datetime objects
            start_date = parser.parse(start_date_str)
            end_date = parser.parse(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        result = get_images_with_compliance(start_date,end_date)

        return jsonify({'image_url': result})