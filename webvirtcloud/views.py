from http import HTTPStatus
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def http_code_to_message(code):
    return HTTPStatus(code).description


def payload_response():
    return {
        "status": "error",
        "status_code": 0,
        "message": "",
        "data": [],
    }


def success_message_reponse(message):
    status_code = status.HTTP_200_OK
    success_payload = payload_response()
    success_payload["status"] = "success"
    success_payload["status_code"] = status_code
    success_payload["message"] = message
    return Response(success_payload, status=status_code)


def custom_exception(message):
    status_code = status.HTTP_400_BAD_REQUEST
    error_payload = payload_response()
    error_payload["status_code"] = status_code
    error_payload["message"] = http_code_to_message(status_code)
    error_payload["data"] = {settings.REST_FRAMEWORK['NON_FIELD_ERRORS_KEY']: [message]}
    return Response(error_payload, status=status_code)


def custom_exception_handler(exc, context):
    error_message = None
    response = exception_handler(exc, context)

    if response is not None:
        error_payload = payload_response()
        status_code = response.status_code  
        error_payload["status_code"] = status_code
        error_payload["message"] = http_code_to_message(status_code)
        error_payload["data"] = response.data
        response.data = error_payload
    return response
