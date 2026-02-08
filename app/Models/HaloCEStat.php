<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class HaloCEStat extends Model
{
    protected $table = 'haloce_stats';

    protected $fillable =
    [
        'player_count',
        'server_count',
        'recorded_at',
    ];

    protected $casts =
    [
        'recorded_at' => 'datetime',
    ];
}
