from django.db import models # type: ignore
from datetime import datetime
import os
import hashlib

DEFAULT_USER_ID = 1

# Function to upload the uploaded ID file
def upload_id_file(instance, filename):
    extension = filename.split('.')[-1]
    new_filename = f"murugo_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    return os.path.join('upload_ID_files/', new_filename)

# Function to upload the uploaded image file
def upload_image_file(instance, filename):
    extension = filename.split('.')[-1]
    new_filename = f"murugo_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    return os.path.join('uploaded_image_files/', new_filename)

class UserProfile(models.Model):
    murugo_user_id = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100)
    secondname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=100)
    personalid = models.CharField(max_length=100, unique=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    dob = models.DateField()
    countryCode = models.CharField(max_length=10)
    country = models.CharField(max_length=100)
    phoneNumber = models.CharField(max_length=15)
    id_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.firstname} {self.secondname} ({self.email})"
    
class UploadedFile(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='uploaded_files')
    file = models.FileField(upload_to=upload_id_file)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, null=True)
    image_file = models.FileField(upload_to=upload_image_file)
    extracted_data = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

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
    