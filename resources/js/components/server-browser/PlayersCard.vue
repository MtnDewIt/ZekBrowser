<script setup lang="ts">
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import generateEmblem from '@/lib/emblemGenerator';
import { reactive, computed } from 'vue';

interface Props {
    numPlayers: number;
    maxPlayers: number;
    players?: any[];
}

const props = defineProps<Props>();

const emblemCache = reactive(new Map<string, string>());

async function ensureEmblem(emblem: string | null | undefined) {
    if (!emblem) return;
    if (emblemCache.has(emblem)) return;
    emblemCache.set(emblem, '');
    try {
        const url = await generateEmblem(emblem);
        emblemCache.set(emblem, url);
    }
    catch {
        // ignore generation errors
    }
}

function getEmblemSrc(emblem: string | null | undefined) {
    if (!emblem) return '';
    return emblemCache.get(emblem) ?? '';
}

function getEmblemString(p: any) {
    if (typeof p !== 'object' || p === null) return null;
    return p.emblem ?? p.emblemUrl ?? p.emblem_url ?? p.emblemString ?? null;
}

// Pre-load emblems for all players
const processedPlayers = computed(() => {
    if (!props.players) return [];
    
    return props.players.map(p => {
        const emblemStr = getEmblemString(p);
        if (emblemStr) {
            void ensureEmblem(emblemStr);
        }
        return {
            player: p,
            emblemStr,
        };
    });
});
</script>

<template>
    <HoverCard>
        <HoverCardTrigger as-child>
            <span class="cursor-default">{{ numPlayers }}/{{ maxPlayers }}</span>
        </HoverCardTrigger>
        <HoverCardContent class="bg-background/100 dark:bg-background/100 backdrop-blur-xs">
            <div v-if="!players || players.length === 0">
                No players
            </div>
            <div v-else class="text-sm">
                <div class="font-semibold mb-2">Players</div>
                <ul class="list-none p-0 space-y-1">
                    <li
                        v-for="({ player: p, emblemStr }, index) in processedPlayers"
                        :key="index"
                        class="flex items-center text-sm space-x-2"
                    >
                        <template v-if="typeof p === 'object' && p !== null">
                            <img
                                v-if="emblemStr && getEmblemSrc(emblemStr)"
                                :src="getEmblemSrc(emblemStr)"
                                class="w-7 h-7 rounded-sm mr-2 flex-shrink-0"
                                alt="emblem"
                            />
                            <span class="truncate">
                                {{ p.name ?? p.playerName ?? p.displayName ?? p.player_name ?? JSON.stringify(p) }}
                            </span>
                            <span
                                v-if="p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag"
                                class="text-xs text-muted-foreground"
                            >
                                [{{ p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag }}]
                            </span>
                        </template>
                        <template v-else>
                            <span class="truncate">{{ p }}</span>
                        </template>
                    </li>
                </ul>
            </div>
        </HoverCardContent>
    </HoverCard>
</template>
