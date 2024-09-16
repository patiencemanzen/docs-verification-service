import os
import time
import google.generativeai as genai # type: ignore
from google.generativeai.types import HarmCategory, HarmBlockThreshold # type: ignore

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
    def igniteChatSession(self):
        print("Starting Fine Tuning...")

        # Fine Tune the model
        files = [
            self.uploadToGemini("/content/drive/MyDrive/ID/Scan9.pdf", mime_type="application/pdf"),
        ]

        # Some files have a processing delay. Wait for them to be ready.
        self.waitForFilesActive(files)

        self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [
                        files[0],
                        self.prompt,
                    ],
                },
                {
                    "role": "model",
                    "parts": [
                        "```json\n{\n  \"Full names\": \"MANIRABONA Hirwa Patience\",\n  \"Date of birth\": \"28/04/2002\",\n  \"Address\": \"BUGESERA/NYAMATA\",\n  \"Any associated identification numbers\": \"1 2002 8 0028683 1 24\",\n  \"Face image details\": \"The document contains a face image of a young African man with a dark complexion and short black hair. He is wearing a white shirt with a blue collar and a light-colored undershirt. He is smiling slightly and looking directly at the camera. There are no discernible text details in the face image.\"\n}\n```\n\nThe document contains a face image. The image can be matched to a reference image using face recognition technology. This can be done using a software program that can analyze the facial features of both images and determine if they are a match. The accuracy of the match will depend on the quality of the images and the sophistication of the face recognition software.\n\nThe accuracy of the face matching depends on the quality of the image and the accuracy of the face recognition technology. However, a human review is also recommended to confirm the accuracy of the match.\n",
                    ],
                },
            ]
        )

        print("Fine Tuning completed.")

    # Prepare a prompt for the model
    def genAiPrompt(self):
        """Generates a prompt for the model to use.

        This implementation uses the file's URI as the prompt text.
        """
        return "You are tasked with extracting key information from the following document. Please provide:\n1. Full names\n2. Date of birth\n3. Address\n4. for the personal identification document and Please provide:\n1. Date of issuance\n2. company code\n3. company name\n4. registration date\n5. owner details. Any associated identification numbers (e.g., national ID, passport number, TIN number, etc.)\n5. Face image details (if any are found)\n\nAfter extracting this information, Json key must be lowercase and no space between words, just add underscore, if any missing column as specified, leave it nullable, if there is any metadata, add them in 'metadata' key, if there is a face image, verify if it matches with a provided reference image using the face matching technique, and don't forget document type, if it is personal ID, Company registration, ETC.\n\nSteps:\n- First, extract all structured and unstructured data as outlined and put them in json.\n- Then, describe any face images found in the document and read the image details, if contain texts.\n- Verify the identity by describing the process and matching the facial data to a reference image if provided."

    # Upload a file to Gemini
    def uploadToGemini(path, mime_type=None):
        """Uploads the given file to Gemini.

        See https://ai.google.dev/gemini-api/docs/prompting_with_media
        """
        file = genai.upload_file(path, mime_type=mime_type)
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file

    # Wait for files to be active
    def waitForFilesActive(files):
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
    def extractData(self, uploaded_file):
        # Upload the file to Gemini
        self.file = uploaded_file
        file = self.uploadToGemini(self.file, mime_type=self.file.mime_type)

        # Some files have a processing delay. Wait for them to be ready.
        self.waitForFilesActive([ file ])

        # Start a new chat session with the new document
        model_session = self.model.start_chat(
            history=[
                {
                    "role": "user",
                    "parts": [ file, self.prompt ],
                },
            ]
        )

        # Send a message to the chat session to continue processing
        chat_response = model_session.send_message("Please extract all relevant details from this new document and verify the identity if applicable.")
        return chat_response.text