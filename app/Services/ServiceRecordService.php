<?php

namespace App\Services;

use App\Models\ServiceRecord;
use GuzzleHttp\Client;
use Illuminate\Support\Facades\Log;
use Exception;

class ServiceRecordService
{
    protected Client $client;
    protected string $apiUrl;

    public function __construct(Client $client = null, string $apiUrl = 'http://api.eldewrito.org/api/servicerecord')
    {
        $this->client = $client ?: new Client(['timeout' => 5]);
        $this->apiUrl = $apiUrl;
    }

    /**
     * Get the external ID for a given UID. Checks local DB first and only
     * queries the external API when needed. Result is cached in DB.
     *
     * @param string $uid
     * @return int|null
     */
    public function getIdForUid(string $uid, ?string $eldewritoVersion = null): ?int
    {
        $record = ServiceRecord::where('uid', $uid)->first();

        if ($record && $record->external_id) {
            return (int) $record->external_id;
        }

        // If the caller provided an eldewrito version and it's older than 0.7,
        // do not invoke the external API. Older clients (0.5/0.6) are excluded.
        if ($eldewritoVersion !== null && !$this->versionIsAtLeast($eldewritoVersion, '0.7')) {
            return null;
        }

        try {
            $resp = $this->client->post($this->apiUrl, [
                'headers' => [
                    'Content-Type' => 'application/json',
                    'User-Agent' => 'ElDewrito/0.7.1',
                ],
                'json' => ['uid' => $uid],
            ]);

            $body = json_decode((string) $resp->getBody(), true);

            if (!is_array($body) || !isset($body['id'])) {
                throw new Exception('Invalid response from service record API');
            }

            $externalId = (int) $body['id'];
            $name = $body['name'] ?? null;

            ServiceRecord::updateOrCreate(
                ['uid' => $uid],
                ['external_id' => $externalId, 'name' => $name, 'payload' => $body]
            );

            return $externalId;
        } catch (Exception $e) {
            Log::warning('ServiceRecordService lookup failed for uid ' . $uid . ': ' . $e->getMessage());

            // If we had a DB record without external_id return null, otherwise return external_id if present
            return $record->external_id ?? null;
        }
    }

    /**
     * Compare semantic-ish version strings (simple numeric segments) to determine
     * whether $version >= $minimum.
     */
    private function versionIsAtLeast(string $version, string $minimum): bool
    {
        $a = array_map('intval', explode('.', $version));
        $b = array_map('intval', explode('.', $minimum));

        $len = max(count($a), count($b));
        for ($i = 0; $i < $len; $i++) {
            $av = $a[$i] ?? 0;
            $bv = $b[$i] ?? 0;
            if ($av > $bv) return true;
            if ($av < $bv) return false;
        }
        return true;
    }
}
