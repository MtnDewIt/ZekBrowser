<?php

use App\Http\Controllers\Api\ProxyController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ProxyController::class, 'index']);
Route::get('/stats', [ProxyController::class, 'stats']);
Route::get('/servicerecord', [ProxyController::class, 'serviceRecord']);