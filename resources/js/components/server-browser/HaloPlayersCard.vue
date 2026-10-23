<script setup lang="ts">
import Scoreboard from '@/components/server-browser/Scoreboard.vue';
import { groupBy, sortGroups, type ScoreboardGroup, type ScoreboardPlayer } from '@/lib/scoreboard';
import { GAMESPY_PLAYER_ROW_COLOR, TEAM_NAMES, teamColor, toTeamIndex } from '@/lib/teams';
import { computed, h } from 'vue';

/**
 * Scoreboard popover for GameSpy (Halo CE / Halo PC) servers. Players arrive as
 * flat player_N / score_N / team_N keys in the server info.
 */
const props = defineProps<{
    numPlayers: number;
    maxPlayers: number;
    info?: Record<string, unknown>;
}>();

interface Player {
    name: string;
    score: number;
    team: number | null;
}

function toNumber(v: unknown): number {
    const n = Number(v);

    return Number.isFinite(n) ? n : 0;
}

/** Scores are numbers, except in timed gametypes where they are "m:ss" strings. */
function parseScore(raw: unknown): number {
    const time = typeof raw === 'string' ? raw.trim().match(/(\d+)?:(\d{1,2})$/) : null;

    return time ? toNumber(time[1]) * 60 + toNumber(time[2]) : toNumber(raw);
}

const teamsEnabled = computed(() => props.info?.team_t0 !== undefined || props.info?.team_t1 !== undefined);

const players = computed<Player[]>(() => {
    const info = props.info ?? {};
    const list: Player[] = [];

    for (let i = 0; i < props.numPlayers; i++) {
        const name = info[`player_${i}`];

        if (name !== undefined && name !== null) {
            list.push({ name: String(name), score: parseScore(info[`score_${i}`]), team: toTeamIndex(info[`team_${i}`]) });
        }
    }

    return list;
});

const byScore = (a: Player, b: Player) => b.score - a.score;

const toRow = (p: Player): ScoreboardPlayer => ({
    cell: h('div', { class: 'player-cell' }, h('div', { class: 'player-info' }, h('span', { class: 'player-name' }, p.name))),
    stats: [p.score],
    color: teamsEnabled.value ? teamColor(p.team) : GAMESPY_PLAYER_ROW_COLOR,
});

const groups = computed<ScoreboardGroup[]>(() => {
    if (!teamsEnabled.value) {
        return [{ team: null, totals: [], players: [...players.value].sort(byScore).map(toRow) }];
    }

    const groups = [...groupBy(players.value, (p) => p.team)].map(([team, members]) => {
        const reported = team !== null ? props.info?.[`score_t${team}`] : undefined;
        const score = reported !== undefined ? toNumber(reported) : members.reduce((acc, p) => acc + p.score, 0);
        const label = String(props.info?.[`team_t${team}`] || (team !== null && TEAM_NAMES[team]) || `Team ${team}`);

        return { team, score, label, totals: [score], players: members.sort(byScore).map(toRow) };
    });

    return sortGroups(groups, (a, b) => b.score - a.score);
});
</script>

<template>
    <Scoreboard
        :num-players="numPlayers"
        :max-players="maxPlayers"
        :columns="[{ label: 'Score' }]"
        :groups="groups"
        :teams="teamsEnabled"
        max-width="300px"
    />
</template>
