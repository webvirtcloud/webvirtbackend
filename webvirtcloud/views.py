from http import HTTPStatus
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def payload_response():
    return {
        "message": "",
        "status_code": 0,
    }


def success_message_reponse(message):
    status_code = status.HTTP_200_OK
    success_payload = {
        "message": message,
        "status_code": status_code,
    }
    return Response(success_payload, status=status_code)


def custom_exception(message):
    status_code = status.HTTP_400_BAD_REQUEST
    error_payload = {
        "message": message,
        "status_code": status_code,
    }
    return Response(error_payload, status=status_code)


def custom_exception_handler(exc, context):
    error_message = None
    response = exception_handler(exc, context)

    if response is not None:
        error_fileds = []
        error_payload = {
            "message": "",
            "status_code": 0,
        }
        status_code = response.status_code
        non_field_error = response.data.get(settings.REST_FRAMEWORK.get("NON_FIELD_ERRORS_KEY"))

        if non_field_error:
            error_message = non_field_error[0]

        if not error_message:
            for key, value in response.data.items():
                error_fileds.append({"message": value[0], "field": key})
            error_payload["errors"] = error_fileds
            error_message = HTTPStatus(status_code).description

        error_payload["message"] = error_message
        error_payload["status_code"] = status_code
        response.data = error_payload
    return response
