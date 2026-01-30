<?php

use Illuminate\Foundation\Application;
use Illuminate\Http\Request;

define('LARAVEL_START', microtime(true));

// Determine if the application is in maintenance mode...
if (file_exists($maintenance = __DIR__.'/../storage/framework/maintenance.php')) {
    require $maintenance;
}

// Register the Composer autoloader...
require __DIR__.'/../vendor/autoload.php';

// Bootstrap Laravel and handle the request...
/** @var Application $app */
$app = require_once __DIR__.'/../bootstrap/app.php';

// If nginx redirected a 403 internally to /error/403, render the 403 view directly.
// Detect by query param, REQUEST_URI, or REDIRECT_STATUS to handle different nginx behaviours.
$shouldRender403 = false;
if ((isset($_GET['status']) && (int)$_GET['status'] === 403)
    || (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], '/error/403') === 0)
    || (isset($_SERVER['REDIRECT_STATUS']) && (int)$_SERVER['REDIRECT_STATUS'] === 403)
) {
    $shouldRender403 = true;
}

if ($shouldRender403) {
    try {
        $content = view('errors.403')->render();
        http_response_code(403);
        echo $content;
        exit;
    } catch (Throwable $e) {
        // If rendering fails, fall through to normal app handling.
    }
}

$app->handleRequest(Request::capture());
