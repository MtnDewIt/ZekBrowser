<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\File;

class UnicodeController extends Controller
{
    private const CACHE_SECONDS = 3600;

    /**
     * JSON list of the unicode glyph images available in public/assets/unicode,
     * as uppercase hex code points without extension (for example "2611").
     */
    public function list(): JsonResponse
    {
        $codes = Cache::remember('unicode:list', self::CACHE_SECONDS, function () {
            $dir = public_path('assets/unicode');

            if (! File::isDirectory($dir)) {
                return [];
            }

            $codes = [];

            foreach (File::files($dir) as $file) {
                if ($file->getExtension() === 'webp') {
                    $codes[] = strtoupper($file->getBasename('.webp'));
                }
            }

            return array_values(array_unique($codes));
        });

        return response()->json($codes);
    }
}
