from rest_framework import permissions


class IsAuthenticatedAndVerified(permissions.BasePermission):
    message = ""

    def has_permission(self, request, view):
        if request.user.is_authenticated:
            if request.user.is_email_verified is False:
                self.message = "Please confirm your email address."
                return False

            if (
                request.method == "PUT"
                or request.method == "POST"
                or request.method == "PATCH"
                or request.method == "DELETE"
            ):
                if request.user.is_verified is False:
                    self.message = "Please verify your account"
                    return False

                if request.auth.scope == request.auth.READ_SCOPE:
                    self.message = "You do not have permission to write."
                    return False

            return True

        return False
