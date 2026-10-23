<?php

namespace App\Http\Controllers\ServerBrowser;

use App\Http\Controllers\Controller;
use Inertia\Inertia;
use Inertia\Response;

class ServerBrowserController extends Controller
{
    public function index(): Response
    {
        return Inertia::render('zekbrowser', [
            'zekBrowserApi' => '/api/',
        ]);
    }
}
