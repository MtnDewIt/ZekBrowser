<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class CartographerProxyController extends Controller
{
    private string $pythonApiUrl;

    private string $applicationPath = 'application/json';

    public function __construct()
    {
        $this->pythonApiUrl = config('eldewrito.python_api_url', 'http://127.0.0.1:8001');
    }

    public function list()
    {
        $cacheKey = 'cartographer:list:summary';

        // Return cached summary if available
        if (Cache::has($cacheKey)) 
        {
            $cached = Cache::get($cacheKey);
            
            return response($cached, 200)->header('Content-Type', $this->applicationPath);
        }

        try 
        {
            // Use the new unified Python API endpoint that returns summarized data
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/cartographer");
            $out = $response->body();
            $status = $response->status();

            // Cache the resulting JSON string for 30 seconds to avoid spamming upstream
            Cache::put($cacheKey, $out, now()->addSeconds(30));

            return response($out, $status)->header('Content-Type', $this->applicationPath);
        } 
        catch (\Exception $e) 
        {
            return response()->json(['error' => 'Failed to fetch cartographer list', 'message' => $e->getMessage()], 503);
        }
    }

    public function server(string $id)
    {
        $cacheKey = "cartographer:server:{$id}";
        if (Cache::has($cacheKey)) 
        {
            $cached = Cache::get($cacheKey);

            return response($cached, 200)->header('Content-Type', $this->applicationPath);
        }

        try 
        {
            // Use the new unified Python API endpoint for server details
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/cartographer/server/{$id}");
            $body = $response->body();

            Cache::put($cacheKey, $body, now()->addSeconds(30));

            return response($body, $response->status())
                ->header('Content-Type', $this->applicationPath);
        } 
        catch (\Exception $e) 
        {
            return response()->json(['error' => 'Failed to fetch cartographer server', 'message' => $e->getMessage()], 503);
        }
    }
}
