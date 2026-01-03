<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ServerStat extends Model
{
    protected $fillable = [
        'player_count',
        'server_count',
        'recorded_at',
    ];

    protected $casts = [
        'recorded_at' => 'datetime',
    ];
}
