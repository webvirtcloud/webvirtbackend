from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import KeyPair, KeyPairVirtance
from .serializers import KeyPairSerializer


class KeyPairListAPI(APIView):
    class_serializer = KeyPairSerializer

    def get_queryset(self):
        return KeyPair.objects.filter(user=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        List All Keypairs
        ---
        """
        serializer = self.class_serializer(self.get_queryset(), many=True)
        return Response({"keypairs": serializer.data})

    def post(self, request, *args, **kwargs):
        """
        Create a New Keypair
        ---
            parameters:
                - name: name
                  description: KeyPair name
                  required: true
                  type: string

                - name: public_key
                  description: Public key
                  required: true
                  type: string
        """
        serializer = self.class_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({"keypair": serializer.data}, status=status.HTTP_201_CREATED)


class KeyPairDataAPI(APIView):
    class_serializer = KeyPairSerializer

    def get_queryset(self):
        return get_object_or_404(KeyPair, pk=self.kwargs.get("pk"), user=self.request.user)

    def get(self, request, *args, **kwargs):
        """
        Retrieve an Existing Keypair
        ---
        """
        serializer = self.class_serializer(self.get_queryset(), many=False)
        return Response({"keypair": serializer.data})

    def put(self, request, *args, **kwargs):
        """
        Update the Keypair
        ---
            parameters:
                - name: name
                  description: KeyPair name
                  required: true
                  type: string
        """
        serializer = self.class_serializer(self.get_queryset(), data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({"keypair": serializer.data}, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Delete the Keypair
        ---
        """
        keypair = self.get_queryset()
        keypairvirtances = KeyPairVirtance.objects.filter(keypair=keypair)
        keypairvirtances.delete()
        keypair.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
