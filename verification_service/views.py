from rest_framework import status # type: ignore
from rest_framework.response import Response # type: ignore
from rest_framework.views import APIView # type: ignore
from .models import UploadedFile
from .serializers import UploadedFileSerializer
from .services import DataExtractionService
import json
import logging  

class FileUploadView(APIView):
    # POST request to upload a file
    def post(self, request, *args, **kwargs):
        file = request.FILES.get('file')

        if not file:
            return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)
        
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
            uploaded_file = file_serializer.save()

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

            return Response(response_data, status=status.HTTP_201_CREATED)
        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
