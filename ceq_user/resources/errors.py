from flask import Response, jsonify

"""
proper error responses are mentioned and saved here

"""


def unauthorized() -> Response:
    output = {"error":
                  {"msg": "401 error: The email or password provided is invalid."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 401
    return resp


def forbidden() -> Response:
    output = {"error":
                  {"msg": "403 error: The current user is not authorized to take this action."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 403
    return resp


def invalid_route() -> Response:
    output = {"error":
                  {"msg": "404 error: This route is currently not supported. See API documentation."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 404
    return resp


def not_found() -> Response:
    output = {"error":
                  {"msg": "403 error: parameters are incorrect."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 403
    return resp


def user_exist() -> Response:
    output = {"error":
                  {"msg": "403 error: this email is already registered."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 403
    return


def ldap_issue() -> Response:
    output = {"error":
                  {"msg": "500 error: contact ldap support."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 500
    return resp


def save_issue() -> Response:
    output = {"error":
                  {"msg": "501 error: not able to save."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 501
    return resp


def saved() -> Response:
    output = {"success":
                  {"msg": "able to delete."}
              }
    resp = jsonify({'result': output})
    resp.status_code = 204
    return resp
