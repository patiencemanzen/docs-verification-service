from rest_framework import serializers # type: ignore
from .models import UploadedFile, UserProfile
from django.conf import settings # type: ignore

class UploadedFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile

        fields = [
            'id', 
            'file', 
            'file_url',
            'image_file', 
            'extracted_data',
            'uploaded_at', 
        ]

    def get_file_url(self, obj):
        request = self.context.get('request')

        if request is not None and obj.file:
            return request.build_absolute_uri(obj.file.url)
        elif obj.file:
            return f"{settings.MEDIA_URL}{obj.file.url}"
        else:
            return None
    
    def create(self, validated_data):
        file_hash = validated_data.get('file_hash')
        existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            return existing_file
        else:
            return super().create(validated_data)

