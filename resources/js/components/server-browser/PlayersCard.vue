<script setup lang="ts">
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';
import generateEmblem from '@/lib/emblemGenerator';
import { reactive, computed } from 'vue';
import { toRaw } from 'vue';

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

function resolvePlayerColor(p: any) {
    const v = p?.primaryColor ?? p?.primary_color ?? p?.color ?? p?.colorPrimary ?? p?.primaryColour ?? p?.primary_colour ?? null;
    if (!v) return 'transparent';
    if (Array.isArray(v) && v.length >= 3) return `rgb(${v[0]}, ${v[1]}, ${v[2]})`;
    if (typeof v === 'object' && v !== null && v.r !== undefined) return `rgb(${v.r}, ${v.g ?? 0}, ${v.b ?? 0})`;
    if (typeof v === 'string') {
        if (/^[0-9a-fA-F]{6}$/.test(v)) return `#${v}`;
        return v;
    }
    return String(v);
}

function textColorForBackground(color: string) {
    try {
        let r = 0, g = 0, b = 0;
        if (color.startsWith('#')) {
            const hex = color.slice(1);
            if (hex.length === 3) {
                r = parseInt(hex[0] + hex[0], 16);
                g = parseInt(hex[1] + hex[1], 16);
                b = parseInt(hex[2] + hex[2], 16);
            } else if (hex.length === 6) {
                r = parseInt(hex.substring(0,2), 16);
                g = parseInt(hex.substring(2,4), 16);
                b = parseInt(hex.substring(4,6), 16);
            }
        }
        else if (color.startsWith('rgb')) {
            const m = color.match(/\d+/g);
            if (m && m.length >= 3) {
                r = parseInt(m[0], 10);
                g = parseInt(m[1], 10);
                b = parseInt(m[2], 10);
            }
        }
        else {
            return 'black';
        }
        const lum = (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
        return lum < 0.5 ? '#ffffff' : '#000000';
    }
    catch {
        return 'black';
    }
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
            <div v-else>
                <h4 class="mb-4 text-foreground has-text-weight-semibold">Players</h4>
                <div class="text-sm">
                <ul class="list-none p-0" :style="{ display: 'flex', flexDirection: 'column', rowGap: '6px' }">
                    <li
                        v-for="({ player: p, emblemStr }, index) in processedPlayers"
                        :key="index"
                        class="block text-sm m-0 p-0"
                    >
                        <template v-if="typeof p === 'object' && p !== null">
                            <div
                                class="w-full overflow-hidden"
                                :style="{ backgroundColor: resolvePlayerColor(p), height: '32px' }"
                            >
                                <div class="h-full w-full flex items-center px-1">
                                    <div class="flex items-center space-x-[6px]">
                                        <img
                                            v-if="emblemStr && getEmblemSrc(emblemStr)"
                                            :src="getEmblemSrc(emblemStr)"
                                            class="flex-shrink-0"
                                            alt="emblem"
                                            width="20"
                                            height="20"
                                            decoding="async"
                                            style="width:20px;height:20px;object-fit:contain"
                                        />
                                    </div>
                                    <div class="flex-1 px-1">
                                        <span
                                            class="font-semibold truncate block text-sm"
                                            :style="{ color: textColorForBackground(resolvePlayerColor(p)) }"
                                        >
                                            {{ p.name ?? p.playerName ?? p.displayName ?? p.player_name ?? JSON.stringify(p) }}
                                        </span>
                                    </div>
                                    <div v-if="p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag" class="text-xs px-1">
                                        <span :style="{ color: textColorForBackground(resolvePlayerColor(p)) }">[{{ p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag }}]</span>
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
            </div>
        </HoverCardContent>
    </HoverCard>
</template>
