<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\HaloCEStat;
use Illuminate\Http\JsonResponse;

class HaloCEStatsController extends Controller
{
    public function index(): JsonResponse
    {
        $stats = HaloCEStat::orderBy('recorded_at', 'asc')->get(['recorded_at', 'player_count', 'server_count']);

        $players = [];
        $servers = [];

        foreach ($stats as $stat)
        {
            $timestamp = $stat->recorded_at->timestamp * 1000;
            $players[] = [$timestamp, $stat->player_count];
            $servers[] = [$timestamp, $stat->server_count];
        }

        return response()->json([
            'players' => $players,
            'servers' => $servers,
        ]);
    }
}
