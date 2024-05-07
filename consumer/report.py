import calendar
from collections import defaultdict, Counter

from ceq_user.database.models import AuditData, Category
from datetime import datetime, timedelta

start_date = datetime(2023, 12, 1)
end_date = datetime(2023, 12, 30)


def get_date_from_days(days: int):
    end_date = datetime.now()  # Current date and time as the end date
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def total_audits_by_region(start_date, end_date, region):
    pipeline = [
        {
            '$match': {
                'createdDate': {'$gte': start_date, '$lte': end_date},
                'region': region,
                'status': 'Approved',
                'ceqvs': {
                    '$elemMatch': {
                        'remarks': {'$exists': True, '$ne': ''},
                        'violation_type': True
                    }
                }
            }
        },
        {
            '$group': {
                '_id': '$region',
                'TotalAudits': {'$sum': 1}
            }
        }
    ]
    results = AuditData.objects.aggregate(*pipeline)
    return {result['_id']: result['TotalAudits'] for result in results}


def total_audits():
    print('total', AuditData.objects(createdDate__gte=start_date, createdDate__lte=end_date).count())
    return AuditData.objects(createdDate__gte=start_date, createdDate__lte=end_date).count()


def total_audits_from_shared_zone():
    total_audits = AuditData.objects(
        createdDate__gte=start_date,
        createdDate__lte=end_date,
        sr_number__icontains='shared zone'
    ).count()

    return total_audits



def errors_by_region(start_date, end_date):
    # Specify the regions to match against
    regions = ['ABU DHABI', 'DUBAI', 'NORTHERN EMIRATES', 'WR']

    pipeline = [
        {
            '$match': {
                'createdDate': {'$gte': start_date, '$lte': end_date},
                'region': {'$in': regions},
                'status': 'Approved'  # Ensure the audit is approved
            }
        },
        {
            '$project': {
                'region': 1,
                'errors': {
                    '$map': {
                        'input': '$ceqvs',
                        'as': 'ceqv',
                        'in': '$$ceqv.violation_type'  # Directly use the boolean value of violation_type
                    }
                }
            }
        },
        {
            '$addFields': {
                'errorPresent': {
                    '$anyElementTrue': ['$errors']  # Checks if any error (True) is present
                }
            }
        },
        {
            '$group': {
                '_id': '$region',
                'ErrorCount': {'$sum': {'$cond': [{'$eq': ['$errorPresent', True]}, 1, 0]}}  # Count only if errorPresent is True
            }
        },
        {
            '$project': {
                '_id': 1,
                'ErrorCount': 1
            }
        }
    ]

    # Create a dictionary to map region names to error counts
    error_counts = {region: 0 for region in regions}

    # Get the error counts for each region from the aggregation result
    results = AuditData.objects.aggregate(pipeline)
    for result in results:
        error_counts[result['_id']] = result['ErrorCount']

    # Convert the dictionary to a list of dictionaries
    final_results = [{'_id': region, 'ErrorCount': error_counts[region]} for region in regions]

    return final_results


def calculate_percentage(start_date, end_date):
    error_results = errors_by_region(start_date, end_date)
    total_errors_by_region = {result['_id']: result['ErrorCount'] for result in error_results}

    # Get total number of audits for each region
    total_audits_by_region_result = total_audits_by_region(start_date, end_date)

    # Calculate percentage for each region
    percentage_results = {}
    for region, total_errors in total_errors_by_region.items():
        total_audits = total_audits_by_region_result.get(region, 0)  # Get the total audits, default to 0 if region not found
        if total_audits > 0:
            percentage = (total_errors / (6 * total_audits)) * 100
        else:
            percentage = 0
        percentage_results[region] = round(percentage, 2)

    return percentage_results


def calculate_compliance(start_date, end_date):
    # Define all expected regions and start compliance at 0%
    percentage_results = calculate_percentage(start_date,end_date)
    compliance_results = {}
    for region, percentage in percentage_results.items():
        compliance = 100 - percentage
        compliance_results[region] = round(compliance, 2)
    return compliance_results


def calculate_compliance_graph():
    today = datetime.now()
    end_date = datetime(today.year, today.month, today.day)  # End date is today's date

    # Calculate start date as 4 months ago from today
    start_date = end_date - timedelta(days=4 * 30)  # Assuming a month is 30 days for simplicity

    # Define all expected regions
    regions = ['ABU DHABI', 'DUBAI', 'NORTHERN EMIRATES', 'WR']

    # Initialize compliance_results dictionary to store results for each month
    compliance_results = {}

    while start_date < end_date:
        month_name = calendar.month_name[start_date.month]
        percentage_results = calculate_percentage(start_date, end_date)
        compliance_results[month_name] = {}
        for region, percentage in percentage_results.items():
            compliance = 100 - percentage
            compliance_results[month_name][region] = f"{compliance}%"
        # Move to the next month
        start_date = start_date.replace(day=1) + timedelta(days=calendar.monthrange(start_date.year, start_date.month)[1])

    return compliance_results


