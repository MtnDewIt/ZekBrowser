<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;

class ProxyController extends Controller
{
    private string $pythonApiUrl;

    private string $applicationPath = 'application/json';

    public function __construct()
    {
        $this->pythonApiUrl = config('eldewrito.python_api_url', 'http://127.0.0.1:8001');
    }

    public function index()
    {
        try 
        {
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/");
            
            return response($response->body(), $response->status())
                ->header('Content-Type', $this->applicationPath);
        } 
        catch (\Exception $e) 
        {
            return response()->json([
                'error' => 'Failed to fetch server data',
                'message' => $e->getMessage()
            ], 503);
        }
    }

    public function stats()
    {
        try 
        {
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/stats");
            
            return response($response->body(), $response->status())
                ->header('Content-Type', $this->applicationPath);
        } 
        catch (\Exception $e) 
        {
            return response()->json([
                'error' => 'Failed to fetch stats data',
                'message' => $e->getMessage()
            ], 503);
        }
    }

    public function serviceRecord(Request $request)
    {
        $json = [];
        
        try 
        {
            $json = $request->json()->all();
        } 
        catch (Exception $e) 
        {
            $json = [];
        }

        $uid = $request->query('uid') ?? ($json['uid'] ?? null);

        if (!isset($uid) || !is_string($uid) || $uid === '') 
        {
            return response()->json(['error' => 'Missing or invalid uid'], 400);
        }

        try 
        {
            $response = Http::timeout(30)->get("{$this->pythonApiUrl}/api/servicerecord", ['uid' => $uid]);

            return response($response->body(), $response->status())
                ->header('Content-Type', $this->applicationPath);
        } 
        catch (Exception $e) 
        {
            return response()->json([
                'error' => 'Failed to fetch service record',
                'message' => $e->getMessage()
            ], 503);
        }
    }
}
