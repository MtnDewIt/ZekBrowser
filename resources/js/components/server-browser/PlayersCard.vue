<script setup lang="ts">
import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { usePopoverToggle } from '@/composables/usePopoverToggle';
import {
    comparePlayers,
    isPlayerObject,
    playerAssists,
    playerBestStreak,
    playerCandidateUid,
    playerColor,
    playerDeaths,
    playerEmblem,
    playerKills,
    playerName,
    playerScore,
    playerServiceTag,
    playerTeam,
    type PlayerLike,
} from '@/lib/eldewritoPlayers';
import { isVersionAtLeast, playerRank, playerStatsHref, preloadPlayerStats, resolveStatsId } from '@/lib/eldewritoStats';
import { emblemSrc, ensureEmblem } from '@/lib/emblemGenerator';
import { TEAM_NAMES, teamColor } from '@/lib/teams';
import { computed } from 'vue';
import '../../../css/PlayersCard.css';

/**
 * Scoreboard popover for an ElDewrito server.
 */
const props = defineProps<{
    numPlayers: number;
    maxPlayers: number;
    players?: unknown[];
    teams?: boolean | string | number;
    teamScores?: number[];
    serverVersion?: string;
    passworded?: boolean;
}>();

const { open, toggle } = usePopoverToggle(() => void preloadPlayerStats(props.players ?? []));

const teamsEnabled = computed(() => {
    const v = props.teams;

    return v === true || v === 'true' || v === 1 || v === '1';
});

/** Server version from the prop, else from whatever the players report. */
const serverVersion = computed<string | null>(() => {
    const fromProp = String(props.serverVersion ?? '').trim();

    if (fromProp) {
        return fromProp;
    }

    for (const p of props.players ?? []) {
        if (isPlayerObject(p)) {
            const v = p.eldewritoVersionShort ?? p.eldewritoVersion ?? p.gameVersion;

            if (v) {
                return String(v);
            }
        }
    }

    return null;
});

// Ranks and stats-site uids exist from ElDewrito 0.7 on.
const supportsStats = computed(() => isVersionAtLeast(serverVersion.value, 0, 7));

const objectPlayers = computed(() => (props.players ?? []).filter(isPlayerObject));

interface TeamGroup {
    team: number | null;
    players: PlayerLike[];
    totals: { score: number; kills: number; deaths: number };
}

const groups = computed<TeamGroup[]>(() => {
    if (!teamsEnabled.value) {
        return [{ team: null, players: [...objectPlayers.value].sort(comparePlayers), totals: { score: 0, kills: 0, deaths: 0 } }];
    }

    const byTeam = new Map<number | null, PlayerLike[]>();

    for (const p of objectPlayers.value) {
        const team = playerTeam(p);
        byTeam.set(team, [...(byTeam.get(team) ?? []), p]);
    }

    const result: TeamGroup[] = [];

    for (const [team, members] of byTeam) {
        members.sort(comparePlayers);

        const reportedScore = team !== null && props.teamScores && team >= 0 && team < props.teamScores.length ? props.teamScores[team] : undefined;

        result.push({
            team,
            players: members,
            totals: {
                score: reportedScore ?? members.reduce((acc, p) => acc + playerScore(p), 0),
                kills: members.reduce((acc, p) => acc + playerKills(p), 0),
                deaths: members.reduce((acc, p) => acc + playerDeaths(p), 0),
            },
        });
    }

    return result.sort((a, b) => {
        if (a.team === null && b.team !== null) return 1;
        if (b.team === null && a.team !== null) return -1;

        return b.totals.score - a.totals.score || b.totals.kills - a.totals.kills || a.totals.deaths - b.totals.deaths;
    });
});

/** Entries that are not objects (malformed player data) are shown raw at the end. */
const rawPlayers = computed(() => (props.players ?? []).filter((p) => !isPlayerObject(p)));

function emblemFor(p: PlayerLike): string {
    const emblem = playerEmblem(p);
    void ensureEmblem(emblem);

    return emblemSrc(emblem);
}

