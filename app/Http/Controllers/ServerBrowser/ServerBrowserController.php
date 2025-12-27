<?php

namespace App\Http\Controllers\ServerBrowser;

use App\Http\Controllers\Controller;
use Illuminate\Http\Request;
use Inertia\Inertia;

class ServerBrowserController extends Controller
{
    /**
     * Display the server browser page.
     * Fetches data from the legacy ZekBrowser API.
     * TODO: Implement local cache
     */
    public function index(Request $request): \Inertia\Response
    {
        $theme = $request->get('theme', 'zekbrowser');

        $view = match ($theme) {
            'zekbrowser' => 'ZekBrowser',
            default => 'ZekBrowser',
        };

        return Inertia::render("server-browser/$view", [
            'zekBrowserApi' => config('eldewrito.zekbrowser_api'),
        ]);
    }
}
