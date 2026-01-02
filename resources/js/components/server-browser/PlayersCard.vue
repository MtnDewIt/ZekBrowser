<script setup lang="ts">
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import generateEmblem from '@/lib/emblemGenerator';
import { reactive, computed } from 'vue';
import '../../../css/PlayersCard.css';

interface Props {
    numPlayers: number;
    maxPlayers: number;
    players?: any[];
    teams?: boolean | string | number;
    teamScores?: number[];
    serverVersion?: string;
    passworded?: boolean;
}

const props = defineProps<Props>();
const passworded = computed(() => !!props.passworded);

// Emblem cache
const emblemCache = reactive(new Map<string, string>());
const resolvedStats = reactive(new Map<string, string>());
const resolvedRanks = reactive(new Map<string, number>());
const resolvedStatsTimestamps = reactive(new Map<string, number>());
const resolvedRanksTimestamps = reactive(new Map<string, number>());
const CACHE_TTL_MS = 1000 * 60 * 60 * 24; // 24 hours
const RANK_CACHE_TTL_MS = 1000 * 60 * 30; // 30 minutes
async function ensureEmblem(emblem: string | null | undefined) {
    if (!emblem) return;
    if (emblemCache.has(emblem)) return;
    emblemCache.set(emblem, '');
    try {
        if (typeof emblem === 'string' && (emblem.startsWith('data:') || emblem.startsWith('http://') || emblem.startsWith('https://') || emblem.startsWith('/'))) {
            emblemCache.set(emblem, emblem);
            return;
        }
        const url = await generateEmblem(emblem);
        emblemCache.set(emblem, url);
    }
    catch {}
}
function getEmblemSrc(emblem: string | null | undefined) {
    if (!emblem) return '';
    return emblemCache.get(emblem) ?? '';
}
function getDisplayEmblemSrc(emblem: string | null | undefined) {
    const src = getEmblemSrc(emblem);
    return src || '/assets/emblems/default.png';
}
function getEmblemString(p: any) {
    if (typeof p !== 'object' || p === null) return null;
    return p.emblem ?? p.emblemUrl ?? p.emblem_url ?? p.emblemString ?? null;
}

// Extract potential UID (hex) or numeric id from player object (simplified)
function getCandidateUid(p: any): string | null {
    if (!p || typeof p !== 'object') return null;

    // Prefer numeric stats ID if present
    const numericFields = [p.id, p.playerId, p.player_id, p.serviceId, p.service_id];
    for (const n of numericFields) {
        if (n === undefined || n === null) continue;
        const s = String(n);
        if (/^\d+$/.test(s)) return s;
    }

    // Prefer common uid fields for 0.7+ servers
    const uidFields = [p.uid, p.uniqueId, p.xuid, p.serviceUid, p.service_uid];
    for (const u of uidFields) {
        if (!u) continue;
        if (typeof u === 'string' && /^[0-9a-fA-F]+$/.test(u)) return u;
    }

    return null;
}

