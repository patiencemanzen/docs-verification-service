from rest_framework import status # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from .services import DataExtractionService
from .forms import UploadForm
from django.middleware.csrf import get_token # type: ignore
from rest_framework.decorators import api_view # type: ignore
from django.views.decorators.csrf import csrf_exempt # type: ignore

from googleapiclient.errors import HttpError # type: ignore
from google.api_core.exceptions import InternalServerError # type: ignore

from .tasks import extract_data_task
import redis # type: ignore
from rq import Queue # type: ignore

import logging
import traceback

from rq import Retry # type: ignore
from datetime import timedelta

logger = logging.getLogger(__name__)
import redis # type: ignore

redis_conn = redis.Redis()
q = Queue(connection=redis_conn)

@api_view(['GET'])
@csrf_exempt
def get_csrf_token(request):
    token = get_token(request)
    return Response({'csrfToken': token}, status=status.HTTP_200_OK)

class FileUploadView(APIView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        try:
            form = UploadForm(request.POST, request.FILES)

            if form.is_valid():
                file = request.FILES.get('file')
                image = request.FILES.get('image_file')

                if not file:
                    return Response({"message": "No file uploaded", "message": "Pls Attach your File"}, status=status.HTTP_400_BAD_REQUEST)
                
                if not image:
                    return Response({"message": "No image uploaded", "message": "Pls Attach your Image"}, status=status.HTTP_400_BAD_REQUEST)

                # Calculate file hash to check for duplicates
                temp_file = UploadedFile(file=file)
                file_hash = temp_file.calculate_file_hash()

                # Check if a file with the same hash already exists and return it
                existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
                
                if existing_file:
                    serializer = UploadedFileSerializer(existing_file, data=request.data, partial=True, context={'request': request})

                    if serializer.is_valid():
                        serializer.save()
                    
                        # Queue the data extraction task
                        extract_data_task.delay(existing_file.id, {'firstname': form.cleaned_data['firstname'], 'secondname': form.cleaned_data['secondname'], 'email': form.cleaned_data['email'], 'personalid': form.cleaned_data['personalid'], 'address': form.cleaned_data['address'], 'city': form.cleaned_data['city'], 'dob': form.cleaned_data['dob'], 'countryCode': form.cleaned_data['countryCode'], 'country': form.cleaned_data['country'], 'phoneNumber': form.cleaned_data['phoneNumber']}, murugo_user_id=form.cleaned_data['murugo_user_id'])
                        
                        return Response({ "message": "Data processing started"}, status=status.HTTP_200_OK)
                    else:
                        return Response({ "message": "Unable to Update Data"}, status=status.HTTP_400_BAD_REQUEST)
                
                # File does not exist, proceed to save the new file
                file_serializer = UploadedFileSerializer(data=request.data, context={'request': request})
                
                if file_serializer.is_valid():
                    # Save the uploaded file to the database
                    uploaded_file = file_serializer.save()

                    # Ensure the file is saved
                    uploaded_file.refresh_from_db()

                    # Ensure file is available and handle extraction
                    if uploaded_file.file:
                        if not uploaded_file.extracted_data or uploaded_file.extracted_data.strip() == "":
                            print(f"Extracting data from file: {uploaded_file}")

                            try:
                                # Queue the data extraction task
                                extract_data_task.delay(uploaded_file.id, {'firstname': form.cleaned_data['firstname'], 'secondname': form.cleaned_data['secondname'], 'email': form.cleaned_data['email'], 'personalid': form.cleaned_data['personalid'], 'address': form.cleaned_data['address'], 'city': form.cleaned_data['city'], 'dob': form.cleaned_data['dob'], 'countryCode': form.cleaned_data['countryCode'], 'country': form.cleaned_data['country'], 'phoneNumber': form.cleaned_data['phoneNumber']}, murugo_user_id=form.cleaned_data['murugo_user_id'])
                                return Response({"message": "File & Identity Created successfully"}, status=status.HTTP_201_CREATED)
                            except Exception as e:
                                return Response({"message": "Error during data extraction"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                        else:
                            # File already processed
                            extracted_data = uploaded_file.extracted_data
                            DataExtractionService.send_callback_to_custom_api(extracted_data)
                            return Response({"message": "File & Identity Created successfully"}, status=status.HTTP_201_CREATED)
                    else:
                        return Response({"message": "File not found"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"message": "Form validation error", "errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error during file upload: {e}")
            logger.error(traceback.format_exc())
            
            return Response({ "message": f"An error occurred during file upload: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)