<?php

use App\Http\Controllers\ServerBrowser\ServerBrowserController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ServerBrowserController::class, 'index'])->name('server-browser');