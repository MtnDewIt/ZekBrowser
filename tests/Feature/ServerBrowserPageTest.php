<?php

use Inertia\Testing\AssertableInertia as Assert;

it('renders the server browser page', function () {
    $this->withoutVite()
        ->get('/')
        ->assertOk()
        ->assertInertia(fn (Assert $page) => $page
            ->component('zekbrowser')
            ->where('zekBrowserApi', '/api/')
        );
});
