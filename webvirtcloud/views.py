from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    error_message = None
    response = exception_handler(exc, context)

    if response is not None:
        if response.status_code == 400:
            if response.data.get('detail'):
                error_message = {'error': response.data.get('detail')}

            if response.data.get('non_field_errors'):
                if len(response.data.get('non_field_errors')) == 1:
                    errors = response.data.get('non_field_errors')[0]
                else:
                    for index, error in enumerate(response.data.get('non_field_errors')):
                        if index != len(my_list) - 1:
                            errors += error + ' '
                        else:
                            errors += error
                error_message = {'error': errors}

        if response.status_code == 401:
            error_message = {'error': 'Unable to authenticate you.'}

        if response.status_code == 403:
            error_message = {'error': 'The resource you were accessing is forbidden.'}

        if response.status_code == 404:
            error_message = {'error': 'The resource you were accessing could not be found.'}

        if response.status_code == 405:
            error_message = {'error': 'Current method not allowed.'}

        if response.status_code == 406:
            error_message = {'error': 'Could not satisfy the request accept header.'}

        if response.status_code == 408:
            error_message = {'error': 'The server timed out waiting for the request.'}

        if response.status_code == 415:
            error_message = {'error': 'Unsupported media type in request.'}

        if error_message:
            response.data = error_message

    return response
