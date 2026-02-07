<script setup lang="ts">

import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { computed, ref } from 'vue';
import '../../../css/PlayersCard.css';

interface Props 
{
    numPlayers: number;
    maxPlayers: number;
    info?: Record<string, any>;
}

const props = defineProps<Props>();

const TEAM_COLORS = 
[
    '#9b3332',
    '#325992',
    '#1F3602',
    '#BC4D00',
    '#1D1052',
    '#A77708',
    '#1C0D02',
    '#FF4D8A',
];

const TEAM_NAMES = 
[
    'Red',
    'Blue',
    'Green',
    'Orange',
    'Purple',
    'Gold',
    'Brown',
    'Pink',
];

interface Player {
    name: string;
    score: number;
    team: number | null;
}

// Parse player_0, player_1, etc. from info
const parsedPlayers = computed<Player[]>(() => {
    if (!props.info || typeof props.info !== 'object') {
        return [];
    }

    const players: Player[] = [];
    const info = props.info;

    for (let i = 0; i < props.numPlayers; i++) {
        const nameKey = `player_${i}`;
        const scoreKey = `score_${i}`;
        const teamKey = `team_${i}`;

        const name = info[nameKey];
        if (name === undefined || name === null) continue;

        const score = Number(info[scoreKey] ?? 0);
        const teamRaw = info[teamKey];
        const team = teamRaw !== undefined && teamRaw !== null ? Number(teamRaw) : null;

        players.push({ name: String(name), score, team });
    }

    return players;
});

// Check if teams are enabled by looking for team_t0 or team_t1 fields
const teamsEnabled = computed(() => {
    if (!props.info) return false;
    return props.info.team_t0 !== undefined || props.info.team_t1 !== undefined;
});

// Sort players by score descending
const sortedPlayers = computed(() => {
    const items = parsedPlayers.value.slice();
    items.sort((a, b) => b.score - a.score);
    return items;
});

// Group players by team
const groupedPlayers = computed(() => {
    if (!teamsEnabled.value) {
        return [];
    }

    const groups = new Map<number | null, Player[]>();

    for (const p of parsedPlayers.value) {
        const key = p.team;
        if (!groups.has(key)) {
            groups.set(key, []);
        }
        groups.get(key)!.push(p);
    }

    const arr: Array<any> = [];

    for (const [team, players] of groups.entries()) {
        players.sort((a, b) => b.score - a.score);

        const teamScore = team !== null && props.info?.[`score_t${team}`] !== undefined
            ? Number(props.info[`score_t${team}`])
            : players.reduce((acc, p) => acc + p.score, 0);

        arr.push({ team, players, teamScore });
    }

    arr.sort((a, b) => {
        if (a.team === null && b.team !== null) return 1;
        if (b.team === null && a.team !== null) return -1;
        return b.teamScore - a.teamScore;
    });

    return arr;
});

const open = ref(false);
const _ignoreOpenUntil = ref(0);

function toggleOpen() {
    const now = Date.now();

    if (open.value) {
        open.value = false;
        _ignoreOpenUntil.value = now + 300;
        return;
    }

    if (now < _ignoreOpenUntil.value) return;

    open.value = true;
}
</script>

<template>
    <template v-if="numPlayers > 0">
        <ClickPopover v-model:modelValue="open" placement="bottom">
            <template #trigger>
                <button
                    type="button"
                    class="player-count-button cursor-pointer"
                    @click.stop="toggleOpen"
                >
                    {{ numPlayers }}/{{ maxPlayers }}
                </button>
            </template>

            <div class="playercard-content bg-background/100 dark:bg-background/100 backdrop-blur-xs" style="max-width: 300px;">
                <table class="scoreboard-table">
                    <thead>
                        <tr class="scoreboard-header">
                            <th class="players-count">Players [{{ numPlayers }}/{{ maxPlayers }}]</th>
                            <th class="stat-header">Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template v-if="teamsEnabled">
                            <template v-for="(group, groupIdx) in groupedPlayers" :key="group.team ?? 'none'">
                                <tr v-if="group.team !== null" class="team-row" :style="{ backgroundColor: TEAM_COLORS[group.team] }">
                                    <td class="team-info">
                                        <span class="team-number">{{ groupIdx + 1 }}</span>
                                        <span class="team-name">
                                            {{ info?.[`team_t${group.team}`] || TEAM_NAMES[group.team] || ('Team ' + group.team) }}
                                        </span>
                                    </td>
                                    <td class="stat-cell team-score">{{ group.teamScore }}</td>
                                </tr>
                                <tr v-for="(p, idx) in group.players" :key="(group.team ?? 'none') + '-' + idx" class="player-row" :style="{ backgroundColor: p.team !== null && p.team >= 0 && p.team < TEAM_COLORS.length ? TEAM_COLORS[p.team] : 'transparent' }">
                                    <td>
                                        <div class="player-cell">
                                            <div class="player-info">
                                                <span class="player-name">{{ p.name }}</span>
                                            </div>
                                        </div>
                                    </td>
                                    <td class="stat-cell">{{ p.score }}</td>
                                </tr>
                            </template>
                        </template>
                        <template v-else>
                            <tr v-for="(p, index) in sortedPlayers" :key="index" class="player-row" style="background-color: #666666">
                                <td>
                                    <div class="player-cell">
                                        <div class="player-info">
                                            <span class="player-name">{{ p.name }}</span>
                                        </div>
                                    </div>
                                </td>
                                <td class="stat-cell">{{ p.score }}</td>
                            </tr>
                        </template>
                    </tbody>
                </table>
            </div>
        </ClickPopover>
    </template>
    <template v-else>
        <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
    </template>
</template>
