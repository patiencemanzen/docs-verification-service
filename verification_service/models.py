from django.db import models # type: ignore
from datetime import datetime
import os

# Function to rename the uploaded file
def rename_uploaded_file(instance, filename):
    extension = filename.split('.')[-1]
    new_filename = f"murugo_file_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{extension}"
    return os.path.join('uploads/', new_filename)

# Create your models here.
class UploadedFile(models.Model):
    file = models.FileField(upload_to=rename_uploaded_file)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File {self.id} uploaded at {self.uploaded_at}"