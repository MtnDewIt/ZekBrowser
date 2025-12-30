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
    serverVersion?: string;
}

const props = defineProps<Props>();

// Emblem cache
const emblemCache = reactive(new Map<string, string>());
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
    const candidates = [p.score, p.kills, p.points, p.pointsTotal, p.points_total, p.s];
    for (const c of candidates) {
        const n = Number(c);
        if (!Number.isNaN(n)) return n;
    }
    return 0;
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

        const totals = players.reduce((acc, it) => {
            acc.score += getPlayerScore(it.player);
            acc.kills += getPlayerKills(it.player);
            acc.deaths += getPlayerDeaths(it.player);
            return acc;
        }, { score: 0, kills: 0, deaths: 0 });

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
            <HoverCardTrigger as-child>
                <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
            </HoverCardTrigger>
            <HoverCardContent class="bg-background/100 dark:bg-background/100 backdrop-blur-xs">
                <h4 class="mb-4 text-foreground has-text-weight-semibold">Players</h4>
                <div class="text-base">
                    <template v-if="teamsEnabled">
                        <div v-for="group in groupedPlayers" :key="group.team ?? 'none'" class="mb-2">
                            <div v-if="group.team !== null" class="mb-1 text-xs font-semibold">
                                <span class="player-label team-label" :style="{ '--team-bg': TEAM_COLORS[group.team], '--team-fg': textColorForBackground(TEAM_COLORS[group.team] || '#fff') }">{{ TEAM_NAMES[group.team] ? (TEAM_NAMES[group.team] + ' Team') : ('Team ' + group.team) }} ({{ group.players.length }})</span>
                            </div>
                            <ul class="players-list">
                                <li v-for="({ player: p, emblemStr }, idx) in group.players" :key="(group.team ?? 'none') + '-' + idx" class="block text-base m-0 p-0">
                                    <template v-if="typeof p === 'object' && p !== null">
                                        <div class="w-full player-row" :style="{ '--player-bg': resolvePlayerColor(p), '--player-fg': textColorForBackground(resolvePlayerColor(p)) }">
                                            <div class="row-inner w-full">
                                                <img :src="getDisplayEmblemSrc(emblemStr)" class="flex-shrink-0 player-emblem" alt="emblem" decoding="async" />
                                                <div class="flex-1 px-1 flex items-center">
                                                    <span class="font-semibold truncate text-base player-label">{{ p?.name ?? p?.playerName ?? p?.displayName ?? p?.player_name ?? JSON.stringify(p) }}</span>
                                                </div>
                                                <div v-if="p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag" class="text-xs px-1 flex items-center">
                                                    <span class="text-base player-label">{{ p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag }}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </template>
                                    <template v-else>
                                        <span class="truncate">{{ p }}</span>
                                    </template>
                                </li>
                            </ul>
                        </div>
                    </template>
                    <template v-else>
                        <ul class="players-list">
                            <li v-for="({ player: p, emblemStr }, index) in sortedPlayers" :key="index" class="block text-base m-0 p-0">
                                <template v-if="typeof p === 'object' && p !== null">
                                    <div class="w-full player-row" :style="{ '--player-bg': resolvePlayerColor(p), '--player-fg': textColorForBackground(resolvePlayerColor(p)) }">
                                        <div class="row-inner w-full">
                                            <img :src="getDisplayEmblemSrc(emblemStr)" class="flex-shrink-0 player-emblem" alt="emblem" decoding="async" />
                                            <div class="flex-1 px-1 flex items-center">
                                                <span class="font-semibold truncate text-base player-label">{{ p.name ?? p.playerName ?? p.displayName ?? p.player_name ?? JSON.stringify(p) }}</span>
                                            </div>
                                            <div v-if="p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag" class="text-xs px-1 flex items-center">
                                                <span class="text-base player-label">{{ p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag }}</span>
                                            </div>
                                        </div>
                                    </div>
                                </template>
                                <template v-else>
                                    <span class="truncate">{{ p }}</span>
                                </template>
                            </li>
                        </ul>
                    </template>
                </div>
            </HoverCardContent>
        </HoverCard>
    </template>
    <template v-else>
        <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
    </template>
</template>
