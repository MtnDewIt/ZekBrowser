/**
 * Tolerant accessors for the player objects ElDewrito servers publish.
 * Field names vary between ElDewrito versions, so each accessor tries the known aliases.
 */

import { teamColor, toTeamIndex } from '@/lib/teams';

export type PlayerLike = Record<string, unknown>;

export function isPlayerObject(value: unknown): value is PlayerLike {
    return typeof value === 'object' && value !== null;
}

function firstNumber(p: PlayerLike, keys: string[], fallback = 0): number {
    for (const key of keys) {
        const n = Number(p[key]);

        if (!Number.isNaN(n)) {
            return n;
        }
    }

    return fallback;
}

function firstString(p: PlayerLike, keys: string[]): string | null {
    for (const key of keys) {
        const v = p[key];

        if (v !== undefined && v !== null && v !== '') {
            return String(v);
        }
    }

    return null;
}

export function playerName(p: PlayerLike): string {
    return firstString(p, ['name', 'playerName', 'displayName', 'player_name']) ?? 'Unknown';
}

export function playerServiceTag(p: PlayerLike): string | null {
    return firstString(p, ['serviceTag', 'service_tag', 'tag', 'playerTag', 'player_tag', 'stag']);
}

export function playerEmblem(p: PlayerLike): string | null {
    return firstString(p, ['emblem', 'emblemUrl', 'emblem_url', 'emblemString']);
}

export function playerTeam(p: PlayerLike): number | null {
    return toTeamIndex(p.team ?? p.teamIndex ?? p.team_number ?? p.teamNumber ?? null);
}

export function playerScore(p: PlayerLike): number {
    const n = Number(p.roundScore);

    return Number.isNaN(n) ? 0 : n;
}

export function playerKills(p: PlayerLike): number {
    return firstNumber(p, ['kills', 'k', 'killCount', 'kill_count']);
}

export function playerDeaths(p: PlayerLike): number {
    return firstNumber(p, ['deaths', 'd', 'deathCount', 'death_count']);
}

export function playerAssists(p: PlayerLike): number {
    return firstNumber(p, ['assists', 'a', 'assistCount', 'assist_count']);
}

export function playerBestStreak(p: PlayerLike): number {
    return firstNumber(p, ['bestStreak', 'best_streak', 'killingSpree', 'killing_spree', 'streak', 'maxStreak', 'max_streak']);
}

/** Rank carried on the player object itself (not the one resolved from the stats site). */
export function playerOwnRank(p: PlayerLike): number | null {
    for (const key of ['rank', 'playerRank', 'service_rank', 'serviceRank']) {
        if (key in p) {
            const n = Number(p[key]);

            if (!Number.isNaN(n) && n >= 0) {
                return n;
            }
        }
    }

    return null;
}

/**
 * The identifier used to look the player up on stats.eldewrito.org:
 * a numeric stats id when present, otherwise a hex uid that still has to be resolved.
 */
export function playerCandidateUid(p: PlayerLike): string | null {
    for (const v of [p.id, p.playerId, p.player_id, p.serviceId, p.service_id]) {
        if (v !== undefined && v !== null && /^\d+$/.test(String(v))) {
            return String(v);
        }
    }

    for (const v of [p.uid, p.uniqueId, p.xuid, p.serviceUid, p.service_uid]) {
        if (typeof v === 'string' && /^[0-9a-fA-F]+$/.test(v)) {
            return v;
        }
    }

    return null;
}

/** Row background: team colour when teams are on, otherwise the player's primary colour. */
export function playerColor(p: PlayerLike, teamsEnabled: boolean): string {
    if (teamsEnabled) {
        const color = teamColor(playerTeam(p), '');

        if (color) {
            return color;
        }
    }

    const v = p.primaryColor ?? p.primary_color ?? p.color ?? p.colorPrimary ?? p.primaryColour ?? p.primary_colour ?? null;

    if (!v) {
        return '#424242';
    }

    if (Array.isArray(v) && v.length >= 3) {
        return `rgb(${v[0]}, ${v[1]}, ${v[2]})`;
    }

    if (typeof v === 'object' && v !== null && 'r' in v) {
        const rgb = v as { r: number; g?: number; b?: number };

        return `rgb(${rgb.r}, ${rgb.g ?? 0}, ${rgb.b ?? 0})`;
    }

    if (typeof v === 'string') {
        return /^[0-9a-fA-F]{6}$/.test(v) ? `#${v}` : v;
    }

    return String(v);
}

/** Scoreboard order: score, then kills, then fewest deaths, then name. */
export function comparePlayers(a: PlayerLike, b: PlayerLike): number {
    return (
        playerScore(b) - playerScore(a) ||
        playerKills(b) - playerKills(a) ||
        playerDeaths(a) - playerDeaths(b) ||
        playerName(a).localeCompare(playerName(b))
    );
}