async function resolveStatsIdFromUid(uid: string): Promise<string | null> {
    try {
        const now = Date.now();
        const cached = resolvedStats.get(uid);
        const ts = resolvedStatsTimestamps.get(uid) ?? 0;
        if (cached && (now - ts) < CACHE_TTL_MS) return cached;

        const resp = await fetch(`/api/servicerecord?uid=${encodeURIComponent(uid)}`);
        if (!resp.ok) return null;
        const data = await resp.json();

        if (!data) return null;
        // Expect { id: 123 } or { player: { id: 123 } }
        if (data.id && (typeof data.id === 'number' || typeof data.id === 'string')) {
            const s = String(data.id);
            if (/^\d+$/.test(s)) {
                resolvedStats.set(uid, s);
                resolvedStatsTimestamps.set(uid, Date.now());
                // capture rank if present at top-level when id is returned
                if (data.rank !== null && data.rank !== undefined && (typeof data.rank === 'number' || (typeof data.rank === 'string' && /^\d+$/.test(String(data.rank))))) {
                    try { 
                        resolvedRanks.set(uid, Number(data.rank));
                        resolvedRanksTimestamps.set(uid, Date.now());
                    } catch {}
                }
                return s;
            }
        }
        if (data.player && data.player.id && (typeof data.player.id === 'number' || typeof data.player.id === 'string')) {
            const s = String(data.player.id);
            if (/^\d+$/.test(s)) {
                resolvedStats.set(uid, s);
                resolvedStatsTimestamps.set(uid, Date.now());
                // store rank if present on nested player
                if (data.player.rank !== null && data.player.rank !== undefined && (typeof data.player.rank === 'number' || (typeof data.player.rank === 'string' && /^\d+$/.test(String(data.player.rank))))) {
                    resolvedRanks.set(uid, Number(data.player.rank));
                    resolvedRanksTimestamps.set(uid, Date.now());
                }
                return s;
            }
        }

        // also capture top-level rank if present
        if (data.rank !== null && data.rank !== undefined && (typeof data.rank === 'number' || (typeof data.rank === 'string' && /^\d+$/.test(String(data.rank))))) {
            try {
                resolvedRanks.set(uid, Number(data.rank));
                resolvedRanksTimestamps.set(uid, Date.now());
            } catch {}
        }

        return null;
    } catch {
        return null;
    }
}

    async function preloadAllPlayers() {
        if (!props.players || !Array.isArray(props.players)) return;
        const items = props.players.slice();
        const candidates: string[] = [];
        for (const p of items) {
            const c = getCandidateUid(p);
            if (!c) continue;
            if (/^\d+$/.test(c)) continue;
            const ts = resolvedStatsTimestamps.get(c) ?? 0;
            if (resolvedStats.has(c) && (Date.now() - ts) < CACHE_TTL_MS) continue;
            candidates.push(c);
        }

        const CONCURRENCY = 6;
        for (let i = 0; i < candidates.length; i += CONCURRENCY) {
            const batch = candidates.slice(i, i + CONCURRENCY).map(uid => resolveStatsIdFromUid(uid));
            // Fire the batch and await to avoid rate-limiting
            await Promise.all(batch);
        }
    }

function getHrefForPlayer(p: any): string {
    const candidate = getCandidateUid(p);
    if (!candidate) return '#';
    if (/^\d+$/.test(candidate)) return `https://stats.eldewrito.org/player/${candidate}`;
    const resolved = resolvedStats.get(candidate);
    if (resolved) return `https://stats.eldewrito.org/player/${resolved}`;
    return '#';
}

async function preloadStatsHref(p: any) {
    const candidate = getCandidateUid(p);
    if (!candidate) return;
    if (/^\d+$/.test(candidate)) return; // already numeric

    // Only attempt resolve for 0.7+ servers
    function getServerVersionString(): string | null {
        const s = serverVersionProp.value;
        if (s && s.trim() !== '') return s;
        if (props.players && Array.isArray(props.players)) {
            for (const pp of props.players) {
                const v = pp?.eldewritoVersionShort ?? pp?.eldewritoVersion ?? pp?.gameVersion ?? null;
                if (v) return String(v);
            }
        }
        return null;
    }

    function isVersionAtLeast(versionStr: string | null, minMajor: number, minMinor: number): boolean {
        if (!versionStr) return false;
        const m = versionStr.match(/^(\d+)\.(\d+)/);
        if (!m) return false;
        const major = Number(m[1]);
        const minor = Number(m[2]);
        if (Number.isNaN(major) || Number.isNaN(minor)) return false;
        if (major > minMajor) return true;
        if (major < minMajor) return false;
        return minor >= minMinor;
    }

    const serverVer = getServerVersionString();
    if (!isVersionAtLeast(serverVer, 0, 7)) return;

    if (resolvedStats.has(candidate)) return;
    const resolved = await resolveStatsIdFromUid(candidate);
    if (resolved) resolvedStats.set(candidate, resolved);
}

