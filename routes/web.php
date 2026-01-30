<?php

use App\Http\Controllers\ServerBrowser\ServerBrowserController;
use Illuminate\Support\Facades\Route;

Route::get('/', [ServerBrowserController::class, 'index'])->name('server-browser');

// Route used by nginx to render a proper 403 page when nginx returns 403
Route::get('/error/403', function () {
	abort(403);
});