def calculate_compliance_for_shared_zone(start_date, end_date, region='WR'):
    # Calculate percentage for the specified region
    percentage_results = calculate_percentage(start_date, end_date)
    wr_percentage = percentage_results.get(region, 0)

    # Calculate compliance for the specified region
    result = {}
    compliance = 100 - wr_percentage
    non_complaince = wr_percentage
    result['compliance'] = round(compliance, 2)
    result['non_compliance'] = non_complaince

    return result


def get_top_error_codes_by_region(start_date, end_date):
    pipeline = [
        {
            '$match': {
                'createdDate': {
                    '$gte': start_date,
                    '$lte': end_date
                },
                'status': 'Approved'
            }
        },
        {'$unwind': '$ceqvs'},
        {
            '$match': {
                "ceqvs.remarks": {"$ne": "", "$exists": True},
                "ceqvs.violation_type": True
            }
        },
        {
            '$group': {
                '_id': {
                    'region': '$region',
                    'violation_code': '$ceqvs.violation_code'
                },
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'count': -1}},
        {
            '$group': {
                '_id': '$_id.region',
                'top_errors': {'$push': {
                    'violation_code': '$_id.violation_code',
                    'count': '$count'
                }}
            }
        },
        {
            '$project': {
                'top_5_errors': {'$slice': ['$top_errors', 5]}
            }
        }
    ]

    results = AuditData.objects.aggregate(*pipeline)
    return list(results)


def get_error_descriptions(error_codes):
    if isinstance(error_codes, str):
        error_codes = [error_codes]

    descriptions = {}
    for error_code in error_codes:
        category = Category.objects.filter(error_codes__code=error_code).first()
        if category:
            error_info = next((ec for ec in category.error_codes if ec.code == error_code), None)
            if error_info:
                descriptions[error_code] = error_info.description
    return descriptions


def get_top_error_codes_for_shared_zone():
    pipeline = [
        {
            '$match': {
                'createdDate': {
                    '$gte': start_date,
                    '$lte': end_date
                },
                'status': 'Approved',
                'sr_number': {'$regex': 'shared zone', '$options': 'i'}
            }
        },
        {'$unwind': '$ceqvs'},
        {
            '$match': {
                "ceqvs.remarks": {"$ne": "", "$exists": True},
                "ceqvs.violation_type": True
            }
        },
        {
            '$group': {
                '_id': {
                    'region': '$region',
                    'violation_code': '$ceqvs.violation_code'
                },
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'count': -1}},
        {
            '$group': {
                '_id': '$_id.region',
                'total_audits': {'$sum': '$count'},
                'top_errors': {'$push': {
                    'violation_code': '$_id.violation_code',
                    'count': '$count'
                }}
            }
        },
        {
            '$project': {
                'top_5_errors': {'$slice': ['$top_errors', 5]},
                'total_audits': 1
            }
        },
        {
            '$unwind': '$top_5_errors'
        },
        {
            '$project': {
                '_id': 0,
                'region': '$_id',
                'violation_code': '$top_5_errors.violation_code',
                'error_count': '$top_5_errors.count',
                'total_audits': 1
            }
        },
        {
            '$project': {
                'region': 1,
                'violation_code': 1,
                'error_percentage': {'$multiply': [{'$divide': ['$error_count', '$total_audits']}, 100]}
            }
        }
    ]

    results = AuditData.objects.aggregate(*pipeline)
    return list(results)


def get_top_5_error_codes(start_date, end_date):
    pipeline = [
        {
            '$match': {
                'createdDate': {
                    '$gte': start_date,
                    '$lte': end_date
                },
                'status': 'Approved',
                'sr_number': {'$regex': 'shared zone', '$options': 'i'}
            }
        },
        {'$unwind': '$ceqvs'},
        {
            '$match': {
                "ceqvs.violation_type": True
            }
        },
        {
            '$group': {
                '_id': {
                    'region': '$region',
                    'violation_code': '$ceqvs.violation_code'
                },
                'count': {'$sum': 1}
            }
        },
        {'$sort': {'count': -1}},
        {
            '$group': {
                '_id': '$_id.region',
                'total_audits': {'$sum': '$count'},
                'top_errors': {'$push': {
                    'violation_code': '$_id.violation_code',
                    'count': '$count'
                }}
            }
        },
        {
            '$project': {
                'top_5_errors': {'$slice': ['$top_errors', 5]},
                'total_audits': 1
            }
        },
        {
            '$unwind': '$top_5_errors'
        },
        {
            '$project': {
                '_id': 0,
                'region': '$_id',
                'violation_code': '$top_5_errors.violation_code',
                'error_count': '$top_5_errors.count',
                'total_audits': 1
            }
        },
        {
            '$project': {
                'region': 1,
                'violation_code': 1,
                'error_percentage': {'$multiply': [{'$divide': ['$error_count', '$total_audits']}, 100]}
            }
        }
    ]

    results = AuditData.objects.aggregate(*pipeline)
    return list(results)

