import calendar
import itertools
from collections import defaultdict, Counter

from ceq_user.database.models import AuditData, Category
from datetime import datetime, timedelta

# previous_start_date = datetime(2023,10,2)
# previous_end_date = datetime(2023,10,31)
# print("update",type(previous_end_date))



def errors_by_region_wr(start_date, end_date):
    # Specify the regions to match against
    regions = 'WR'

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
                    '$reduce': {
                        'input': '$errors',
                        'initialValue': False,
                        'in': {'$or': ['$$value', '$$this']}  # Check if any element in errors is True
                    }
                }
            }
        },
        {
            '$group': {
                '_id': '$region',
                'ErrorCount': {'$sum': {'$cond': ['$errorPresent', 1, 0]}}  # Count only if errorPresent is True
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
    results = AuditData.objects.aggregate(*pipeline)
    for result in results:
        error_counts[result['_id']] = result['ErrorCount']

    # Convert the dictionary to a list of dictionaries
    final_results = [{'_id': region, 'ErrorCount': error_counts[region]} for region in regions]

    return final_results


def total_wr(start_date, end_date):
    region = 'WR'
    pipeline = [
        {
            '$match': {
                'createdDate': {'$gte': start_date, '$lte': end_date},
                'region': region,
                'status': 'Approved'
            }
        },
        {
            '$group': {
                '_id': '$region',
                'TotalAudits': {'$sum': 1}
            }
        }
    ]

    # Get the total audits for the "WR" region from the aggregation result
    result = AuditData.objects.aggregate(*pipeline)
    first_result = next(result, None)  # Get the first result or None if the cursor is empty
    total_audits_wr_result = first_result['TotalAudits'] if first_result else 0

    return total_audits_wr_result


def calculate_percentage_shared_zone(start_date, end_date):
    # Get the total errors for the "shared" region
    error_results = errors_by_region_shared_zone(start_date, end_date)
    total_errors_by_region = sum(result['ErrorCount'] for result in error_results)
    print(error_results)

    # Get the total audits for the "WR" region
    total_audits_wr = total_wr(start_date, end_date)

    # Calculate the percentage for the "WR" region
    if total_audits_wr > 0:
        percentage_wr = (total_errors_by_region / (6 * total_audits_wr)) * 100
    else:
        percentage_wr = 0

    return round(percentage_wr, 2)

def get_date_from_days(days: int):
    end_date = datetime.now()  # Current date and time as the end date
    start_date = end_date - timedelta(days=days)
    return start_date, end_date


def get_date_past_current(start_date, end_date):
    """
    Calculates the start and end dates for the previous period based on the provided start and end dates.
    Formats the dates to include time '00:00:00' for clarity in timestamps.

    :param start_date: The start date as a datetime object.
    :param end_date: The end date as a datetime object.
    :return: A tuple containing the formatted start and end datetime strings for the previous period.
    """
    # Ensure end_date and start_date are at midnight
    end_date_current = datetime(end_date.year, end_date.month, end_date.day)
    start_date_current = datetime(start_date.year, start_date.month, start_date.day)

    # Calculate the duration of the current period
    period_duration = end_date_current - start_date_current

    # Calculate the end date for the previous period (one day before the current start date)
    end_date_previous = start_date_current - timedelta(days=1)
    # Calculate the start date for the previous period
    start_date_previous = end_date_previous - period_duration

    # Format to 'YYYY-MM-DD HH:MM:SS'
    formatted_start_date_previous = start_date_previous.strftime('%Y-%m-%d %H:%M:%S')
    formatted_end_date_previous = end_date_previous.strftime('%Y-%m-%d %H:%M:%S')

    return (datetime.strptime(formatted_start_date_previous, '%Y-%m-%d %H:%M:%S'), datetime.strptime(formatted_end_date_previous, '%Y-%m-%d %H:%M:%S'))


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

    
def errors_by_region_shared_zone(start_date, end_date):
    # Specify the regions to match against

    pipeline = [
        {
            '$match': {
                'createdDate': {'$gte': start_date, '$lte': end_date},
                'sr_number': {'$regex': 'shared zone', '$options': 'i'},
                'status': 'Approved'
            }
        },
        {'$unwind': '$ceqvs'},  # Unwind the ceqvs first to facilitate easier processing
        {
            '$project': {
                'errorPresent': '$ceqvs.violation_type'  # Directly use the boolean value of violation_type
            }
        },
        {
            '$group': {
                '_id': '$region',
                'ErrorCount': {'$sum': {'$cond': ['$errorPresent', 1, 0]}}  # Increment count if errorPresent is True
            }
        },
        {
            '$project': {
                'region': '$_id',
                'ErrorCount': 1,
                '_id': 0
            }
        }
    ]

    results = list(AuditData.objects.aggregate(pipeline))
    final_results = {}  # Initialize all regions with zero count

    # Update counts based on aggregation results
    for result in results:
        final_results[result['region']] = result['ErrorCount']

    # Convert the dictionary to a list of dictionaries for output
    return [{'region': k, 'ErrorCount': v} for k, v in final_results.items()]


def errors_by_region(start_date, end_date):
    # Specify the regions to match against
    regions = ['ABU DHABI', 'DUBAI', 'NORTHERN EMIRATES', 'WR']

    pipeline = [
        {
            '$match': {
                'createdDate': {'$gte': start_date, '$lte': end_date},
                'region': {'$in': regions},
                'status': 'Approved'
            }
        },
        {'$unwind': '$ceqvs'},  # Unwind the ceqvs first to facilitate easier processing
        {
            '$project': {
                'region': 1,
                'errorPresent': '$ceqvs.violation_type'  # Directly use the boolean value of violation_type
            }
        },
        {
            '$group': {
                '_id': '$region',
                'ErrorCount': {'$sum': {'$cond': ['$errorPresent', 1, 0]}}  # Increment count if errorPresent is True
            }
        },
        {
            '$project': {
                'region': '$_id',
                'ErrorCount': 1,
                '_id': 0
            }
        }
    ]

    results = list(AuditData.objects.aggregate(pipeline))
    final_results = {region: 0 for region in regions}  # Initialize all regions with zero count

    # Update counts based on aggregation results
    for result in results:
        final_results[result['region']] = result['ErrorCount']

    # Convert the dictionary to a list of dictionaries for output
    return [{'region': k, 'ErrorCount': v} for k, v in final_results.items()]


def total_audits_regions(start_date, end_date):
    regions = ['ABU DHABI', 'DUBAI', 'NORTHERN EMIRATES', 'WR']
    pipeline = [
        {
            '$match': {
                'createdDate': {'$gte': start_date, '$lte': end_date},
                'region': {'$in': regions},
                'status': 'Approved'
            }
        },
        {
            '$group': {
                '_id': '$region',
                'TotalAudits': {'$sum': 1}
            }
        }
    ]

    # Create a dictionary to store the total audits for each region
    total_audits_by_region = {region: 0 for region in regions}

    # Get the total audits for each region from the aggregation result
    results = AuditData.objects.aggregate(*pipeline)
    for result in results:
        total_audits_by_region[result['_id']] = result['TotalAudits']

    return total_audits_by_region


def calculate_percentage(start_date, end_date):

    error_results = errors_by_region(start_date, end_date)
    total_errors_by_region = {result['region']: result['ErrorCount'] for result in error_results}

    # Get total number of audits for each region
    total_audits_by_region_result = total_audits_regions(start_date, end_date)

    # Calculate percentage for each region
    percentage_results = {}
    for region, total_errors in total_errors_by_region.items():
        total_audits = total_audits_by_region_result.get(region, 0)  # Get the total audits, default to 0 if region not found
        if total_audits > 0:
            percentage = (total_errors / (6 * total_audits)) * 100
        else:
            percentage = 0
        formatted_region = region.replace(" ", "_")    
        percentage_results[formatted_region] = round(percentage, 2)

    return percentage_results


def calculate_compliance(start_date, end_date):
    # Define all expected regions and start compliance at 0%
    percentage_results = calculate_percentage(start_date, end_date)
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

    percentage_results = calculate_percentage_shared_zone(start_date, end_date)

    if isinstance(percentage_results, dict):
        wr_percentage = percentage_results.get(region, 0)
    else:
        wr_percentage = percentage_results

    # Calculate compliance for the specified region
    result = {}
    compliance = 100 - wr_percentage
    non_complaince = wr_percentage
    result['Non_compliance'] = round(compliance, 2)
    result['compliance'] = non_complaince

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
                "ceqvs.violation_type": True  # Filter for non-compliance
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
                'violations': {'$push': {
                    'violation_code': '$_id.violation_code',
                    'count': '$count'
                }}
            }
        },
        {
            '$project': {
                'top_5_errors': {'$slice': ['$violations', 5]}
            }
        }
    ]

    results = list(AuditData.objects.aggregate(pipeline))
    return results


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


