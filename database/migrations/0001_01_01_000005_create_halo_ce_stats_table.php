<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('halo_ce_stats', function (Blueprint $table)
        {
            $table->id();
            $table->integer('player_count')->default(0);
            $table->integer('server_count')->default(0);
            $table->timestamp('recorded_at')->index();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('halo_ce_stats');
    }
};
