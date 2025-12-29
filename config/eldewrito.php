<?php


return [

    /*
    |--------------------------------------------------------------------------
    | ZekBrowser API URL (temporary)
    |--------------------------------------------------------------------------
    |
    | The URL of the ZekBrowser API, used to populate the server browser and stats.
    |
    */

    'zekbrowser_api' => env('ZEKBROWSER_API', 'http://localhost:8000/api/'),

    /*
    |--------------------------------------------------------------------------
    | Python API URL
    |--------------------------------------------------------------------------
    |
    | The internal URL where the Python FastAPI server is running.
    | This is used by Laravel to proxy requests.
    |
    */

    'python_api_url' => env('PYTHON_API_URL', 'http://127.0.0.1:8001'),

];