<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class ServiceRecord extends Model
{
    protected $table = 'service_records';

    protected $fillable = [
        'uid',
        'external_id',
        'name',
        'payload',
    ];

    protected $casts = [
        'payload' => 'array',
    ];
}
