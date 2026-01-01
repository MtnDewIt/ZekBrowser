<?php

namespace App\Providers;

use Illuminate\Support\Facades\URL;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        //
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        if (request()->server('HTTP_X_FORWARDED_PROTO') === 'https' 
            || request()->server('HTTP_X_FORWARDED_SSL') === 'on'
            || request()->header('X-Forwarded-Proto') === 'https') 
        {
            URL::forceScheme('https');
        }
        else
        {
            URL::forceScheme('http');            
        }
        
        // Trust all proxies (safe behind reverse proxy)
        // Using bitwise OR of all forwarded header constants
        request()->setTrustedProxies(
            ['*'], 
            \Illuminate\Http\Request::HEADER_X_FORWARDED_FOR |
            \Illuminate\Http\Request::HEADER_X_FORWARDED_HOST |
            \Illuminate\Http\Request::HEADER_X_FORWARDED_PORT |
            \Illuminate\Http\Request::HEADER_X_FORWARDED_PROTO |
            \Illuminate\Http\Request::HEADER_X_FORWARDED_PREFIX
        );
    }
}