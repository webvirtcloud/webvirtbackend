from http import HTTPStatus
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def http_code_to_message(code):
    return HTTPStatus(code).description


def error_payload_response():
    return {
        "error": {
            "status_code": 0,
            "message": "",
            "details": [],
        }
    }

def custom_exception(message):
    status_code = 400
    error_payload = error_payload_response()
    error = error_payload["error"]
    error["status_code"] = status_code
    error["message"] = http_code_to_message(status_code)
    error["details"] = {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [message]}
    return Response(error_payload, status=status.HTTP_400_BAD_REQUEST)

def custom_exception_handler(exc, context):
    error_message = None
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = error_payload_response()
        error = error_payload["error"]
        status_code = response.status_code  
        error["status_code"] = status_code
        error["message"] = http_code_to_message(status_code)
        error["details"] = response.data
        response.data = error_payload
    return response
