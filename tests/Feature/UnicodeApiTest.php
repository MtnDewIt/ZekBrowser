<?php

it('lists the available unicode glyph images as uppercase hex codes', function () {
    $codes = $this->getJson('/api/unicode/list')->assertOk()->json();

    expect($codes)->toBeArray()->not->toBeEmpty()
        ->and($codes)->toContain('2611')
        ->and($codes)->each->toMatch('/^[0-9A-F]+$/');
});
