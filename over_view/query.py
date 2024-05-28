from ceq_user.database.models import AuditData


def get_audit_statistics(start_date, end_date):
    pipeline = [
        {"$match": {"createdDate": {"$gte": start_date, "$lte": end_date}, "status": {"$in": ["Approved", "Submitted", "Pending", "Rejected", "Reverted"]}}},
        {"$group": {
            "_id": {
                "$switch": {
                    "branches": [
                        {"case": {"$eq": ["$status", "Approved"]}, "then": "Approved"},
                        {"case": {"$in": ["$status", ["Rejected", "Reverted"]]}, "then": "Reverted/Rejected"},
                        {"case": {"$in": ["$status", ["Submitted", "Pending"]]}, "then": "Submitted/Pending"}
                    ],
                    "default": "Other"
                }
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