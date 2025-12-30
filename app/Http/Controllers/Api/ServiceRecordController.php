<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use App\Services\ServiceRecordService;
use Illuminate\Http\JsonResponse;

class ServiceRecordController extends Controller
{
    protected ServiceRecordService $service;

    public function __construct(ServiceRecordService $service)
    {
        $this->service = $service;
    }

    /**
     * Lookup an external ID for a player UID. Returns cached value if present;
     * otherwise will attempt an external lookup for eldewrito >= 0.7.
     *
     * POST payload: { "uid": "...", "eldewrito_version": "0.7.1" }
     */
    public function lookup(Request $request): JsonResponse
    {
        $data = $request->validate([
            'uid' => 'required|string',
            'eldewrito_version' => 'nullable|string',
        ]);

        $uid = $data['uid'];
        $version = $data['eldewrito_version'] ?? null;

        $id = $this->service->getIdForUid($uid, $version);

        return response()->json([
            'uid' => $uid,
            'id' => $id,
        ]);
    }
}
