<?php

namespace App\Http\Controllers\Api;

use Illuminate\Http\Request;
use Illuminate\Routing\Controller;
use Illuminate\Support\Facades\File;

class UnicodeController extends Controller
{
    /**
     * Return a JSON list of unicode image basenames (without extension) from public/assets/unicode
     */
    public function list(Request $request)
    {
        $dir = public_path('assets/unicode');
        $out = [];
        if (File::exists($dir) && File::isDirectory($dir)) {
            $files = File::files($dir);
            foreach ($files as $f) {
                $name = $f->getBasename('.png');
                // normalize uppercase hex
                $out[] = strtoupper($name);
            }
        }
        return response()->json(array_values(array_unique($out)));
    }
}
