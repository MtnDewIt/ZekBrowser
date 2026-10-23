<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Services\StatsRepository;
use Illuminate\Http\JsonResponse;

/**
 * Historical player/server counts for the stats chart, one endpoint per game.
 */
class StatsController extends Controller
{
    public function __construct(private readonly StatsRepository $stats) {}

    public function eldewrito(): JsonResponse
    {
        return response()->json($this->stats->history('eldewrito'));
    }

    public function cartographer(): JsonResponse
    {
        return response()->json($this->stats->history('cartographer'));
    }

    public function haloce(): JsonResponse
    {
        return response()->json($this->stats->history('haloce'));
    }

    public function halopc(): JsonResponse
    {
        return response()->json($this->stats->history('halopc'));
    }
}
