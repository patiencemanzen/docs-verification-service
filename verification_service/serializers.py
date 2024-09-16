from rest_framework import serializers # type: ignore
from .models import UploadedFile
from django.conf import settings # type: ignore

class UploadedFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = ['id', 'file_url', 'file', 'uploaded_at']

    def get_file_url(self, obj):
        request = self.context.get('request')

        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        
        return f"{settings.MEDIA_URL}{obj.file.url}"
