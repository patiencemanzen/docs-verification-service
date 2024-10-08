# Murugo Verification Service in Laravel 

The Murugo Verification Service leverages Django technology to extract and validate user details against provided documents and images. This service ensures that user information is accurately verified, enhancing the reliability of your application.

## Basic Usage

To get started, ensure you have the Custom Data package installed properly. You can install it using Composer:

```⚠ Please Follow step by step:```

```bash
composer require kakaprodo/custom-data
```

### Dispatching the Verification Job

You can dispatch the VerifyClientRecords job with the necessary user details and document paths. Below is an example of how to do this in your Laravel application:

```php
VerifyClientRecords::dispatch([
    'murugo_user_id' => '1',
    'firstname' => 'Manirabona',
    'secondname' => 'Patience',
    'email' => 'hseal419@gmail.com',
    'personalid' => '123456',
    'address' => '123456',
    'city' => 'Kigali',
    'dob' => '2000-01-01',
    'countryCode' => '+250',
    'country' => 'Rwanda',
    'phoneNumber' => '0781234567',
    'id_type' => 'National ID',
    'file' => public_path('files/doc_test.pdf'),
    'image_file' => public_path('files/image_test.jpg'),
]);
```

### VerifyClientRecords Job

Ensure that you have a Cron job class defined to handle background processes efficiently. This class will manage the scheduling and execution of tasks that need to run periodically without manual intervention.

```php
<?php

    namespace App\Jobs;

    use App\Services\DataExtractionService;
    use Illuminate\Contracts\Queue\ShouldQueue;
    use Illuminate\Foundation\Queue\Queueable;

    class VerifyClientRecords implements ShouldQueue {
        use Queueable;

        /**
         * DataExtractionService
         * @var DataExtractionService
         */
        public DataExtractionService $dataExtractionService;

        /**
         * Client Payload
         * @var array
         */
        public array $clientPayload = [];

        /**
         * Create a new job instance.
         */
        public function __construct(array $clientPayload) {
            $this->dataExtractionService = new \App\Services\DataExtractionService();
            $this->clientPayload = $clientPayload;
        }

        /**
         * Execute the job.
         */
        public function handle(): void {
            $this->dataExtractionService->setPayload($this->clientPayload)->extractData(function ($extractedData) {
                // call database service to save extracted data
                // dd($extractedData);
            }, function ($error) {
                // Retry or Handle Return exception
                // dd($error);
            });
        }
    }
```

## Data Extraction and Validation

To ensure accurate data extraction, it is essential to provide a well-structured payload and implement robust data validation mechanisms. This process involves sending the necessary data to the extraction service and validating the returned results to ensure they meet the required standards.

### Payload Structure

The payload should include all the necessary fields required by the data extraction service. Here is an example of a typical payload structure:

```json
{
    "murugo_user_id": "1",
    "firstname": "Manirabona",
    "secondname": "Patience",
    "email": "hseal419@gmail.com",
    "personalid": "123456",
    "address": "123456",
    "city": "Kigali",
    "dob": "2000-01-01",
    "countryCode": "+250",
    "country": "Rwanda",
    "phoneNumber": "0781234567",
    "id_type": "National ID",
    "file": "/path/to/doc_test.pdf",
    "image_file": "/path/to/image_test.jpg"
}
```

Implementing data validation ensures that the extracted data is accurate and reliable. Here are some key validation steps:

```php
<?php
    namespace App\Http\CustomData;

    use Kakaprodo\CustomData\CustomData;

    class DataExtractionPyload extends CustomData {
        /**
         * DataExtractionData  Payload data validation
         *
         * @var string
         */
        protected function expectedProperties(): array {
            return [
                'murugo_user_id' => $this->dataType()->string(),
                'firstname' => $this->dataType()->string(),
                'secondname' => $this->dataType()->string(),
                'email' => $this->dataType()->string(),
                'personalid' => $this->dataType()->string(),
                'address' => $this->dataType()->string(),
                'city' => $this->dataType()->string(),
                'dob' => $this->dataType()->string(),
                'countryCode' => $this->dataType()->string(),
                'country' => $this->dataType()->string(),
                'phoneNumber' => $this->dataType()->string(),
                'id_type' => $this->dataType()->string(),

                // Files
                'file' => $this->dataType()->string(),
                'image_file' => $this->dataType()->string(),
            ];
        }
    }
```

## Service Class for Data Extraction

To handle communication between your project and the Data Extraction Service, you need to create a dedicated Service class. This class will encapsulate all the logic required to interact with the Data Extraction Service, making your code more modular and maintainable.

### Creating the Service Class

