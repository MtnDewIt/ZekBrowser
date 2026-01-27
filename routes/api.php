<?php

use App\Http\Controllers\Api\ProxyController;
use App\Http\Controllers\Api\CartographerProxyController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ProxyController::class, 'index']);
Route::get('/stats', [ProxyController::class, 'stats']);
Route::get('/servicerecord', [ProxyController::class, 'serviceRecord']);

// Cartographer proxy endpoints to avoid CORS issues from the browser
Route::get('/cartographer/list', [CartographerProxyController::class, 'list']);
Route::get('/cartographer/servers/{id}', [CartographerProxyController::class, 'server']);
