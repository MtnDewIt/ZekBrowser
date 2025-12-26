<?php

use App\Http\Controllers\Api\StatsController;

Route::get('/api/stats', [StatsController::class, 'index']);
Route::get('/api/stats/{from}/{to}', [StatsController::class, 'range']);