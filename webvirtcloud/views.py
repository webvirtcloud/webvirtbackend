from http import HTTPStatus
from django.conf import settings
from django.http import JsonResponse
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

        if isinstance(response.data, dict):
            detail_error = response.data.get("detail")
            non_field_error = response.data.get("non_field_errors")

            if detail_error:
                error_message = detail_error

            if non_field_error:
                error_message = non_field_error[0]

        if isinstance(response.data, list):
            error_message = response.data[0]

        if not error_message:
            for key, value in response.data.items():
                error_fileds.append({"message": value[0], "field": key})
            error_payload["errors"] = error_fileds
            error_message = HTTPStatus(status_code).description

        error_payload["message"] = error_message
        error_payload["status_code"] = status_code
        response.data = error_payload
    return response


def custom_handler404(request, exception):
    status_code = 404
    response = JsonResponse(
        {
            "status_code": status_code,
            "message": "The resource you were accessing could not be found.",
        },
        content_type="application/json",
        status=status_code,
    )
    return response


def custom_handler500(request):
    status_code = 500
    response = JsonResponse(
        {
            "status_code": status_code,
            "message": "The resource you were accessing got internal error.",
        },
        content_type="application/json",
        status=status_code,
    )
    return response
