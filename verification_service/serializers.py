from rest_framework import serializers # type: ignore
from .models import UploadedFile
from django.conf import settings # type: ignore

class UploadedFileSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = UploadedFile
        fields = ['id', 'file_url', 'file', 'uploaded_at', 'extracted_data']

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
            # Log or print details for debugging
            print(f"Found existing file: {existing_file.id}")
            return existing_file
        else:
            # Log or print details for debugging
            print("Creating new file entry.")
            return super().create(validated_data)

