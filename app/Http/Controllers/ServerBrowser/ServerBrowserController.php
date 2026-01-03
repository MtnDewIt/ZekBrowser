<?php

namespace App\Http\Controllers\ServerBrowser;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Inertia\Inertia;

class ServerBrowserController extends Controller
{
    public function index(Request $request): \Inertia\Response
    {
        $theme = $request->get('theme', 'zekbrowser');

        $view = match ($theme) {
            'zekbrowser' => 'zekbrowser',
            default => 'zekbrowser',
        };

        $apiUrl = '/api/';

        return Inertia::render("$view", [
            'zekBrowserApi' => $apiUrl,
        ]);
    }
}