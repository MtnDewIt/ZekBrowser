<script setup lang="ts">
import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { usePopoverToggle } from '@/composables/usePopoverToggle';
import type { ScoreboardColumn, ScoreboardGroup } from '@/lib/scoreboard';
import { teamColor } from '@/lib/teams';

/**
 * "n/max" button that opens a scoreboard popover: optional team header rows,
 * one row per player, one stat column per entry in `columns`.
 */
const props = defineProps<{
    numPlayers: number;
    maxPlayers: number;
    columns: ScoreboardColumn[];
    groups: ScoreboardGroup[];
    /** Render team header rows. */
    teams: boolean;
    /** Shown instead of the table (e.g. for private servers). */
    message?: string;
    maxWidth?: string;
    onOpen?: () => void;
}>();

const { open, toggle } = usePopoverToggle(() => props.onOpen?.());
</script>

<template>
    <template v-if="numPlayers > 0">
        <ClickPopover v-model:model-value="open" placement="bottom">
            <template #trigger>
                <button type="button" class="player-count-button cursor-pointer" @click.stop="toggle">{{ numPlayers }}/{{ maxPlayers }}</button>
            </template>

            <div class="playercard-content bg-background/100 backdrop-blur-xs dark:bg-background/100" :style="maxWidth ? { maxWidth } : undefined">
                <div v-if="message" class="text-sm text-muted-foreground">{{ message }}</div>
                <table v-else class="scoreboard-table">
                    <thead>
                        <tr class="scoreboard-header">
                            <th class="players-count">Players [{{ numPlayers }}/{{ maxPlayers }}]</th>
                            <th v-for="col in columns" :key="col.label" class="stat-header" :class="col.class">{{ col.label }}</th>
                        </tr>
                    </thead>
                    <tbody>
                        <template v-for="(group, groupIdx) in groups" :key="group.team ?? 'none'">
                            <tr v-if="teams && group.team !== null" class="team-row" :style="{ backgroundColor: teamColor(group.team) }">
                                <td class="team-info">
                                    <span class="team-number">{{ groupIdx + 1 }}</span>
                                    <span class="team-name">{{ group.label }}</span>
                                </td>
                                <td
                                    v-for="(col, i) in columns"
                                    :key="col.label"
                                    class="stat-cell"
                                    :class="[col.class, i === columns.length - 1 ? 'team-score' : '']"
                                >
                                    {{ group.totals[i] }}
                                </td>
                            </tr>
                            <tr
                                v-for="(p, idx) in group.players"
                                :key="(group.team ?? 'none') + '-' + idx"
                                class="player-row"
                                :style="{ backgroundColor: p.color }"
                            >
                                <td v-if="p.raw" :colspan="columns.length + 1"><component :is="() => p.cell" /></td>
                                <template v-else>
                                    <td><component :is="() => p.cell" /></td>
                                    <td v-for="(col, i) in columns" :key="col.label" class="stat-cell" :class="col.class">{{ p.stats[i] }}</td>
                                </template>
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

<!-- Halo-style scoreboard: deliberately the same dark look in both themes. -->
<style>
.scoreboard-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    font-family: 'Conduit ITC Std', 'Segoe UI', Arial, sans-serif;
    font-size: 14px;
    color: #ffffff;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    text-shadow:
        -1px -1px 0 #000,
        1px -1px 0 #000,
        -1px 1px 0 #000,
        1px 1px 0 #000;
    background-color: #1a1a1a;
}

.scoreboard-header {
    height: 34px;
    background: #2a2a2a;
    border-bottom: 1px solid #000;
}

.scoreboard-header th {
    padding: 6px 12px;
    text-align: left;
    font-weight: bold;
    font-size: 14px;
    vertical-align: middle;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
    color: #ffffff !important;
}

.scoreboard-header th:last-child {
    border-right: none;
}

.scoreboard-header .players-count {
    text-align: left;
    padding-left: 16px;
    width: auto;
}

.scoreboard-header .stat-header {
    text-align: center;
    width: 100px;
    padding-left: 12px;
    padding-right: 12px;
}

.team-row {
    height: 34px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.6);
    box-sizing: border-box;
}

.team-row td {
    padding: 0;
    vertical-align: middle;
    height: 34px;
    box-sizing: border-box;
}

.team-info {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 12px 0 16px;
    height: 34px;
}

.team-number {
    font-size: 18px;
    font-weight: bold;
    min-width: 30px;
    text-align: center;
    padding-left: 8px;
}

.team-name {
    font-size: 15px;
    font-weight: bold;
}

.team-score {
    font-size: 24px;
    font-weight: bold;
    text-align: center;
}

.player-row {
    height: 34px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.4);
}

.player-row:last-child {
    border-bottom: none;
}

.player-row td {
    padding: 6px 0;
    vertical-align: middle;
}

.player-row td:first-child {
    padding-left: 0;
    padding-right: 0;
}

.player-cell {
    display: flex;
    align-items: center;
    gap: 8px;
    padding-left: 10px;
    padding-right: 12px;
    justify-content: space-between;
}

.player-emblem {
    width: 20px;
    height: 20px;
    object-fit: contain;
    flex-shrink: 0;
}

.player-info {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    min-width: 0;
}

.player-name {
    font-weight: bold;
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.player-link {
    color: #ffffff !important;
    text-decoration: none;
    cursor: pointer;
}

.player-link:hover {
    text-decoration: underline;
}

.service-tag {
    font-size: 12px;
    font-weight: bold;
    padding: 2px 6px;
    background: rgba(0, 0, 0, 0.4);
    border-radius: 2px;
    white-space: nowrap;
    min-width: 45px;
    text-align: center;
    display: inline-block;
}

.player-rank-icon {
    width: 18px;
    height: 18px;
    flex-shrink: 0;
}

.stat-cell {
    text-align: center;
    width: 100px;
    font-size: 15px;
    font-weight: bold;
    padding: 6px 12px !important;
}

.player-tags {
    display: flex;
    align-items: center;
    gap: 6px;
}

.playercard-content {
    min-width: 750px;
    max-width: 950px;
    width: auto;
    padding: 0;
    overflow: hidden;
}

.playercard-content:has(.text-muted-foreground) {
    min-width: 200px;
    max-width: 300px;
    padding: 16px;
}

@media (max-width: 640px) {
    .playercard-content {
        min-width: 0;
        width: calc(100vw - 24px);
        max-width: calc(100vw - 24px);
    }

    .stat-col-assists,
    .stat-col-beststreak {
        display: none;
    }

    .scoreboard-header .stat-header {
        width: 62px;
        padding: 4px 6px;
        font-size: 12px;
    }

    .stat-cell {
        width: 62px !important;
        padding: 4px 6px !important;
        font-size: 13px;
    }

    .player-cell {
        padding-left: 6px;
        padding-right: 6px;
        gap: 5px;
    }

    .player-name {
        font-size: 12px;
    }

    .player-emblem {
        width: 16px;
        height: 16px;
    }

    .player-rank-icon {
        width: 14px;
        height: 14px;
    }

    .service-tag {
        font-size: 10px;
        min-width: 30px;
        padding: 1px 3px;
    }

    .team-number {
        font-size: 14px;
        min-width: 18px;
        padding-left: 4px;
    }

    .team-name {
        font-size: 12px;
    }

    .team-score {
        font-size: 16px;
    }

    .scoreboard-header .players-count {
        font-size: 12px;
        padding-left: 10px;
    }
}
</style>
