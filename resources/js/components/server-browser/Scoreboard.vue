<script setup lang="ts">
import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { usePopoverToggle } from '@/composables/usePopoverToggle';
import type { ScoreboardColumn, ScoreboardGroup } from '@/lib/scoreboard';
import { teamColor } from '@/lib/teams';
import '../../../css/PlayersCard.css';

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
