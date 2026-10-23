<?php

namespace App\Services;

use Illuminate\Http\Client\Response as HttpResponse;
use Illuminate\Http\Response;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Throwable;

/**
 * Thin client for the internal FastAPI service (server.py).
 *
 * Every public endpoint of the Laravel API is a pass-through to this service,
 * so all of the fetch / cache / error handling lives here exactly once.
 */
class PythonApi
{
    public const CONTENT_TYPE = 'application/json';

    public function __construct(
        private readonly string $baseUrl,
        private readonly int $timeoutSeconds = 30,
    ) {}

    /**
     * Proxy a GET request and return it to the browser as-is.
     *
     * Successful (2xx) bodies are cached for $cacheSeconds when a $cacheKey is given.
     * Upstream error responses are passed through with their status but never cached,
     * so a transient "warming up" 503 does not get replayed as a 200 for 30 seconds.
     */
    public function proxy(string $path, array $query = [], ?string $cacheKey = null, int $cacheSeconds = 0): Response
    {
        $useCache = $cacheKey !== null && $cacheSeconds > 0;

        if ($useCache) {
            $cached = Cache::get($cacheKey);

            if (is_string($cached)) {
                return $this->jsonResponse($cached, 200);
            }
        }

        try {
            $response = $this->get($path, $query);
        } catch (Throwable $e) {
            Log::warning('Python API request failed', ['path' => $path, 'error' => $e->getMessage()]);

            return $this->unavailable();
        }

        if ($useCache && $response->successful()) {
            Cache::put($cacheKey, $response->body(), now()->addSeconds($cacheSeconds));
        }

        return $this->jsonResponse($response->body(), $response->status());
    }

    public function get(string $path, array $query = []): HttpResponse
    {
        return Http::timeout($this->timeoutSeconds)
            ->acceptJson()
            ->get(rtrim($this->baseUrl, '/').'/'.ltrim($path, '/'), $query);
    }

    private function jsonResponse(string $body, int $status): Response
    {
        return response($body, $status)->header('Content-Type', self::CONTENT_TYPE);
    }

    private function unavailable(): Response
    {
        return $this->jsonResponse(json_encode([
            'error' => 'Failed to fetch data from the server API',
            'message' => 'The server API is unavailable, please try again shortly.',
        ]), 503);
    }
}