def get_top_error_codes_for_shared_zone(start_date, end_date):
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
                'status': 'Approved'
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
                'top_5_errors': {
                    '$slice': [
                        '$top_errors',
                        2
                    ]
                },
                'total_audits': 1
            }
        },
        {
            '$unwind': '$top_5_errors'
        },
        {
            '$project': {
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
                'error_percentage': {
                    '$multiply': [
                        {
                            '$divide': [
                                '$error_count',
                                '$total_audits'
                            ]
                        },
                        100
                    ]
                }
            }
        }
    ]

    results = list(AuditData.objects.aggregate(pipeline))
    return results


def calculate_category_percentage(start_date, end_date):
    pipeline_total_current = [
        {
            "$match": {
                "createdDate": {"$gte": start_date, "$lte": end_date},
                "status": "Approved"
            }
        },
        {"$unwind": "$ceqvs"},
        {"$match": {"ceqvs.violation_type": True}},
        {
            "$group": {
                "_id": None,  # Grouping by None to count all docs
                "total_count": {"$sum": 1}
            }
        },
    ]
    pipeline_errors_per_category = [
        {
            "$match": {
                "createdDate": {"$gte": start_date, "$lte": end_date},
                "status": "Approved"
            }
        },
        {"$unwind": "$ceqvs"},
        {"$match": {"ceqvs.violation_type": True}},  # Assuming you want to filter violations marked as true
        {
            "$group": {
                "_id": "$ceqvs.category_code",
                "error_count": {"$sum": 1}
            }
        }
    ]

    errors_per_category = list(AuditData.objects.aggregate(pipeline_errors_per_category))

    # Run this pipeline separately to get the total count of errors
    total_errors_current = list(AuditData.objects.aggregate(pipeline_total_current))
    total_count_current = total_errors_current[0]['total_count'] if total_errors_current else 0
    return total_count_current, errors_per_category


