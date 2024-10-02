import os
import time
import google.generativeai as genai # type: ignore
from google.generativeai.types import HarmCategory, HarmBlockThreshold # type: ignore
from googleapiclient.errors import HttpError
import mimetypes
import logging

logger = logging.getLogger(__name__)
genai.configure(api_key="AIzaSyDstXHSVIdNxNmoPZfb-ToufV1Nv8fmzyI")

class GenFileDataExtractionService:
    # Initialize the service
    def __init__(self):
        print("Initializing Gen AI Model Chat Session...")

        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        model = genai.GenerativeModel(
            model_name="gemini-1.5-pro",
            generation_config=generation_config,
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE
            }
        )

        self.model = model
        self.prompt = self.genAiPrompt()

        print("Gen AI Model Chat Session initialized.")

    # Start a chat session with the model
    def initChatSession(self):
        print("Starting Fine Tuning...")

        # Fine Tune the model
        local_file_path = os.path.join(os.getcwd(), "verification_service", "model_test_files", "manirabona_patience_ID.pdf")
        local_image_path = os.path.join(os.getcwd(), "verification_service", "model_test_files", "manirabona_patience_photo.jpg")
        
        files = [
            self.uploadToGemini(local_file_path, mime_type="application/pdf"),
            self.uploadToGemini(local_image_path, mime_type="image/jpeg"),
        ]

        # Some files have a processing delay. Wait for them to be ready.
        self.waitForFilesActive(files)

        self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        files[0],
                        files[1],
                        self.prompt,
                    ],
                },
                {
                    "role": "model",
                    "parts": [
                        "```json\n{\n  \"full_names\": \"MANIRABONA Hirwa Patience\",\n  \"date_of_birth\": \"28/04/2002\",\n  \"address\": \"BUGESERA/NYAMATA\",\n  \"date_of_issuance\": null,\n  \"company_code\": null,\n  \"company_name\": null,\n  \"registration_date\": null,\n  \"owner_details\": null,\n  \"associated_identification_numbers\": null,\n  \"metadata\": {\n    \"document_type\": \"National Identity Card\",\n    \"country\": \"Rwanda\",\n    \"national_id_number\": \"1 2002 8 0028683 1 24\"\n  },\n  \"valid\": false,\n  \"face_matches\": null\n}\n```\nThe provided data is partially valid.\n\n- **Full Name:** Matches the information on the document.\n- **Date of Birth:** Matches the information on the document.\n- **Address:** The document provides a place of issue, which is \"BUGESERA/NYAMATA,\" while the submitted data does not include an address.\n- **Date of Issuance:** The provided data does not include a date of issuance.\n- **Company Code:** This is not applicable to the document.\n- **Company Name:** This is not applicable to the document.\n- **Registration Date:** This is not applicable to the document.\n- **Owner Details:** This is not applicable to the document.\n- **Associated Identification Numbers:**  The provided data does not include associated identification numbers.\n\nThe document provides a national ID number, \"1 2002 8 0028683 1 24.\" \n- **Face Matching:**  A face image is provided in the document.  However, a reference image is not provided, so face matching cannot be performed.\n\nThe provided data is partially valid because it matches the name and date of birth information on the document. The address information is not matched as the document provides a place of issue. \n",
                    ],
                },
            ]
        )

        print("Fine Tuning completed.")

    # Prepare a prompt for the model
    def genAiPrompt(self, personal_key_information="\\n1. Full names\\n2. Date of birth\\n3. Address\\n", company_key_information="\\n1. Date of issuance\\n2. company code\\n3. company name\\n4. registration date\\n5. owner details or Any associated identification numbers (e.g., national ID, passport number, TIN number, etc.)", submitted_data="\\n1. firstname: Manirabona \\n2. secondname: Patience \\n\n3.email: hseal419@gmail.com\\n4.personalid: \\n5.address: kigali, rwanda\\n6. city: kigali\\n7. Dob: 28/04/2002\\n8.countryCode: +250\\n9. Country: rwanda\\n10.phoneNumber: 0780289432\\n"):
        """Generates a prompt for the model to use.

        This implementation uses the file's URI as the prompt text.
        """
        return (
            f"You are tasked with extracting key information from the following document. "
            f"Please provide:{personal_key_information}. \n"
            f"For the personal identification document, Please provide: {company_key_information}. "
            f"After extracting this information, please use JSON, and JSON key must be lowercase and no space between words, just add an underscore, if any missing column as specified above, add the key but leave it nullable, if there is any metadata, add it in the 'metadata' key. "
            f"And here is the submitted data as follows: {submitted_data}"
            f"Please validate this data and check if it matches with what is provided in the document, please make sure each key is object of submited data and document data regard the key value record and it must contain key submitted, key document data and key is match true or false key, add the key 'valid' as true or false in JSON to determine if the document and submitted data are real or valid and if this key is mandatory.\\n"
            f"If there is a face image provided, verify if it matches with a provided reference image using the face matching technique, after matching, add the key in JSON as 'face_matches' to be true or false, and don't forget the document type, if it is personal ID, Company registration, ETC. \\n\\n"
            f"Steps:\\n- First, extract all structured and unstructured data as outlined and put them in JSON where each extracted data should be matched with submitted data. \\n\\n"
            f"then, check if the submitted data matches with document details and highlight the mismatched. \\n- Then, describe any face images found in the document and read the image details then compare to the provided image file if match with details on the image or are related, if contain text.\\n"
            f"- Verify the identity by describing the process and matching the facial data to a reference image if provided."
        )

    # Upload a file to Gemini
    def uploadToGemini(self, path, mime_type=None):
        """Uploads the given file to Gemini.

        See https://ai.google.dev/gemini-api/docs/prompting_with_media
        """
        max_retries = 2
        backoff_factor = 2

        for attempt in range(max_retries):
            try:
                file = genai.upload_file(path, mime_type=mime_type)
                print(f"Uploaded file '{file.display_name}' as: {file.uri}")
                return file
            except HttpError as e:
                if e.resp.status == 503:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Service unavailable. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to upload file: {e}")
                    raise
        raise Exception("Max retries exceeded. Failed to upload file.")

    # Wait for files to be active
    def waitForFilesActive(self, files):
        """Waits for the given files to be active.

        Some files uploaded to the Gemini API need to be processed before they can be
        used as prompt inputs. The status can be seen by querying the file's "state"
        field.

        This implementation uses a simple blocking polling loop. Production code
        should probably employ a more sophisticated approach.
        """
        print("Waiting for file processing...")

        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        
        print("...all files ready")
        print()

    # Extract data from the uploaded file
    def extractData(self, uploaded_file, uploaded_image, submitted_data):
        # Upload the file to Gemini
        self.file = uploaded_file
        self.image = uploaded_image
        self.submitted_data = submitted_data

        file = self.uploadToGemini(self.file, mime_type=self.determineMIMETypeOfFile(self.file))
        image = self.uploadToGemini(self.image, mime_type=self.determineMIMETypeOfFile(self.image))

        # Some files have a processing delay. Wait for them to be ready.
        self.waitForFilesActive([ file, image ])

        # Build custom Prompt
        if submitted_data is None:
            prompt = self.genAiPrompt()
        else:
            prompt = self.genAiPrompt(submitted_data=self.formatSubmittedData(submitted_data))

        # Start a new chat session with the new document
        model_session = self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [ file, image, prompt ],
                },
            ]
        )

        # Send a message to the chat session to continue processing
        chat_response = model_session.send_message("Please extract all relevant details from this new document, validate the submitted data and verify the identity if applicable.")
        return chat_response.text
    
    # Determine the MIME type of a file
    def determineMIMETypeOfFile(self, file):
        mime_type, _ = mimetypes.guess_type(file)
        
        if mime_type is None:
            mime_type = 'application/octet-stream'

        return mime_type
    
    # Format the extracted data
    def formatSubmittedData(self, data):
        return (
            f"\\n1. firstname: {data['firstname']} "
            f"\\n2. secondname: {data['secondname']} "
            f"\\n3. email: {data['email']} "
            f"\\n4. personalid: {data['personalid']} "
            f"\\n5. address: {data['address']} "
            f"\\n6. city: {data['city']} "
            f"\\n7. Dob: {data['dob']} "
            f"\\n8. countryCode: {data['countryCode']} "
            f"\\n9. Country: {data['country']} "
            f"\\n10. phoneNumber: {data['phoneNumber']}\\n"
        )
    
DataExtractionService = GenFileDataExtractionService()