1. **Define the Service Class**: Create a new PHP class that will handle all interactions with the Data Extraction Service.
2. **Implement Methods**: Add methods for sending requests, handling responses, and managing errors.
3. **Use cURL**: Utilize cURL for making HTTP requests to the Data Extraction Service.

### Below Service Class

Here is an example of how to create a Service class for handling communication with the Data Extraction Service:

```php
<?php
    namespace App\Services;

    use App\Http\CustomData\DataExtractionPyload;

    class DataExtractionService {
        /**
         * CSRF token
         *
         * @var string|null
         */
        public ?string $csrfToken = null;

        /**
         * Data extraction service URL
         *
         * @var string
         */
        public string $dataExtractionServiceUrl;

        /**
         * DataExtractionPyload
         *
         * @var array
         */
        public array $payload;

        /**
         * DataExtractionService constructor
         */
        public function __construct() {
            $this->dataExtractionServiceUrl =  "http://127.0.0.1:8000/api";
            $this->getCRFToken();
        }

        /**
         * Set the payload for the API
         *
         * @param DataExtractionPyload $data
         * @return DataExtractionService
         */
        public function setPayload(array $data) {
            $this->payload = DataExtractionPyload::make($data)->all();
            return $this;
        }

        /**
         * Get the CSRF token from the API
         *
         * @param void
         * @return string|null
         */
        public function getCRFToken() {
            try {
                $ch = curl_init();

                curl_setopt($ch, CURLOPT_URL, $this->dataExtractionServiceUrl."/csrf-token");
                curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
                curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

                $output = curl_exec($ch);

                if ($output === FALSE) {
                    $this->csrfToken = null;
                } else {
                    $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

                    if ($http_code == 200) {
                        $response_data = json_decode($output, true);
                        $this->csrfToken = (isset($response_data['csrfToken'])) ? $response_data['csrfToken'] : null;
                    } else {
                        $this->csrfToken = null;
                    }
                }

                curl_close($ch);
            } catch (\Exception $e) {
                $this->csrfToken = null;
            }
        }

        /**
         * Call Extract data Service from the API
         *
         * @param void
         * @return void
         */
        public function extractData(callable $callback, callable $fallback = null) {
            try {
                $csrfToken = $this->csrfToken ?? throw new \Exception("CSRF token is not set");
                $response = $this->callDataExtractionService($csrfToken, $this->payload);
                return $callback($response);
            } catch (\Exception $e) {
                return $fallback($e);
            }
        }

        /**
         * Call Data Extraction Service
         *
         * @param string $csrfToken
         * @param array $data
         * @return void
         */
        public function callDataExtractionService(string $csrfToken, array $data) {
            $ch = curl_init();

            (!file_exists($data['file']) || !file_exists($data['image_file']))
                ?? throw new \Exception("file or image Path must be exist");

            $data['file'] = new \CURLFile(realpath($data['file']));
            $data['image_file'] = new \CURLFile(realpath($data['image_file']));

            curl_setopt($ch, CURLOPT_URL, "{$this->dataExtractionServiceUrl}/upload/");
            curl_setopt($ch, CURLOPT_TIMEOUT, 120);
            curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 60);

            curl_setopt($ch, CURLOPT_POST, 1);
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_VERBOSE, true);

            // Set headers
            curl_setopt($ch, CURLOPT_HTTPHEADER, [
                "X-CSRFToken: $csrfToken",
                'Content-Type: multipart/form-data',
                'Expect:' // Disable the Expect header
            ]);

            $output = curl_exec($ch);

            if ($output === FALSE) {
                $curl_error = curl_error($ch);
                $curl_errno = curl_errno($ch);
                curl_close($ch);

                throw new \Exception("Data extraction service failed: Curl error: " . $curl_error);
            } else {
                $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);

                return ($http_code != 200)
                    ? throw new \Exception("Data extraction service failed: Service error: " . $http_code)
                    : $this->formatJson($output);

                curl_close($ch);
            }
        }

        /**
         * Format the return Json Response
         */
        public function formatJson($output) {
            $responseData = json_decode($output, true);

            if (is_array($responseData) || is_object($responseData)) {
                $this->recursiveDecode($responseData);
            }

            return $responseData;
        }

        /**
         * Handle nested JSON decoding
         *
         * @param $data
         */
        public function recursiveDecode(&$data) {
            if (is_array($data) || is_object($data)) {
                foreach ($data as $key => &$value) {
                    if (is_string($value) && ($decodedValue = json_decode($value, true)) !== null) {
                        $value = $decodedValue;
                        $this->recursiveDecode($value); // Recursively decode any nested JSON
                    } elseif (is_array($value) || is_object($value)) {
                        $this->recursiveDecode($value);
                    }
                }
            }
        }
    }

```
