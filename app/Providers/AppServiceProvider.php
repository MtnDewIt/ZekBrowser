<?php

namespace App\Providers;

use App\Services\PythonApi;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\URL;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(PythonApi::class, fn () => new PythonApi(
            config('eldewrito.python_api_url', 'http://127.0.0.1:8001'),
        ));
    }

    public function boot(): void
    {
        if (
            request()->header('X-Forwarded-Proto') === 'https' ||
            request()->header('X-Forwarded-SSL') === 'on' ||
            request()->server('HTTP_X_FORWARDED_PROTO') === 'https' ||
            request()->server('HTTP_X_FORWARDED_SSL') === 'on'
        ) {
            URL::forceScheme('https');
        }

        request()->setTrustedProxies(
            ['*'],
            Request::HEADER_X_FORWARDED_FOR |
            Request::HEADER_X_FORWARDED_HOST |
            Request::HEADER_X_FORWARDED_PORT |
            Request::HEADER_X_FORWARDED_PROTO |
            Request::HEADER_X_FORWARDED_PREFIX
        );
    }
}
