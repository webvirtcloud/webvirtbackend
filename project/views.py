from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Project
from .serializers import ProjectSerializer


class ProjectDefaultAPI(APIView):
    class_serializer = ProjectSerializer

    def get(self, request, *args, **kwargs):
        projects = Project.objects.get(user=request.user, is_default=True, is_deleted=False)
        serilizator = self.class_serializer(projects, many=False)
        return Response({'project': serilizator.data})


class ProjectListAPI(APIView):
    class_serializer = ProjectSerializer

    def get(self, request, *args, **kwargs):
        projects = Project.objects.filter(user=request.user, is_deleted=False)
        serilizator = self.class_serializer(projects, many=True)
        return Response({'projects': serilizator.data})
