<?php

use App\Http\Controllers\Api\ProxyController;
use App\Http\Controllers\Api\UnicodeController;
use App\Http\Controllers\Api\CartographerProxyController;
use App\Http\Controllers\Api\CartographerStatsController;
use App\Http\Controllers\Api\HaloCEProxyController;
use App\Http\Controllers\Api\HaloCEStatsController;
use App\Http\Controllers\Api\HaloPCProxyController;
use App\Http\Controllers\Api\HaloPCStatsController;
use Illuminate\Support\Facades\Route;

// Backup proxy endpoints because zekken is *something*
Route::get('/', [ProxyController::class, 'index']);
Route::get('/stats', [ProxyController::class, 'stats']);
Route::get('/servicerecord', [ProxyController::class, 'serviceRecord']);

// ElDewrito proxy endpoints to avoid CORS issues from the browser
// Route::get('/eldewrito/list', [ProxyController::class, 'list']);
// Route::get('/eldewrito/stats', [ProxyController::class, 'stats']);
// Route::get('/eldewrito/servicerecord', [ProxyController::class, 'serviceRecord']);

// Cartographer proxy endpoints to avoid CORS issues from the browser
Route::get('/cartographer/list', [CartographerProxyController::class, 'list']);
Route::get('/cartographer/servers/{id}', [CartographerProxyController::class, 'server']);
Route::get('/cartographer/stats', [CartographerStatsController::class, 'index']);
Route::get('/unicode/list', [UnicodeController::class, 'list']);

// Halo CE proxy endpoints to avoid CORS issues from the browser
Route::get('/haloce/list', [HaloCEProxyController::class, 'list']);
Route::get('/haloce/stats', [HaloCEStatsController::class, 'index']);

// Halo PC proxy endpoints to avoid CORS issues from the browser
Route::get('/halopc/list', [HaloPCProxyController::class, 'list']);
Route::get('/halopc/stats', [HaloPCStatsController::class, 'index']);