def calculate_category_error_stats(start_date, end_date, categories):
    previous_start_date, previous_end_date = get_date_past_current(start_date, end_date)
    print("testing this", type(previous_start_date), previous_end_date)

    pipeline_current = [
        {
            "$match": {
                "createdDate": {"$gte": start_date, "$lte": end_date},
                "status": "Approved",
                "ceqvs.category_code": {"$in": categories}  # Filter audits based on desired categories
            }
        },
        {"$unwind": "$ceqvs"},
        {"$match": {"ceqvs.violation_type": True}},  # Assuming you want to consider only true violations
        {
            "$group": {
                "_id": {
                    "category_code": "$ceqvs.category_code",
                    "violation_code": "$ceqvs.violation_code"
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {
            "$group": {
                "_id": "$_id.category_code",
                "total_errors": {"$sum": "$count"},
                "top_violations": {"$push": {"violation_code": "$_id.violation_code", "count": "$count"}}
            }
        },
        {"$project": {"category": "$_id", "total_errors": 1, "top_violations": {"$slice": ["$top_violations", 2]}}},
    ]

    pipeline_previous = [
        {
            "$match": {
                "createdDate": {"$gte": start_date, "$lte": end_date},
                "status": "Approved",
                "ceqvs.category_code": {"$in": categories}  # Filter audits based on desired categories
            }
        },
        {"$unwind": "$ceqvs"},
        {"$match": {"ceqvs.violation_type": True}},  # Assuming you want to consider only true violations
        {
            "$group": {
                "_id": {
                    "category_code": "$ceqvs.category_code",
                    "violation_code": "$ceqvs.violation_code"
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"count": -1}},
        {
            "$group": {
                "_id": "$_id.category_code",
                "total_errors": {"$sum": "$count"},
                "top_violations": {"$push": {"violation_code": "$_id.violation_code", "count": "$count"}}
            }
        },
        {"$project": {"category": "$_id", "total_errors": 1, "top_violations": {"$slice": ["$top_violations", 2]}}},
    ]
    results_current = list(AuditData.objects.aggregate(*pipeline_current))
    results_previous = list(AuditData.objects.aggregate(*pipeline_previous))
    # Assuming you use the same pipelines for both current and previous periods,
    # I'll show adjustments for the current period.

    total_count_current, current_errors_per_category = calculate_category_percentage(start_date, end_date)
    total_previous_count, previous_errors_per_cateogory = calculate_category_percentage(previous_start_date, previous_end_date)
    print("prev",previous_errors_per_cateogory)
    print("check",current_errors_per_category)
    final_results = []
    for item, entry, previous in zip(results_current, current_errors_per_category,previous_errors_per_cateogory):
        category_code = entry['_id']
        error_count = entry['error_count']
        error_percentage = (error_count / total_count_current * 100.0) if total_count_current else 0
        error_previous_count = previous['error_count']
        error_percentage_previous = (error_previous_count / total_previous_count * 100.0) if total_previous_count else 0


        # Fetch category details based on category_code if needed, e.g., name
        category = Category.objects(name=category_code).first()
        category_name = category.name if category else "Unknown Category"
        category = item['_id']  # As _id is grouped by category_code
        total_errors = item['total_errors']
        for violation in item['top_violations']:  # Iterate over each violation
            violation_code = violation['violation_code']
            count = violation['count']
            description = get_error_descriptions(violation_code)
            # Assuming category_details join gives you description directly)

            # Calculate percentage
            category_obj = Category.objects(name=category).first()
            if category_obj:
                total_count = len(category_obj.error_codes)
                print("code", total_count, count)
            else:
                print("Category not found")
            # percentage_current = (total_count / count  * 100) if total_count > 0 else 0

            # Find corresponding previous period data
            corresponding_previous = next((prev for prev in results_previous if prev['_id'] == item['_id']), None)
            # previous_count = corresponding_previous.get('count', 0) if corresponding_previous else 0
            # percentage_previous = (
            #             previous_count / total_count * 100) if total_count > 0 and corresponding_previous else 0

            # Append final results
            final_results.append({
                "category": category,
                "violation_code": violation_code,
                "description": description,
                "current_period_count": count,
                "current_period_percentage":round(error_percentage, 2),
                # "current_period_percentage": round(percentage_current, 2),
                "previous_period_precent": round(error_percentage_previous,2)
                # "previous_period_percentage": round(percentage_previous, 2)
            })
    return final_results


def audited_data_for_technicians_region_wise(start_date, end_date):
    pipeline = [
        {
            "$match": {
                "createdDate": {"$gte": start_date, "$lte": end_date},
                "status": "Approved",
                "region": {"$in": ["DUBAI", "ABU DHABI", "WR", "NORTHERN EMIRATES"]}
            }
        },
        {"$unwind": "$ceqvs"},
        {
            "$match": {
                "ceqvs.violation_code": "CEQV27"
            }
        },
        {
            "$group": {
                "_id": {
                    "region": "$region",
                    "compliance_status": {
                        "$cond": {
                            "if": {"$eq": ["$ceqvs.violation_type", True]},
                            "then": "Non-Compliance",
                            "else": "Compliance"
                        }
                    }
                },
                "count": {"$sum": 1}
            }
        },
        {
            "$group": {
                "_id": "$_id.region",
                "details": {
                    "$push": {
                        "type": "$_id.compliance_status",
                        "count": "$count"
                    }
                }
            }
        },
        {
            "$project": {
                "region": "$_id",
                "compliance_details": "$details",
                "_id": 0
            }
        }
    ]

    results = list(AuditData.objects.aggregate(pipeline))
    return results



def get_images_data(start_date, end_date, region):
    pipeline = [
        {"$match": {
            "createdDate": {"$gte": start_date, "$lte": end_date},
            "status": "Approved",
            "region": {"$exists": ""} if region is None else region
        }},
        {"$unwind": "$ceqvs"},
        {"$match": {
            "ceqvs.violation_type": {"$exists": True},
            "ceqvs.image": {"$ne": ""},
            "ceqvs.remarks": {"$ne" : ""}
        }},
        {
            "$group": {
                "_id": "$ceqvs.violation_type",
                "top_images": {
                    "$push": {
                        "image_url": "$ceqvs.image",
                        "remark": "$ceqvs.remarks"
                    }
            }
            }
        },
        {
            "$project": {
                "top_images": {"$slice": ["$top_images", 2]}  # MongoDB 3.4 supports $slice
            }
        }
    ]

    results = list(AuditData.objects.aggregate(pipeline))
    print(results)
    # Format results into more readable format
    formatted_results = {}
    for item in results:
        key = 'Compliance' if not item['_id'] else 'Non_Compliance'
        formatted_results[key] = item['top_images']

    return formatted_results



def last_six_month_category_non_compliance(start_date, end_date):
    categories = ["Tools & Devices", "Vehicles", "Technicians Appearance","Personal Behavior","Field Work Standards","Processes & Policies"]

    pipeline_last_7_months = [
        {
            "$match": {
                "createdDate": {"$gte": start_date, "$lte": end_date},
                "ceqvs.category_code": {"$in": categories}
            }
        },
        {"$unwind": "$ceqvs"},
        {"$match": {"ceqvs.violation_type": True}},
        {
            "$group": {
                "_id": {
                    "category_code": "$ceqvs.category_code",
                    "violation_code": "$ceqvs.violation_code",
                    "month": {"$dateToString": {"format": "%Y-%m", "date": "$createdDate"}}
                },
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"_id.month": 1, "count": -1}},
        {
            "$group": {
                "_id": {
                    "category_code": "$_id.category_code",
                    "month": "$_id.month"
                },
                "total_errors": {"$sum": "$count"},
                "top_violations": {
                    "$push": {
                        "violation_code": "$_id.violation_code",
                        "count": "$count"
                    }
                }
            }
        },
        {"$project": {
            "category": "$_id.category_code",
            "month": "$_id.month",
            "total_errors": 1,
            "top_violations": {"$slice": ["$top_violations", 2]}
        }},
        {"$sort": {"_id.month": 1}}
    ]
    # Print the results
    results = AuditData.objects.aggregate(pipeline_last_7_months)

    # Print the results
    formatted_results = []
    for result in results:
        formatted_results.append({
            "month": result["month"],
            "category": result["category"],
            "total_errors": result["total_errors"],
            "top_violations": result["top_violations"]
        })
    return formatted_results

