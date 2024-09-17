from django.db import models # type: ignore
from datetime import datetime
import os
import hashlib

# Function to rename the uploaded file
def rename_uploaded_file(instance, filename):
    extension = filename.split('.')[-1]
    new_filename = f"murugo_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    return os.path.join('uploads/', new_filename)

# Create your models here.
class UploadedFile(models.Model):
    file = models.FileField(upload_to=rename_uploaded_file)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_data = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"File {self.id} uploaded at {self.uploaded_at}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_hash = self.calculate_file_hash()

        super().save(*args, **kwargs)

    def calculate_file_hash(self):
        # Generate a hash of the file content
        file_hash = hashlib.sha256()

        for chunk in self.file.chunks():
            file_hash.update(chunk)
            
        return file_hash.hexdigest()
    