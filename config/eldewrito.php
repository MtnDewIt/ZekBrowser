<?php

return 
[
    /*
    |--------------------------------------------------------------------------
    | Python API URL
    |--------------------------------------------------------------------------
    |
    | The internal URL where the Python FastAPI server is running.
    | This is used by Laravel to proxy requests.
    | Defaults to localhost for internal communication.
    |
    */

    'python_api_url' => env('PYTHON_API_URL', 'http://127.0.0.1:8001'),
];
