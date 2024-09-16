from rest_framework import status # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from .models import UploadedFile
from .serializers import UploadedFileSerializer

class FileUploadView(APIView):
    # POST request to upload a file
    def post(self, request, *args, **kwargs):
        file_serializer = UploadedFileSerializer(data=request.data, context={'request': request})
        
        if file_serializer.is_valid():
            file_serializer.save()
            return Response(file_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
