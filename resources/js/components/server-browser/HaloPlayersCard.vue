<script setup lang="ts">
import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { usePopoverToggle } from '@/composables/usePopoverToggle';
import { TEAM_NAMES, teamColor, toTeamIndex } from '@/lib/teams';
import { computed } from 'vue';
import '../../../css/PlayersCard.css';

/**
 * Scoreboard popover for GameSpy (Halo CE / Halo PC) servers. Players arrive as
 * flat player_N / score_N / team_N keys in the server info.
 */
const props = defineProps<{
    numPlayers: number;
    maxPlayers: number;
    info?: Record<string, unknown>;
}>();

const { open, toggle } = usePopoverToggle();

interface Player {
    name: string;
    score: number;
    team: number | null;
}

function toNumber(v: unknown, fallback = 0): number {
    const n = Number(v);

    return Number.isFinite(n) ? n : fallback;
}

/** "m:ss" or ":ss" (also at the end of a longer string) to seconds; null when there is no colon. */
function parseTimeToSeconds(v: unknown): number | null {
    const match = String(v)
        .trim()
        .match(/(\d+)?:(\d{1,2})$/);

    if (!match) {
        return null;
    }

    const mins = match[1] !== undefined ? parseInt(match[1], 10) : 0;
    const secs = parseInt(match[2], 10);

    return Number.isNaN(mins) || Number.isNaN(secs) ? null : mins * 60 + secs;
}

/** Scores are numbers, except in timed gametypes where they are "m:ss" strings. */
function parseScore(raw: unknown): number {
    if (raw === undefined || raw === null) {
        return 0;
    }

    if (typeof raw === 'number') {
        return toNumber(raw);
    }

    return parseTimeToSeconds(raw) ?? toNumber(raw);
}

const players = computed<Player[]>(() => {
    const info = props.info;

    if (!info) {
        return [];
    }

    const list: Player[] = [];

    for (let i = 0; i < props.numPlayers; i++) {
        const name = info[`player_${i}`];

        if (name === undefined || name === null) {
            continue;
        }

        list.push({ name: String(name), score: parseScore(info[`score_${i}`]), team: toTeamIndex(info[`team_${i}`]) });
    }

    return list;
});

const teamsEnabled = computed(() => props.info?.team_t0 !== undefined || props.info?.team_t1 !== undefined);

interface TeamGroup {
    team: number | null;
    players: Player[];
    teamScore: number;
}

const groups = computed<TeamGroup[]>(() => {
    if (!teamsEnabled.value) {
        return [{ team: null, players: [...players.value].sort((a, b) => b.score - a.score), teamScore: 0 }];
    }

    const byTeam = new Map<number | null, Player[]>();

    for (const p of players.value) {
        byTeam.set(p.team, [...(byTeam.get(p.team) ?? []), p]);
    }

    const result: TeamGroup[] = [];

    for (const [team, members] of byTeam) {
        members.sort((a, b) => b.score - a.score);

        const reported = team !== null ? props.info?.[`score_t${team}`] : undefined;
        const teamScore = reported !== undefined ? toNumber(reported) : members.reduce((acc, p) => acc + p.score, 0);

        result.push({ team, players: members, teamScore });
    }

    return result.sort((a, b) => {
        if (a.team === null && b.team !== null) return 1;
        if (b.team === null && a.team !== null) return -1;

        return b.teamScore - a.teamScore;
    });
});

function teamLabel(team: number): string {
    return String(props.info?.[`team_t${team}`] || TEAM_NAMES[team] || `Team ${team}`);
}
</script>

<template>
    <template v-if="numPlayers > 0">
        <ClickPopover v-model:model-value="open" placement="bottom">
            <template #trigger>
                <button type="button" class="player-count-button cursor-pointer" @click.stop="toggle">{{ numPlayers }}/{{ maxPlayers }}</button>
            </template>

            <div class="playercard-content bg-background/100 backdrop-blur-xs dark:bg-background/100" style="max-width: 300px">
                <table class="scoreboard-table">
                    <thead>
                        <tr class="scoreboard-header">
                            <th class="players-count">Players [{{ numPlayers }}/{{ maxPlayers }}]</th>
                            <th class="stat-header">Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template v-for="(group, groupIdx) in groups" :key="group.team ?? 'none'">
                            <tr v-if="teamsEnabled && group.team !== null" class="team-row" :style="{ backgroundColor: teamColor(group.team) }">
                                <td class="team-info">
                                    <span class="team-number">{{ groupIdx + 1 }}</span>
                                    <span class="team-name">{{ teamLabel(group.team) }}</span>
                                </td>
                                <td class="stat-cell team-score">{{ group.teamScore }}</td>
                            </tr>
                            <tr
                                v-for="(p, idx) in group.players"
                                :key="(group.team ?? 'none') + '-' + idx"
                                class="player-row"
                                :style="{ backgroundColor: teamsEnabled ? teamColor(p.team) : '#666666' }"
                            >
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
