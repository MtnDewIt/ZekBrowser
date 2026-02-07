<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class HaloPCProxyController extends Controller
{
    private string $pythonApiUrl;

    private string $applicationPath = 'application/json';

    public function __construct()
    {
        $this->pythonApiUrl = config('eldewrito.python_api_url', 'http://127.0.0.1:8001');
    }
}