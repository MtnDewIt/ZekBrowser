<?php

use App\Http\Controllers\Api\ProxyController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ProxyController::class, 'index']);
Route::get('/stats', [ProxyController::class, 'stats']);
Route::post('/service-record/lookup', [\App\Http\Controllers\Api\ServiceRecordController::class, 'lookup']);