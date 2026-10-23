<script setup lang="ts">
import Scoreboard from '@/components/server-browser/Scoreboard.vue';
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
import { groupBy, sortGroups, type ScoreboardColumn, type ScoreboardGroup, type ScoreboardPlayer } from '@/lib/scoreboard';
import { TEAM_NAMES } from '@/lib/teams';
import { computed, h } from 'vue';

/** Scoreboard popover for an ElDewrito server. */
const props = defineProps<{
    numPlayers: number;
    maxPlayers: number;
    players?: unknown[];
    teams?: boolean | string | number;
    teamScores?: number[];
    serverVersion?: string;
    passworded?: boolean;
}>();

const COLUMNS: ScoreboardColumn[] = [
    { label: 'Kills' },
    { label: 'Assists', class: 'stat-col-assists' },
    { label: 'Deaths' },
    { label: 'Best Streak', class: 'stat-col-beststreak' },
    { label: 'Score' },
];

const teamsEnabled = computed(() => [true, 'true', 1, '1'].includes(props.teams as never));

/** Server version from the prop, else from whatever the players report. */
const serverVersion = computed<string | null>(() => {
    const fromProp = String(props.serverVersion ?? '').trim();
    const fromPlayers = (props.players ?? []).find((p) => isPlayerObject(p) && (p.eldewritoVersionShort ?? p.eldewritoVersion ?? p.gameVersion)) as
        | PlayerLike
        | undefined;

    return fromProp || (fromPlayers ? String(fromPlayers.eldewritoVersionShort ?? fromPlayers.eldewritoVersion ?? fromPlayers.gameVersion) : null);
});

// Ranks and stats-site uids exist from ElDewrito 0.7 on.
const supportsStats = computed(() => isVersionAtLeast(serverVersion.value, 0, 7));

function openStats(p: PlayerLike) {
    const href = playerStatsHref(p);

    if (href !== '#') {
        window.open(href, '_blank');
    } else {
        console.warn('Player stats unavailable or not supported on this server');
    }
}

function preloadHref(p: PlayerLike) {
    const candidate = playerCandidateUid(p);

    if (supportsStats.value && candidate && !/^\d+$/.test(candidate)) {
        void resolveStatsId(candidate);
    }
}

function nameCell(p: PlayerLike) {
    const emblem = playerEmblem(p);
    void ensureEmblem(emblem);

    const tag = playerServiceTag(p);
    const rank = supportsStats.value ? playerRank(p) : null;
    const clickable = supportsStats.value && playerCandidateUid(p) !== null;

    return h('div', { class: 'player-cell' }, [
        h('img', { src: emblemSrc(emblem), class: 'player-emblem', alt: 'emblem', decoding: 'async' }),
        h('div', { class: 'player-info' }, [
            clickable
                ? h(
                      'a',
                      {
                          class: 'player-name player-link',
                          href: playerStatsHref(p),
                          target: '_blank',
                          onClick: (e: Event) => (e.preventDefault(), openStats(p)),
                          onMouseenter: (e: Event) => (e.preventDefault(), preloadHref(p)),
                      },
                      playerName(p),
                  )
                : h('span', { class: 'player-name' }, playerName(p)),
        ]),
        h('div', { class: 'player-tags' }, [
            tag ? h('span', { class: 'service-tag' }, tag) : null,
            rank !== null ? h('img', { src: `/assets/ranks/${rank}.svg`, class: 'player-rank-icon', alt: 'rank', decoding: 'async' }) : null,
        ]),
    ]);
}

function toRow(p: PlayerLike): ScoreboardPlayer {
    return {
        cell: nameCell(p),
        stats: [playerKills(p), playerAssists(p), playerDeaths(p), playerBestStreak(p), playerScore(p)],
        color: playerColor(p, teamsEnabled.value),
    };
}

const groups = computed<ScoreboardGroup[]>(() => {
    const players = (props.players ?? []).filter(isPlayerObject);
    // Malformed entries are shown raw at the end.
    const raw: ScoreboardPlayer[] = (props.players ?? [])
        .filter((p) => !isPlayerObject(p))
        .map((p) => ({ cell: String(p), stats: [], color: '#424242', raw: true }));

    if (!teamsEnabled.value) {
        return [{ team: null, totals: [], players: [...players.sort(comparePlayers).map(toRow), ...raw] }];
    }

    const groups = [...groupBy(players, playerTeam)].map(([team, members]) => {
        members.sort(comparePlayers);

        const reported = team !== null && props.teamScores && team >= 0 && team < props.teamScores.length ? props.teamScores[team] : undefined;
        const sum = (fn: (p: PlayerLike) => number) => members.reduce((acc, p) => acc + fn(p), 0);
        const score = reported ?? sum(playerScore);
        const kills = sum(playerKills);
        const deaths = sum(playerDeaths);

        return {
            team,
            kills,
            deaths,
            score,
            label: team !== null && TEAM_NAMES[team] ? `${TEAM_NAMES[team]} Team` : `Team ${team}`,
            totals: ['', '', '', '', score],
            players: members.map(toRow),
        };
    });

    sortGroups(groups, (a, b) => b.score - a.score || b.kills - a.kills || a.deaths - b.deaths);

    if (raw.length) {
        groups[groups.length - 1].players.push(...raw);
    }

    return groups;
});
</script>

<template>
    <Scoreboard
        :num-players="numPlayers"
        :max-players="maxPlayers"
        :columns="COLUMNS"
        :groups="groups"
        :teams="teamsEnabled"
        :message="passworded ? 'Private Server' : undefined"
        :on-open="() => void preloadPlayerStats(players ?? [])"
    />
</template>