async function openStatsForPlayer(p: any) {
    const href = getHrefForPlayer(p);
    if (href && href !== '#') {
        window.open(href, '_blank');
    } else {
        console.warn('Player stats unavailable or not supported on this server');
    }
}

// Team colors from the user's C# code
const TEAM_COLORS = [
    '#9b3332', // 0
    '#325992', // 1
    '#1F3602', // 2
    '#BC4D00', // 3
    '#1D1052', // 4
    '#A77708', // 5
    '#1C0D02', // 6
    '#FF4D8A', // 7
];

// Friendly team names matching indices 0..7
const TEAM_NAMES = [
    'Red',   // 0
    'Blue',  // 1
    'Green', // 2
    'Orange',// 3
    'Purple',// 4
    'Gold',  // 5
    'Brown', // 6
    'Pink',  // 7
];

const teamsEnabled = computed(() => {
    const v = props.teams;
    return v === true || v === 'true' || v === 1 || v === '1';
});

// Determine whether server is old (0.5.1.1). Prefer explicit prop, fall back to player fields.
const serverVersionProp = computed(() => String(props.serverVersion ?? '').trim());
const isOldServerVersion = computed(() => {
    if (serverVersionProp.value === '0.5.1.1') return true;
    if (!props.players || !Array.isArray(props.players)) return false;
    for (const p of props.players) {
        const v = p?.eldewritoVersionShort ?? p?.eldewritoVersion ?? p?.gameVersion ?? null;
        if (v === '0.5.1.1') return true;
    }
    return false;
});

function getServerVersionString(): string | null {
    const s = serverVersionProp.value;
    if (s && s.trim() !== '') return s;
    if (props.players && Array.isArray(props.players)) {
        for (const pp of props.players) {
            const v = pp?.eldewritoVersionShort ?? pp?.eldewritoVersion ?? pp?.gameVersion ?? null;
            if (v) return String(v);
        }
    }
    return null;
}

function isVersionAtLeast(versionStr: string | null, minMajor: number, minMinor: number): boolean {
    if (!versionStr) return false;
    const m = versionStr.match(/^(\d+)\.(\d+)/);
    if (!m) return false;
    const major = Number(m[1]);
    const minor = Number(m[2]);
    if (Number.isNaN(major) || Number.isNaN(minor)) return false;
    if (major > minMajor) return true;
    if (major < minMajor) return false;
    return minor >= minMinor;
}

const canResolveUids = computed(() => isVersionAtLeast(getServerVersionString(), 0, 7));

function isClickablePlayer(p: any): boolean {
    // Never clickable unless server supports UID resolution (0.7+)
    if (!canResolveUids.value) return false;
    const candidate = getCandidateUid(p);
    return !!candidate;
}

function textColorForBackground(color: string) {
    // Always use white text for player entries to ensure readability
    return '#ffffff';
}

function resolvePlayerColor(p: any) {
    // If teams mode is enabled and player has a team index, use the team color
    try {
        if (teamsEnabled.value) {
            const teamVal = p?.team ?? p?.teamIndex ?? p?.team_number ?? p?.teamNumber ?? null;
            if (teamVal !== null && teamVal !== undefined) {
                const idx = Number(teamVal);
                if (!Number.isNaN(idx) && idx >= 0 && idx < TEAM_COLORS.length) {
                    return TEAM_COLORS[idx];
                }
            }
        }
    }
    catch {}

    const v = p?.primaryColor ?? p?.primary_color ?? p?.color ?? p?.colorPrimary ?? p?.primaryColour ?? p?.primary_colour ?? null;
    if (!v) return '#424242';
    if (Array.isArray(v) && v.length >= 3) return `rgb(${v[0]}, ${v[1]}, ${v[2]})`;
    if (typeof v === 'object' && v !== null && v.r !== undefined) return `rgb(${v.r}, ${v.g ?? 0}, ${v.b ?? 0})`;
    if (typeof v === 'string') {
        if (/^[0-9a-fA-F]{6}$/.test(v)) return `#${v}`;
        return v;
    }
    return String(v);
}

