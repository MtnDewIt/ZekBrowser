<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Support\Facades\Http;

class ProxyController extends Controller
{
    private string $pythonApiUrl;

    public function __construct()
    {
        $this->pythonApiUrl = config('eldewrito.python_api_url', 'http://127.0.0.1:8001');
    }

    public function index()
    {
        try {
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/");
            
            return response($response->body(), $response->status())
                ->header('Content-Type', 'application/json');
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to fetch server data',
                'message' => $e->getMessage()
            ], 503);
        }
    }

    public function stats()
    {
        try {
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/stats");
            
            return response($response->body(), $response->status())
                ->header('Content-Type', 'application/json');
        } catch (\Exception $e) {
            return response()->json([
                'error' => 'Failed to fetch stats data',
                'message' => $e->getMessage()
            ], 503);
        }
    }
}