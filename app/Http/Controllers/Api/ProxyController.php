<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\PythonApi;
use Illuminate\Http\Request;
use Illuminate\Http\Response;

/**
 * Public JSON endpoints that pass through to the internal FastAPI service.
 * Lists are cached briefly so browser polling does not hammer the Python process.
 */
class ProxyController extends Controller
{
    private const LIST_CACHE_SECONDS = 30;

    public function __construct(private readonly PythonApi $api) {}

    public function eldewritoList(): Response
    {
        return $this->api->proxy('/api/');
    }

    public function serviceRecord(Request $request): Response
    {
        $uid = $request->query('uid') ?? $request->json('uid');

        if (! is_string($uid) || $uid === '') {
            return response(json_encode(['error' => 'Missing or invalid uid']), 400)
                ->header('Content-Type', PythonApi::CONTENT_TYPE);
        }

        return $this->api->proxy('/api/servicerecord', ['uid' => $uid]);
    }

    public function cartographerList(): Response
    {
        return $this->api->proxy('/api/cartographer', [], 'cartographer:list:summary', self::LIST_CACHE_SECONDS);
    }

    public function cartographerServer(string $id): Response
    {
        return $this->api->proxy("/api/cartographer/server/$id", [], "cartographer:server:$id", self::LIST_CACHE_SECONDS);
    }

    public function haloceList(): Response
    {
        return $this->api->proxy('/api/haloce', [], 'haloce:list', self::LIST_CACHE_SECONDS);
    }

    public function halopcList(): Response
    {
        return $this->api->proxy('/api/halopc', [], 'halopc:list', self::LIST_CACHE_SECONDS);
    }
}