function getPlayerScore(p: any) {
    if (!p || typeof p !== 'object') return 0;
    const n = Number(p.roundScore);
    return Number.isNaN(n) ? 0 : n;
}

function getPlayerKills(p: any) {
    if (!p || typeof p !== 'object') return 0;
    const candidates = [p.kills, p.k, p.killCount, p.kill_count];
    for (const c of candidates) {
        const n = Number(c);
        if (!Number.isNaN(n)) return n;
    }
    return 0;
}

function getPlayerDeaths(p: any) {
    if (!p || typeof p !== 'object') return 0;
    const candidates = [p.deaths, p.d, p.deathCount, p.death_count];
    for (const c of candidates) {
        const n = Number(c);
        if (!Number.isNaN(n)) return n;
    }
    return 0;
}

function getPlayerAssists(p: any) {
    if (!p || typeof p !== 'object') return 0;
    const candidates = [p.assists, p.a, p.assistCount, p.assist_count];
    for (const c of candidates) {
        const n = Number(c);
        if (!Number.isNaN(n)) return n;
    }
    return 0;
}

function getPlayerBestStreak(p: any) {
    if (!p || typeof p !== 'object') return 0;
    const candidates = [p.bestStreak, p.best_streak, p.killingSpree, p.killing_spree, p.streak, p.maxStreak, p.max_streak];
    for (const c of candidates) {
        const n = Number(c);
        if (!Number.isNaN(n)) return n;
    }
    return 0;
}

function getPlayerRank(p: any): number | null {
    if (!p || typeof p !== 'object') return null;
    
    // Check for rank field directly
    if ('rank' in p) {
        const n = Number(p.rank);
        if (!Number.isNaN(n) && n >= 0) return n;
    }
    
    // Try other field names
    const rankFields = ['playerRank', 'service_rank', 'serviceRank'];
    for (const field of rankFields) {
        if (field in p) {
            const n = Number(p[field]);
            if (!Number.isNaN(n) && n >= 0) return n;
        }
    }
    
    // Try resolvedRanks cache via UID
    const candidate = getCandidateUid(p);
    if (candidate) {
        const cached = resolvedRanks.get(candidate);
        if (typeof cached === 'number' && cached >= 0) {
            // Validate timestamp
            const timestamp = resolvedRanksTimestamps.get(candidate);
            if (timestamp && (Date.now() - timestamp < RANK_CACHE_TTL_MS)) {
                return cached;
            }
            // Cache expired, remove it
            resolvedRanks.delete(candidate);
            resolvedRanksTimestamps.delete(candidate);
        }
    }
    
    return null;
}

// Pre-load emblems for all players
const processedPlayers = computed(() => {
    if (!props.players) return [];
    return props.players.map(p => {
        const emblemStr = getEmblemString(p);
        if (emblemStr) void ensureEmblem(emblemStr);
        return { player: p, emblemStr };
    });
});

// Sorted flat list when teams are not enabled
const sortedPlayers = computed(() => {
    const items = processedPlayers.value.slice();
    items.sort((a, b) => {
        const pa = a.player, pb = b.player;
        const sa = getPlayerScore(pa), sb = getPlayerScore(pb);
        if (sb !== sa) return sb - sa;
        const ka = getPlayerKills(pa), kb = getPlayerKills(pb);
        if (kb !== ka) return kb - ka;
        const da = getPlayerDeaths(pa), db = getPlayerDeaths(pb);
        if (da !== db) return da - db;
        return String(pa.name ?? pa.playerName ?? '').localeCompare(String(pb.name ?? pb.playerName ?? ''));
    });
    return items;
});

