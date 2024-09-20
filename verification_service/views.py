from rest_framework import status # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from .models import UploadedFile, UserProfile
from .serializers import UploadedFileSerializer
from .services import DataExtractionService
from .forms import UploadForm
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import json
import logging  

@api_view(['GET'])
@csrf_exempt
def get_csrf_token(request):
    token = get_token(request)
    return Response({'csrfToken': token}, status=status.HTTP_200_OK)

class FileUploadView(APIView):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        form = UploadForm(request.POST, request.FILES)

        if form.is_valid():
            file = request.FILES.get('file')
            image = request.FILES.get('image_file')

            if not file:
                return Response({"error": "No file uploaded", "message": "Pls Attach your File"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not image:
                return Response({"error": "No image uploaded", "message": "Pls Attach your Image"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not UserProfile.objects.filter(murugo_user_id=form.cleaned_data['murugo_user_id']).exists():
                UserProfile.objects.create(
                    murugo_user_id=form.cleaned_data['murugo_user_id'],
                    firstname=form.cleaned_data['firstname'],
                    secondname=form.cleaned_data['secondname'],
                    email=form.cleaned_data['email'],
                    personalid=form.cleaned_data['personalid'],
                    address=form.cleaned_data['address'],
                    city=form.cleaned_data['city'],
                    dob=form.cleaned_data['dob'],
                    countryCode=form.cleaned_data['countryCode'],
                    country=form.cleaned_data['country'],
                    phoneNumber=form.cleaned_data['phoneNumber'],
                    id_type=form.cleaned_data['id_type']
                )
            
            user_profile = UserProfile.objects.get(murugo_user_id=form.cleaned_data['murugo_user_id'])

            # Calculate file hash to check for duplicates
            temp_file = UploadedFile(file=file)
            file_hash = temp_file.calculate_file_hash()

            # Check if a file with the same hash already exists and return it
            existing_file = UploadedFile.objects.filter(file_hash=file_hash).first()
            
            if existing_file:
                serializer = UploadedFileSerializer(existing_file, context={'request': request})

                if existing_file.extracted_data:
                    # Format the response to include extracted data in real JSON format
                    response_data = serializer.data
                    response_data['extracted_data'] = json.dumps(json.loads(existing_file.extracted_data), indent=4)
                else:
                    # Extract data from the uploaded file
                    extracted_data = DataExtractionService.extractData(existing_file.file.path)

                    # Log the extracted data for debugging
                    logging.debug(f"Extracted data (raw): {extracted_data}")

                    # Clean up the extracted data by removing unwanted characters
                    cleaned_data_str = extracted_data.strip().replace("```json\n", "").replace("```", "")

                    logging.debug(f"Cleaned extracted data: {cleaned_data_str}")

                    # Store extracted data in the database with the file record
                    existing_file.extracted_data = cleaned_data_str
                    existing_file.save()

                    # Format the response to include extracted data in real JSON format
                    response_data = serializer.data
                    response_data['extracted_data'] = json.dumps(json.loads(existing_file.extracted_data), indent=4)
                    
                return Response(response_data, status=status.HTTP_200_OK)
            
            # File does not exist, proceed to save the new file
            file_serializer = UploadedFileSerializer(data=request.data, context={'request': request})
            
            if file_serializer.is_valid():
                # Save the uploaded file to the database
                uploaded_file = file_serializer.save(user=user_profile)

                # Ensure the file is saved
                uploaded_file.refresh_from_db()

                # Ensure file is available and handle extraction
                if uploaded_file.file:
                    if not uploaded_file.extracted_data:
                        print(f"Extracting data from file: {uploaded_file}")

                        # Extract data from the uploaded file
                        extracted_data = DataExtractionService.extractData(uploaded_file.file.path)

                        # Log the extracted data for debugging
                        logging.debug(f"Extracted data (raw): {extracted_data}")

                        # Clean up the extracted data by removing unwanted characters
                        cleaned_data_str = extracted_data.strip().replace("```json\n", "").replace("```", "")

                        logging.debug(f"Cleaned extracted data: {cleaned_data_str}")

                        # Store extracted data in the database with the file record
                        uploaded_file.extracted_data = cleaned_data_str
                        uploaded_file.save()
                    else:
                        # File already processed
                        extracted_data = uploaded_file.extracted_data
                else:
                    return Response({"error": "File not found"}, status=status.HTTP_400_BAD_REQUEST)

                # Format the response to include extracted data in real JSON format
                response_data = file_serializer.data
                response_data['extracted_data'] = json.dumps(json.loads(uploaded_file.extracted_data), indent=4)
                response_data['message'] = "File & Identity Created successfully"

                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"message": "Form validation error", "errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)
