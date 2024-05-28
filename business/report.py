from ceq_user.database.models import BusinessAudit
from datetime import datetime, timedelta


def compliance_business_check(start_date, end_date):
    # List of regions to check
    regions = ['auh', 'dxb', 'ne']

    pipeline = [
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date}
            }
        },
        {
            '$project': {
                'region': {'$toLower': '$region'},
                'ceqv01_sub_cable_inst': 1,
                'ceqvo2_sub_inst_ont': 1,
                'ceqv03_sub_inst_wastes_left_uncleaned': 1,
                'ceqv04_existing_sub_inst_not_rectified': 1,
                'ceqv05_sub_inst_cpe': 1,
                'ceqv06_sub_labelling': 1
            }
        },
        {
            '$match': {
                'region': {'$in': regions}
            }
        },
        {
            '$project': {
                'region': 1,
                'compliance_status': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$eq': ['$ceqv01_sub_cable_inst', 'NO']},
                                {'$eq': ['$ceqvo2_sub_inst_ont', 'NO']},
                                {'$eq': ['$ceqv03_sub_inst_wastes_left_uncleaned', 'NO']},
                                {'$eq': ['$ceqv04_existing_sub_inst_not_rectified', 'NO']},
                                {'$eq': ['$ceqv05_sub_inst_cpe', 'NO']},
                                {'$eq': ['$ceqv06_sub_labelling', 'NO']}
                            ]
                        },
                        'then': 'Compliance',
                        'else': 'Non-Compliance'
                    }
                }
            }
        },
        {
            '$group': {
                '_id': {
                    'region': '$region',
                    'compliance_status': '$compliance_status'
                },
                'count': {'$sum': 1}
            }
        },
        {
            '$group': {
                '_id': '$_id.region',
                'compliance_details': {
                    '$push': {
                        'type': '$_id.compliance_status',
                        'count': '$count'
                    }
                }
            }
        },
        {
            '$project': {
                'region': '$_id',
                'compliance_details': 1,
                '_id': 0
            }
        }
    ]

    results = list(BusinessAudit.objects.aggregate(pipeline))
    return results


def count_error_codes(start_date, end_date):
    pipeline = [
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date}
            }
        },
        {
            '$group': {
                '_id': None,  # We don't need to group by a specific field, we're counting each error independently
                'ceqvo2_sub_inst_ont_count': {
                    '$sum': {
                        '$cond': [{ '$eq': ['$ceqvo2_sub_inst_ont', 'YES'] }, 1, 0]
                    }
                },
                'ceqv03_sub_inst_wastes_left_uncleaned_count': {
                    '$sum': {
                        '$cond': [{ '$eq': ['$ceqv03_sub_inst_wastes_left_uncleaned', 'YES'] }, 1, 0]
                    }
                },
                'ceqv04_existing_sub_inst_not_rectified_count': {
                    '$sum': {
                        '$cond': [{ '$eq': ['$ceqv04_existing_sub_inst_not_rectified', 'YES'] }, 1, 0]
                    }
                },
                'ceqv05_sub_inst_cpe_count': {
                    '$sum': {
                        '$cond': [{ '$eq': ['$ceqv05_sub_inst_cpe', 'YES'] }, 1, 0]
                    }
                },
                'ceqv06_sub_labelling_count': {
                    '$sum': {
                        '$cond': [{ '$eq': ['$ceqv06_sub_labelling', 'YES'] }, 1, 0]
                    }
                }
            }
        },
        {
            '$project': {
                '_id': 0,
                'ceqv01_sub_cable_inst':1,
                'ceqv02_sub_inst_ont_count': 1,
                'ceqv03_sub_inst_wastes_left_uncleaned_count': 1,
                'ceqv04_existing_sub_inst_not_rectified_count': 1,
                'ceqv05_sub_inst_cpe_count': 1,
                'ceqv06_sub_labelling_count': 1
            }
        }
    ]

    result = list(BusinessAudit.objects.aggregate(pipeline))
    return result[0] if result else {}


def overall_compliance_check(start_date, end_date):
    pipeline = [
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date}
            }
        },
        {
            '$project': {
                'region': {'$toLower': '$region'},
                'compliance_status': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$eq': ['$ceqv01_sub_cable_inst', 'NO']},
                                {'$eq': ['$ceqvo2_sub_inst_ont', 'NO']},
                                {'$eq': ['$ceqv03_sub_inst_wastes_left_uncleaned', 'NO']},
                                {'$eq': ['$ceqv04_existing_sub_inst_not_rectified', 'NO']},
                                {'$eq': ['$ceqv05_sub_inst_cpe', 'NO']},
                                {'$eq': ['$ceqv06_sub_labelling', 'NO']}
                            ]
                        },
                        'then': 'Compliance',
                        'else': 'Non-Compliance'
                    }
                }
            }
        },
        {
            '$group': {
                '_id': '$compliance_status',
                'count': {'$sum': 1}
            }
        }
    ]

    result = list(BusinessAudit.objects.aggregate(pipeline))

    compliance_result = {item['_id']: item['count'] for item in result}
    compliance_result.setdefault('Compliance', 0)
    compliance_result.setdefault('Non-Compliance', 0)
    return compliance_result


