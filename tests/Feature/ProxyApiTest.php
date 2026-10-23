<?php

use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;

const PYTHON = 'http://127.0.0.1:8001';

beforeEach(function () {
    config(['eldewrito.python_api_url' => PYTHON]);
});

it('passes the ElDewrito server list through unchanged', function () {
    $payload = [
        'count' => ['players' => 3, 'servers' => 1],
        'updatedAt' => 'Thu, 22 Oct 2026 00:00:00 GMT',
        'servers' => ['1.2.3.4:11775' => ['name' => 'x', 'numPlayers' => 3]],
    ];
    Http::fake([PYTHON.'/api/' => Http::response($payload, 200)]);

    $this->getJson('/api/')
        ->assertOk()
        ->assertHeader('Content-Type', 'application/json')
        ->assertExactJson($payload);
});

it('proxies list endpoints and caches successful bodies', function (string $route, string $upstream) {
    $payload = ['count' => ['players' => 0, 'servers' => 0], 'updatedAt' => 'now', 'servers' => []];
    Http::fake([PYTHON.$upstream => Http::response($payload, 200)]);

    $this->getJson($route)->assertOk()->assertExactJson($payload);
    $this->getJson($route)->assertOk()->assertExactJson($payload);

    Http::assertSentCount(1);
})->with([
    ['/api/cartographer/list', '/api/cartographer'],
    ['/api/haloce/list', '/api/haloce'],
    ['/api/halopc/list', '/api/halopc'],
    ['/api/cartographer/servers/123', '/api/cartographer/server/123'],
]);

it('does not cache upstream errors and passes their status through', function () {
    Http::fake([
        PYTHON.'/api/haloce' => Http::sequence()
            ->push(['error' => 'warming up'], 503)
            ->push(['count' => ['players' => 1, 'servers' => 1], 'servers' => []], 200),
    ]);

    $this->getJson('/api/haloce/list')->assertStatus(503)->assertJson(['error' => 'warming up']);
    $this->getJson('/api/haloce/list')->assertOk()->assertJsonPath('count.players', 1);

    Http::assertSentCount(2);
});

it('returns 503 with an error body when the Python API is unreachable', function () {
    Http::fake(fn () => throw new ConnectionException('connection refused'));

    $this->getJson('/api/')
        ->assertStatus(503)
        ->assertJsonStructure(['error', 'message'])
        ->assertJsonMissing(['message' => 'connection refused']);
});

it('requires a uid for the service record', function () {
    Http::fake();

    $this->getJson('/api/servicerecord')->assertStatus(400)->assertJson(['error' => 'Missing or invalid uid']);
    Http::assertNothingSent();
});

it('forwards the service record uid from the query string', function () {
    Http::fake([PYTHON.'/api/servicerecord*' => Http::response(['id' => 42, 'rank' => 7], 200)]);

    $this->getJson('/api/servicerecord?uid=abc123')->assertOk()->assertExactJson(['id' => 42, 'rank' => 7]);

    Http::assertSent(fn ($request) => $request['uid'] === 'abc123');
});

it('rejects cartographer server ids with unexpected characters', function () {
    Http::fake();

    $this->getJson('/api/cartographer/servers/..%2Fetc')->assertNotFound();
    Http::assertNothingSent();
});
