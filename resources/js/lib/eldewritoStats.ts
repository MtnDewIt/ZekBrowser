/**
 * Resolves ElDewrito player uids to stats.eldewrito.org ids and ranks via /api/servicerecord.
 * The caches are module-level so every PlayersCard on the page shares them.
 */

import { playerCandidateUid, playerOwnRank, type PlayerLike } from '@/lib/eldewritoPlayers';
import { reactive } from 'vue';

const STATS_ID_TTL_MS = 86_400_000; // 24 hours
const RANK_TTL_MS = 1_800_000; // 30 minutes
const STATS_SITE = 'https://stats.eldewrito.org/player/';

interface Cached<T> {
    value: T;
    at: number;
}

const statsIds = reactive(new Map<string, Cached<string>>());
const ranks = reactive(new Map<string, Cached<number>>());
const inflight = new Map<string, Promise<string | null>>();

function fresh<T>(entry: Cached<T> | undefined, ttl: number): T | null {
    return entry && Date.now() - entry.at < ttl ? entry.value : null;
}

function isDigits(value: unknown): value is string | number {
    return (typeof value === 'number' || typeof value === 'string') && /^\d+$/.test(String(value));
}

/** Versions from 0.7 publish uids the stats site knows about. */
export function isVersionAtLeast(version: string | null | undefined, minMajor: number, minMinor: number): boolean {
    const m = version?.match(/^(\d+)\.(\d+)/);

    if (!m) {
        return false;
    }

    const major = Number(m[1]);
    const minor = Number(m[2]);

    return major > minMajor || (major === minMajor && minor >= minMinor);
}

interface ServiceRecord {
    id?: unknown;
    rank?: unknown;
    player?: { id?: unknown; rank?: unknown };
}

async function fetchServiceRecord(uid: string): Promise<string | null> {
    try {
        const response = await fetch(`/api/servicerecord?uid=${encodeURIComponent(uid)}`);

        if (!response.ok) {
            return null;
        }

        const data = (await response.json()) as ServiceRecord | null;

        if (!data) {
            return null;
        }

        const id = isDigits(data.id) ? String(data.id) : isDigits(data.player?.id) ? String(data.player?.id) : null;
        const rank = isDigits(data.rank) ? Number(data.rank) : isDigits(data.player?.rank) ? Number(data.player?.rank) : null;

        if (rank !== null) {
            ranks.set(uid, { value: rank, at: Date.now() });
        }

        if (id !== null) {
            statsIds.set(uid, { value: id, at: Date.now() });
        }

        return id;
    } catch {
        return null;
    }
}

export function resolveStatsId(uid: string): Promise<string | null> {
    const cached = fresh(statsIds.get(uid), STATS_ID_TTL_MS);

    if (cached) {
        return Promise.resolve(cached);
    }

    let pending = inflight.get(uid);

    if (!pending) {
        pending = fetchServiceRecord(uid).finally(() => inflight.delete(uid));
        inflight.set(uid, pending);
    }

    return pending;
}

/** Resolve every unresolved hex uid in the list, a few at a time. */
export async function preloadPlayerStats(players: unknown[], concurrency = 6): Promise<void> {
    const uids = players
        .map((p) => (typeof p === 'object' && p !== null ? playerCandidateUid(p as PlayerLike) : null))
        .filter((uid): uid is string => !!uid && !/^\d+$/.test(uid) && !fresh(statsIds.get(uid), STATS_ID_TTL_MS));

    for (let i = 0; i < uids.length; i += concurrency) {
        await Promise.all(uids.slice(i, i + concurrency).map(resolveStatsId));
    }
}

/** Link to the player's stats page, or '#' when it cannot be determined (yet). */
export function playerStatsHref(p: PlayerLike): string {
    const candidate = playerCandidateUid(p);

    if (!candidate) {
        return '#';
    }

    if (/^\d+$/.test(candidate)) {
        return STATS_SITE + candidate;
    }

    const resolved = statsIds.get(candidate)?.value;

    return resolved ? STATS_SITE + resolved : '#';
}

/** Rank from the player object, else the cached rank from the stats site. */
export function playerRank(p: PlayerLike): number | null {
    const own = playerOwnRank(p);

    if (own !== null) {
        return own;
    }

    const candidate = playerCandidateUid(p);

    if (!candidate) {
        return null;
    }

    const rank = fresh(ranks.get(candidate), RANK_TTL_MS);

    if (rank === null) {
        ranks.delete(candidate);
    }

    return rank;
}
