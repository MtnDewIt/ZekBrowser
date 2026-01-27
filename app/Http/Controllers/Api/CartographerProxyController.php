<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Cache;

class CartographerProxyController extends Controller
{
    private string $base = 'https://cartographer.online/live';

    public function list()
    {
        $cacheKey = 'cartographer:list:summary';

        // Return cached summary if available
        if (Cache::has($cacheKey)) {
            $cached = Cache::get($cacheKey);
            return response($cached, 200)->header('Content-Type', 'application/json');
        }

        try {
            // Prefer running the local Python summarizer which mirrors the original
            // carto_browser.py logic and returns a consolidated JSON summary.
            $script = base_path('scripts/carto_api.py');
            $python = env('PYTHON_BINARY', 'python');
            $cmd = escapeshellcmd("{$python} " . escapeshellarg($script));
            $output = null;
            $returnVar = 0;
            exec($cmd . ' 2>&1', $output, $returnVar);
            $out = implode("\n", (array) $output);

            if ($returnVar !== 0 || trim($out) === '') {
                // fallback to direct proxy if Python fails
                $response = Http::timeout(30)->withoutVerifying()->get("{$this->base}/server_list.php");
                $out = $response->body();
                $status = $response->status();
            } else {
                $status = 200;
            }

            // Cache the resulting JSON string for 30 seconds to avoid spamming upstream
            Cache::put($cacheKey, $out, now()->addSeconds(30));

            return response($out, $status)->header('Content-Type', 'application/json');
        } catch (\Exception $e) {
            return response()->json(['error' => 'Failed to fetch cartographer list', 'message' => $e->getMessage()], 503);
        }
    }

    public function server(string $id)
    {
        $cacheKey = "cartographer:server:{$id}";
        if (Cache::has($cacheKey)) {
            $cached = Cache::get($cacheKey);
            return response($cached, 200)->header('Content-Type', 'application/json');
        }

        try {
            $response = Http::timeout(30)->withoutVerifying()->get("{$this->base}/servers/{$id}");
            $body = $response->body();
            Cache::put($cacheKey, $body, now()->addSeconds(30));
            return response($body, $response->status())
                ->header('Content-Type', 'application/json');
        } catch (\Exception $e) {
            return response()->json(['error' => 'Failed to fetch cartographer server', 'message' => $e->getMessage()], 503);
        }
    }
}
