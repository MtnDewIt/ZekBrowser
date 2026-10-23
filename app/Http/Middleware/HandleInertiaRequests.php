<?php

namespace App\Http\Middleware;

use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    protected $rootView = 'zekbrowser';

    public function share(Request $request): array
    {
        return [
            ...parent::share($request),
            'name' => config('app.name'),
        ];
    }
}
