<?php

use App\Http\Controllers\Api\ProxyController;
use App\Http\Controllers\Api\StatsController;
use App\Http\Controllers\Api\UnicodeController;
use Illuminate\Support\Facades\Route;

// Everything under /api is a same-origin pass-through to the internal FastAPI
// service (server.py) so the browser never has to deal with CORS.

// ElDewrito
Route::get('/', [ProxyController::class, 'eldewritoList']);
Route::get('/stats', [StatsController::class, 'eldewrito']);
Route::get('/servicerecord', [ProxyController::class, 'serviceRecord']);

// Project Cartographer
Route::get('/cartographer/list', [ProxyController::class, 'cartographerList']);
Route::get('/cartographer/servers/{id}', [ProxyController::class, 'cartographerServer'])->where('id', '[A-Za-z0-9_-]+');
Route::get('/cartographer/stats', [StatsController::class, 'cartographer']);
Route::get('/unicode/list', [UnicodeController::class, 'list']);

// Halo Custom Edition
Route::get('/haloce/list', [ProxyController::class, 'haloceList']);
Route::get('/haloce/stats', [StatsController::class, 'haloce']);

// Halo PC
Route::get('/halopc/list', [ProxyController::class, 'halopcList']);
Route::get('/halopc/stats', [StatsController::class, 'halopc']);
