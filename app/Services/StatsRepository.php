<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;
use InvalidArgumentException;

/**
 * Reads the per-game player/server history tables written by server.py.
 */
class StatsRepository
{
    public const TABLES = [
        'eldewrito' => 'server_stats',
        'cartographer' => 'cartographer_stats',
        'haloce' => 'haloce_stats',
        'halopc' => 'halopc_stats',
    ];

    private const CACHE_SECONDS = 60;

    /**
     * Highcharts-style series: [[timestampMs, value], ...] for players and servers.
     *
     * @return array{players: array<int, array{int, int}>, servers: array<int, array{int, int}>}
     */
    public function history(string $game): array
    {
        $table = self::TABLES[$game] ?? throw new InvalidArgumentException("Unknown game [$game]");

        return Cache::remember("stats:$table", self::CACHE_SECONDS, fn () => $this->load($table));
    }

    private function load(string $table): array
    {
        $rows = DB::table($table)
            ->orderBy('recorded_at')
            ->get(['recorded_at', 'player_count', 'server_count']);

        $players = [];
        $servers = [];

        foreach ($rows as $row) {
            $timestamp = strtotime((string) $row->recorded_at);

            if ($timestamp === false) {
                continue;
            }

            $timestamp *= 1000;
            $players[] = [$timestamp, (int) $row->player_count];
            $servers[] = [$timestamp, (int) $row->server_count];
        }

        return ['players' => $players, 'servers' => $servers];
    }
}