// Group players by team and compute team totals and sorting
const groupedPlayers = computed(() => {
    if (!props.players) return [];
    if (!teamsEnabled.value) return [];

    const groups = new Map<number|null, Array<any>>();
    for (const item of processedPlayers.value) {
        const p = item.player;
        const teamVal = p?.team ?? p?.teamIndex ?? p?.team_number ?? p?.teamNumber ?? null;
        const idx = teamVal === null || teamVal === undefined ? null : Number(teamVal);
        const key = (idx === null || Number.isNaN(idx)) ? null : idx;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key)!.push(item);
    }

    const arr: Array<any> = [];
    for (const [team, players] of groups.entries()) {
        // sort players within team
        players.sort((a, b) => {
            const pa = a.player, pb = b.player;
            const sa = getPlayerScore(pa), sb = getPlayerScore(pb);
            if (sb !== sa) return sb - sa;
            const ka = getPlayerKills(pa), kb = getPlayerKills(pb);
            if (kb !== ka) return kb - ka;
            const da = getPlayerDeaths(pa), db = getPlayerDeaths(pb);
            if (da !== db) return da - db;
            return String(pa.name ?? pa.playerName ?? '').localeCompare(String(pb.name ?? pb.playerName ?? ''));
        });

        const totals = {
            score: (props.teamScores && team !== null && team >= 0 && team < props.teamScores.length) 
                ? props.teamScores[team] 
                : players.reduce((acc, it) => acc + getPlayerScore(it.player), 0),
            kills: players.reduce((acc, it) => acc + getPlayerKills(it.player), 0),
            deaths: players.reduce((acc, it) => acc + getPlayerDeaths(it.player), 0)
        };

        arr.push({ team, players, totals });
    }

    // sort teams: by score desc, kills desc, deaths asc; null team (no team) goes last
    arr.sort((a, b) => {
        if (a.team === null && b.team !== null) return 1;
        if (b.team === null && a.team !== null) return -1;
        if (a.totals.score !== b.totals.score) return b.totals.score - a.totals.score;
        if (a.totals.kills !== b.totals.kills) return b.totals.kills - a.totals.kills;
        return a.totals.deaths - b.totals.deaths;
    });

    return arr;
});
</script>