function isClickable(p: PlayerLike): boolean {
    return supportsStats.value && playerCandidateUid(p) !== null;
}

function preloadHref(p: PlayerLike) {
    const candidate = playerCandidateUid(p);

    if (supportsStats.value && candidate && !/^\d+$/.test(candidate)) {
        void resolveStatsId(candidate);
    }
}

function openStats(p: PlayerLike) {
    const href = playerStatsHref(p);

    if (href !== '#') {
        window.open(href, '_blank');
    } else {
        console.warn('Player stats unavailable or not supported on this server');
    }
}

function teamLabel(team: number): string {
    return TEAM_NAMES[team] ? `${TEAM_NAMES[team]} Team` : `Team ${team}`;
}
</script>

<template>
    <template v-if="numPlayers > 0">
        <ClickPopover v-model:model-value="open" placement="bottom">
            <template #trigger>
                <button type="button" class="player-count-button cursor-pointer" @click.stop="toggle">{{ numPlayers }}/{{ maxPlayers }}</button>
            </template>

            <div class="playercard-content bg-background/100 backdrop-blur-xs dark:bg-background/100">
                <div v-if="passworded" class="text-sm text-muted-foreground">Private Server</div>
                <table v-else class="scoreboard-table">
                    <thead>
                        <tr class="scoreboard-header">
                            <th class="players-count">Players [{{ numPlayers }}/{{ maxPlayers }}]</th>
                            <th class="stat-header">Kills</th>
                            <th class="stat-header stat-col-assists">Assists</th>
                            <th class="stat-header">Deaths</th>
                            <th class="stat-header stat-col-beststreak">Best Streak</th>
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
                                <td class="stat-cell"></td>
                                <td class="stat-cell stat-col-assists"></td>
                                <td class="stat-cell"></td>
                                <td class="stat-cell stat-col-beststreak"></td>
                                <td class="stat-cell team-score">{{ group.totals.score }}</td>
                            </tr>
                            <tr
                                v-for="(p, idx) in group.players"
                                :key="(group.team ?? 'none') + '-' + idx"
                                class="player-row"
                                :style="{ backgroundColor: playerColor(p, teamsEnabled) }"
                            >
                                <td>
                                    <div class="player-cell">
                                        <img :src="emblemFor(p)" class="player-emblem" alt="emblem" decoding="async" />
                                        <div class="player-info">
                                            <a
                                                v-if="isClickable(p)"
                                                class="player-name player-link"
                                                :href="playerStatsHref(p)"
                                                target="_blank"
                                                @click.prevent="openStats(p)"
                                                @mouseenter.prevent="preloadHref(p)"
                                            >
                                                {{ playerName(p) }}
                                            </a>
                                            <span v-else class="player-name">{{ playerName(p) }}</span>
                                        </div>
                                        <div class="player-tags">
                                            <span v-if="playerServiceTag(p)" class="service-tag">{{ playerServiceTag(p) }}</span>
                                            <img
                                                v-if="supportsStats && playerRank(p) !== null"
                                                :src="`/assets/ranks/${playerRank(p)}.svg`"
                                                class="player-rank-icon"
                                                alt="rank"
                                                decoding="async"
                                            />
                                        </div>
                                    </div>
                                </td>
                                <td class="stat-cell">{{ playerKills(p) }}</td>
                                <td class="stat-cell stat-col-assists">{{ playerAssists(p) }}</td>
                                <td class="stat-cell">{{ playerDeaths(p) }}</td>
                                <td class="stat-cell stat-col-beststreak">{{ playerBestStreak(p) }}</td>
                                <td class="stat-cell">{{ playerScore(p) }}</td>
                            </tr>
                        </template>
                        <tr v-for="(p, idx) in rawPlayers" :key="'raw-' + idx" class="player-row" style="background-color: #424242">
                            <td colspan="6">{{ p }}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </ClickPopover>
    </template>
    <template v-else>
        <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
    </template>
</template>
