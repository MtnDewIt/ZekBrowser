<?php

use Illuminate\Support\Facades\DB;

it('returns chart series for every game', function (string $route, string $table) {
    DB::table($table)->insert([
        ['player_count' => 5, 'server_count' => 2, 'recorded_at' => '2026-01-01 00:05:00'],
        ['player_count' => 7, 'server_count' => 3, 'recorded_at' => '2026-01-01 00:00:00.123456+00:00'],
    ]);

    $this->getJson($route)
        ->assertOk()
        ->assertExactJson([
            'players' => [[1767225600000, 7], [1767225900000, 5]],
            'servers' => [[1767225600000, 3], [1767225900000, 2]],
        ]);
})->with([
    ['/api/stats', 'server_stats'],
    ['/api/cartographer/stats', 'cartographer_stats'],
    ['/api/haloce/stats', 'haloce_stats'],
    ['/api/halopc/stats', 'halopc_stats'],
]);

it('returns empty series when nothing has been recorded', function () {
    $this->getJson('/api/halopc/stats')->assertOk()->assertExactJson(['players' => [], 'servers' => []]);
});
