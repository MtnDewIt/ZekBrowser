<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Foundation\Inspiring;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;
use Inertia\Middleware;
use Symfony\Component\HttpFoundation\Response;
use Tighten\Ziggy\Ziggy;

class HandleInertiaRequests extends Middleware
{
    protected $rootView = 'zekbrowser';

    public function version(Request $request): ?string
    {
        return parent::version($request);
    }

    public function share(Request $request): array
    {
        [$message, $author] = str(Inspiring::quotes()->random())->explode('-');

        return
        [
            ...parent::share($request),
            'name' => config('app.name'),
            'quote' => ['message' => trim($message), 'author' => trim($author)],
            'auth' =>
            [
                'user' => $request->user(),
            ],
            'ziggy' =>
            [
                ...(new Ziggy)->toArray(),
                'location' => $request->url(),
            ],
            'sidebarOpen' => ! $request->hasCookie('sidebar_state') || $request->cookie('sidebar_state') === 'true',
        ];
    }

    /**
     * Handle the incoming request.
     */
    public function handle(Request $request, Closure $next): Response
    {
        if (Route::currentRouteName() === 'home')
        {
            $this->rootView = 'zekbrowser';
        }

        return parent::handle($request, $next);
    }
}
