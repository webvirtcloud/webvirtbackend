from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectSerializer


class ProjectDefaultAPI(APIView):
    class_serializer = ProjectSerializer

    def get_object(self, uuid):
        try:
            return Project.objects.get(user=user, is_default=True, is_deleted=False)
        except Snippet.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        projects = self.get_object(user=request.user)
        serilizator = self.class_serializer(projects, many=False)
        return Response({'project': serilizator.data})


class ProjectListAPI(APIView):
    class_serializer = ProjectSerializer

    def get(self, request, *args, **kwargs):
        projects = Project.objects.filter(user=request.user, is_deleted=False)
        serilizator = self.class_serializer(projects, many=True)
        return Response({'projects': serilizator.data})


class ProjectDataAPI(APIView):
    class_serializer = ProjectSerializer

    def get_object(self, uuid, user):
        try:
            return Project.objects.get(uuid=uuid, user=user)
        except Snippet.DoesNotExist:
            raise Http404

    def get(self, request, uuid, *args, **kwargs):
        project = self.get_object(uuid, request.user)
        serilizator = self.class_serializer(project, many=False)
        return Response({'project': serilizator.data})