<template>
    <template v-if="numPlayers > 0">
        <HoverCard>
            <HoverCardTrigger as-child @mouseenter="preloadAllPlayers">
                <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
            </HoverCardTrigger>
            <HoverCardContent class="playercard-content bg-background/100 dark:bg-background/100 backdrop-blur-xs">
                <template v-if="passworded">
                    <div class="text-sm text-muted-foreground">Private Server</div>
                </template>
                <template v-else>
                    <table class="scoreboard-table">
                        <thead>
                            <tr class="scoreboard-header">
                                <th class="players-count">Players [{{ numPlayers }}/{{ maxPlayers }}]</th>
                                <th class="stat-header">Kills</th>
                                <th class="stat-header">Assists</th>
                                <th class="stat-header">Deaths</th>
                                <th class="stat-header">Best Streak</th>
                                <th class="stat-header">Score</th>
                            </tr>
                        </thead>
                        <tbody>
                            <template v-if="teamsEnabled">
                                <template v-for="(group, groupIdx) in groupedPlayers" :key="group.team ?? 'none'">
                                    <tr v-if="group.team !== null" class="team-row" :style="{ backgroundColor: TEAM_COLORS[group.team] }">
                                        <td class="team-info">
                                            <span class="team-number">{{ groupIdx + 1 }}</span>
                                            <span class="team-name">{{ TEAM_NAMES[group.team] ? (TEAM_NAMES[group.team] + ' Team') : ('Team ' + group.team) }}</span>
                                        </td>
                                        <td class="stat-cell"></td>
                                        <td class="stat-cell"></td>
                                        <td class="stat-cell"></td>
                                        <td class="stat-cell"></td>
                                        <td class="stat-cell team-score">{{ group.totals.score }}</td>
                                    </tr>
                                    <tr v-for="({ player: p, emblemStr }, idx) in group.players" :key="(group.team ?? 'none') + '-' + idx" class="player-row" :style="{ backgroundColor: resolvePlayerColor(p) }">
                                        <template v-if="typeof p === 'object' && p !== null">
                                            <td>
                                                <div class="player-cell">
                                                    <img :src="getDisplayEmblemSrc(emblemStr)" class="player-emblem" alt="emblem" decoding="async" />
                                                    <div class="player-info">
                                                        <template v-if="isClickablePlayer(p)">
                                                            <a class="player-name player-link" :href="getHrefForPlayer(p)" target="_blank" @click.prevent="openStatsForPlayer(p)" @mouseenter.prevent="preloadStatsHref(p)">
                                                                {{ p?.name ?? p?.playerName ?? p?.displayName ?? p?.player_name ?? 'Unknown' }}
                                                            </a>
                                                        </template>
                                                        <template v-else>
                                                            <span class="player-name">{{ p?.name ?? p?.playerName ?? p?.displayName ?? p?.player_name ?? 'Unknown' }}</span>
                                                        </template>
                                                    </div>
                                                    <div class="player-tags">
                                                        <span v-if="p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag" class="service-tag">
                                                            {{ p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag }}
                                                        </span>
                                                        <img v-if="getPlayerRank(p) !== null" :src="`/assets/ranks/${getPlayerRank(p)}.svg`" class="player-rank-icon" alt="rank" decoding="async" />
                                                    </div>
                                                </div>
                                            </td>
                                            <td class="stat-cell">{{ getPlayerKills(p) }}</td>
                                            <td class="stat-cell">{{ getPlayerAssists(p) }}</td>
                                            <td class="stat-cell">{{ getPlayerDeaths(p) }}</td>
                                            <td class="stat-cell">{{ getPlayerBestStreak(p) }}</td>
                                            <td class="stat-cell">{{ getPlayerScore(p) }}</td>
                                        </template>
                                        <template v-else>
                                            <td colspan="6">{{ p }}</td>
                                        </template>
                                    </tr>
                                </template>
                            </template>
                            <template v-else>
                                <tr v-for="({ player: p, emblemStr }, index) in sortedPlayers" :key="index" class="player-row" :style="{ backgroundColor: resolvePlayerColor(p) }">
                                    <template v-if="typeof p === 'object' && p !== null">
                                        <td>
                                            <div class="player-cell">
                                                <img :src="getDisplayEmblemSrc(emblemStr)" class="player-emblem" alt="emblem" decoding="async" />
                                                <div class="player-info">
                                                    <template v-if="isClickablePlayer(p)">
                                                        <a class="player-name player-link" :href="getHrefForPlayer(p)" target="_blank" @click.prevent="openStatsForPlayer(p)" @mouseenter.prevent="preloadStatsHref(p)">
                                                            {{ p?.name ?? p?.playerName ?? p?.displayName ?? p?.player_name ?? 'Unknown' }}
                                                        </a>
                                                    </template>
                                                    <template v-else>
                                                        <span class="player-name">{{ p?.name ?? p?.playerName ?? p?.displayName ?? p?.player_name ?? 'Unknown' }}</span>
                                                    </template>
                                                </div>
                                                <div class="player-tags">
                                                    <span v-if="p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag" class="service-tag">
                                                        {{ p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag }}
                                                    </span>
                                                    <img v-if="getPlayerRank(p) !== null" :src="`/assets/ranks/${getPlayerRank(p)}.svg`" class="player-rank-icon" alt="rank" decoding="async" />
                                                </div>
                                            </div>
                                        </td>
                                        <td class="stat-cell">{{ getPlayerKills(p) }}</td>
                                        <td class="stat-cell">{{ getPlayerAssists(p) }}</td>
                                        <td class="stat-cell">{{ getPlayerDeaths(p) }}</td>
                                        <td class="stat-cell">{{ getPlayerBestStreak(p) }}</td>
                                        <td class="stat-cell">{{ getPlayerScore(p) }}</td>
                                    </template>
                                    <template v-else>
                                        <td colspan="6">{{ p }}</td>
                                    </template>
                                </tr>
                            </template>
                        </tbody>
                    </table>
                </template>
            </HoverCardContent>
        </HoverCard>
    </template>
    <template v-else>
        <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
    </template>
</template>
