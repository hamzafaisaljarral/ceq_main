from flask import request, jsonify
from ceq_user.database.models import User
from mongoengine import DoesNotExist


def update_user(user_id, role, supervisor):
    try:
        user = User.objects.get(id=user_id)
        role = request.json.get('role')
        supervisor = request.json.get('supervisor')
        user.update(role=role)
    except DoesNotExist:
        return jsonify(message="User not found"), 404
    return jsonify(message="User updated"), 200