def calculate_account_category_percentages(start_date, end_date):
    # Pipeline to calculate total audits and audits per account_category
    pipeline_total_and_category_counts = [
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date}
            }
        },
        {
            '$group': {
                '_id': None,
                'total_audits': {'$sum': 1},
                'categories': {
                    '$push': '$account_category'
                }
            }
        },
        {
            '$unwind': '$categories'
        },
        {
            '$group': {
                '_id': {'category': '$categories'},
                'count': {'$sum': 1},
                'totalAudits': {'$first': '$total_audits'}
            }
        },
        {
            '$project': {
                'account_category': '$_id.category',
                'count': 1,
                'percentage': {
                    '$floor': {
                        '$multiply': [
                            {'$divide': ['$count', '$totalAudits']},
                            100
                        ]
                    }
                }
            }
        }
    ]

    results = list(BusinessAudit.objects.aggregate(pipeline_total_and_category_counts))
    return results


def calculate_monthly_compliance(start_date, end_date):
    pipeline = [
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date}
            }
        },
        {
            '$project': {
                'yearMonth': {
                    '$dateToString': {
                        'format': '%Y-%m',
                        'date': '$date_of_visit'
                    }
                },
                'region': {'$toLower': '$region'},
                'compliance_status': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$eq': ['$ceqv01_sub_cable_inst', 'NO']},
                                {'$eq': ['$ceqvo2_sub_inst_ont', 'NO']},
                                {'$eq': ['$ceqv03_sub_inst_wastes_left_uncleaned', 'NO']},
                                {'$eq': ['$ceqv04_existing_sub_inst_not_rectified', 'NO']},
                                {'$eq': ['$ceqv05_sub_inst_cpe', 'NO']},
                                {'$eq': ['$ceqv06_sub_labelling', 'NO']}
                            ]
                        },
                        'then': 'Compliance',
                        'else': 'Non-Compliance'
                    }
                }
            }
        },
        {
            '$group': {
                '_id': {
                    'yearMonth': '$yearMonth',
                    'region': '$region',
                    'compliance_status': '$compliance_status'
                },
                'count': {'$sum': 1}
            }
        },
        {
            '$group': {
                '_id': {
                    'yearMonth': '$_id.yearMonth',
                    'region': '$_id.region'
                },
                'compliance_total': {
                    '$sum': {
                        '$cond': [
                            {'$eq': ['$_id.compliance_status', 'Compliance']},
                            '$count',
                            0
                        ]
                    }
                },
                'total_audits': {'$sum': '$count'}
            }
        },
        {
            '$project': {
                'yearMonth': '$_id.yearMonth',
                'region': '$_id.region',
                'compliance_percentage': {
                    '$floor': {
                        '$multiply': [
                            {'$divide': ['$compliance_total', '$total_audits']},
                            100
                        ]
                    }
                }
            }
        },
        {'$sort': {'yearMonth': 1, 'region': 1}}  # Optional: sort by date and region for readability
    ]

    results = list(BusinessAudit.objects.aggregate(pipeline))
    return results


def count_error_codes_monthwise(start_date, end_date):
    # Calculate six months before the start_date
    six_months_ago = start_date - timedelta(days=6*30)

    pipeline = [
        {
            '$match': {
                'date_of_visit': {'$gte': six_months_ago, '$lte': end_date}
            }
        },
        {
            '$project': {
                'yearMonth': {
                    '$dateToString': {
                        'format': '%Y-%m',
                        'date': '$date_of_visit'
                    }
                },
                'ceqv01_sub_cable_inst': 1,
                'ceqvo2_sub_inst_ont': 1,
                'ceqv03_sub_inst_wastes_left_uncleaned': 1,
                'ceqv04_existing_sub_inst_not_rectified': 1,
                'ceqv05_sub_inst_cpe': 1,
                'ceqv06_sub_labelling': 1
            }
        },
        {
            '$group': {
                '_id': '$yearMonth',
                'ceqv01_sub_cable_inst_count': {
                    '$sum': {'$cond': [{'$eq': ['$ceqv01_sub_cable_inst', 'YES']}, 1, 0]}
                },
                'ceqvo2_sub_inst_ont_count': {
                    '$sum': {'$cond': [{'$eq': ['$ceqvo2_sub_inst_ont', 'YES']}, 1, 0]}
                },
                'ceqv03_sub_inst_wastes_left_uncleaned_count': {
                    '$sum': {'$cond': [{'$eq': ['$ceqv03_sub_inst_wastes_left_uncleaned', 'YES']}, 1, 0]}
                },
                'ceqv04_existing_sub_inst_not_rectified_count': {
                    '$sum': {'$cond': [{'$eq': ['$ceqv04_existing_sub_inst_not_rectified', 'YES']}, 1, 0]}
                },
                'ceqv05_sub_inst_cpe_count': {
                    '$sum': {'$cond': [{'$eq': ['$ceqv05_sub_inst_cpe', 'YES']}, 1, 0]}
                },
                'ceqv06_sub_labelling_count': {
                    '$sum': {'$cond': [{'$eq': ['$ceqv06_sub_labelling', 'YES']}, 1, 0]}
                }
            }
        },
        {
            '$sort': {'_id': 1}  # Sort by yearMonth in ascending order
        },
        {
            '$project': {
                '_id': 0,
                'yearMonth': '$_id',
                'ceqv01_sub_cable_inst': 1,
                'ceqv02_sub_inst_ont_count': 1,
                'ceqv03_sub_inst_wastes_left_uncleaned_count': 1,
                'ceqv04_existing_sub_inst_not_rectified_count': 1,
                'ceqv05_sub_inst_cpe_count': 1,
                'ceqv06_sub_labelling_count': 1
            }
        }
    ]

    result = list(BusinessAudit.objects.aggregate(pipeline))
    return result


