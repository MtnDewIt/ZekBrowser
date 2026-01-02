<?php

namespace App\Http\Controllers\ServerBrowser;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Inertia\Inertia;

class ServerBrowserController extends Controller
{
    /**
     * Display the server browser page.
     * API endpoint is dynamically determined from the current request URL.
     */
    public function index(Request $request): \Inertia\Response
    {
        $theme = $request->get('theme', 'zekbrowser');

        $view = match ($theme) {
            'zekbrowser' => 'zekbrowser',
            default => 'zekbrowser',
        };

        // Build API URL dynamically from current request
        $apiUrl = '/api/';

        return Inertia::render("$view", [
            'zekBrowserApi' => $apiUrl,
        ]);
    }
}