def business_name_with_non_compliance(start_date, end_date):
    # Calculate six months before the start_date
    pipeline = [
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date},
                '$or': [
                    {'ceqv01_sub_cable_inst': 'YES'},
                    {'ceqvo2_sub_inst_ont': 'YES'},
                    {'ceqv03_sub_inst_wastes_left_uncleaned': 'YES'},
                    {'ceqv04_existing_sub_inst_not_rectified': 'YES'},
                    {'ceqv05_sub_inst_cpe': 'YES'},
                    {'ceqv06_sub_labelling': 'YES'}
                ]
            }
        },
        {
            '$project': {
                '_id': 0,
                'customer_name': 1
            }
        }
    ]

    result = list(BusinessAudit.objects.aggregate(pipeline))
    return [doc['customer_name'] for doc in result]


def get_images_with_compliance(start_date, end_date):
    pipeline = [
        # Match documents within the specified date range and with 'Approved' status
        {
            '$match': {
                'date_of_visit': {'$gte': start_date, '$lte': end_date},
                'status': 'Approved'
            }
        },
        # Project necessary fields and determine compliance status
        {
            '$project': {
                'product_type': 1,
                'violation_remarks': 1,
                'images': {
                    '$filter': {
                        'input': ['$photo1', '$photo2', '$photo3', '$photo4', '$photo5', '$photo6'],
                        'as': 'photo',
                        'cond': {'$ne': ['$$photo', '']}
                    }
                },
                'compliance_status': {
                    '$cond': {
                        'if': {
                            '$and': [
                                {'$eq': ['$ceqv01_sub_cable_inst', 'NO']},
                                {'$eq': ['$ceqvo2_sub_inst_ont', 'NO']},
                                {'$eq': ['$ceqv03_sub_inst_wastes_left_uncleaned', 'NO']},
                                {'$eq': ['$ceqv04_existing_sub_inst_not_rectified', 'NO']},
                                {'$eq': ['$ceqv05_sub_inst_cpe', 'NO']},
                                {'$eq': ['$ceqv06_sub_labelling', 'NO']}
                            ]
                        },
                        'then': 'Compliance',
                        'else': 'Non-Compliance'
                    }
                }
            }
        },
        # Filter documents based on image presence
        {
            '$match': {
                'images': {'$ne': []}
            }
        },
        # Split the documents into compliance and non-compliance facets and limit to 2 documents per facet
        {
            '$facet': {
                'Compliance': [
                    {'$match': {'compliance_status': 'Compliance'}},
                    {'$limit': 2}
                ],
                'Non-Compliance': [
                    {'$match': {'compliance_status': 'Non-Compliance'}},
                    {'$limit': 2}
                ]
            }
        },
        # Unwind facets and project final output
        {
            '$project': {
                'Compliance': {
                    '$map': {
                        'input': '$Compliance',
                        'as': 'compliance_doc',
                        'in': {
                            'product_type': '$$compliance_doc.product_type',
                            'violation_remarks': '$$compliance_doc.violation_remarks',
                            'images': '$$compliance_doc.images'
                        }
                    }
                },
                'Non-Compliance': {
                    '$map': {
                        'input': '$Non-Compliance',
                        'as': 'non_compliance_doc',
                        'in': {
                            'product_type': '$$non_compliance_doc.product_type',
                            'violation_remarks': '$$non_compliance_doc.violation_remarks',
                            'images': '$$non_compliance_doc.images'
                        }
                    }
                }
            }
        }
    ]

    results = list(BusinessAudit.objects.aggregate(pipeline))
    return results[0] if results else {}




