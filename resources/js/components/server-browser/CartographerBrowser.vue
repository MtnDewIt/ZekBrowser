<script setup lang="ts">
import DataTable from '@/components/server-browser/DataTable.vue';
import UnicodeText from '@/components/UnicodeText.vue';
import { fetchJson, listUrl, type ServerListResponse } from '@/lib/api';
import { makeSortHeader } from '@/lib/tableHeaders';
import type { ColumnDef } from '@tanstack/vue-table';
import { computed, h, onMounted, ref } from 'vue';

const props = withDefaults(defineProps<{ apiBase?: string }>(), { apiBase: '/api/' });

interface CartoServer {
    xuid?: string | number;
    server_name: string;
    map_name: string;
    map_id?: number | string | null;
    gametype: string;
    variant: string;
    players: { filled?: number | null; max?: number | null };
    description: string;
}

const servers = ref<CartoServer[]>([]);
const error = ref<string | null>(null);

// Stock Halo 2 map ids (mirrors MAP_ID_TO_INFO in server.py); anything else is a custom map.
const KNOWN_MAP_IDS = new Set([
    1, 101, 105, 301, 305, 401, 405, 501, 505, 601, 605, 701, 801, 705, 805, 80, 1201, 100, 60, 110, 70, 1300, 10, 1302, 1400, 3001, 1200, 1001, 120,
    1002, 800, 1402, 50, 20, 444678, 91101, 1101, 1000, 1109, 40, 30,
]);

function isCustomMap(server: CartoServer): boolean {
    const id = server.map_id;

    if (id === null || id === undefined || String(id).trim() === '') {
        return true;
    }

    const n = Number(id);

    return Number.isNaN(n) || !KNOWN_MAP_IDS.has(n);
}

function filledPlayers(server: CartoServer): number {
    return Number(server.players?.filled ?? 0);
}

const totalPlayers = computed(() => servers.value.reduce((sum, s) => sum + filledPlayers(s), 0));

const searchOptions = [
    { label: 'All', value: 'all' },
    { label: 'Server', value: 'server' },
    { label: 'Map', value: 'map' },
    { label: 'Gametype', value: 'gametype' },
    { label: 'Variant', value: 'variant' },
    { label: 'Description', value: 'description' },
];

const columns: ColumnDef<CartoServer>[] = [
    {
        accessorKey: 'server_name',
        header: makeSortHeader('Server'),
        cell: ({ row }) =>
            h('div', { class: 'md:whitespace-nowrap' }, [h('span', { class: 'font-bold!' }, h(UnicodeText, { text: row.original.server_name }))]),
    },
    {
        accessorKey: 'map_name',
        header: makeSortHeader('Map'),
        cell: ({ row }) => h(UnicodeText, { text: row.original.map_name }),
    },
    {
        id: 'custom_map',
        accessorFn: (row) => (isCustomMap(row) ? 1 : 0),
        header: makeSortHeader(
            h('span', { class: 'inline-flex items-center' }, [
                h('span', {
                    class: 'icon-mask icon-download-b inline-block w-4 h-4 leading-none text-muted-foreground relative top-[2px]',
                    ariaHidden: 'true',
                }),
            ]),
            { title: 'Custom Map', buttonClass: 'gap-0' },
        ),
        cell: ({ row }) =>
            isCustomMap(row.original)
                ? h('span', { class: 'block w-4 h-4 leading-none text-muted-foreground icon-mask icon-download-b', title: 'Custom Map' })
                : h('span', { class: 'block w-4 h-4' }, ''),
    },
    {
        accessorKey: 'gametype',
        header: makeSortHeader('Gametype'),
        cell: ({ row }) => h(UnicodeText, { text: row.original.gametype }),
    },
    {
        accessorKey: 'variant',
        header: makeSortHeader('Variant'),
        cell: ({ row }) => h(UnicodeText, { text: row.original.variant }),
    },
    {
        id: 'players',
        accessorFn: (row) => filledPlayers(row),
        header: makeSortHeader('Players'),
        cell: ({ row }) => `${row.original.players?.filled ?? '?'}/${row.original.players?.max ?? '?'}`,
    },
    {
        accessorKey: 'description',
        header: makeSortHeader('Description'),
        cell: ({ row }) => h(UnicodeText, { text: row.original.description || '—', stripUnicode: true }),
    },
];

interface CartoServerRaw {
    xuid?: string | number;
    server_name?: string;
    map_name?: string;
    map_id?: number | string | null;
    gametype?: string;
    variant?: string;
    players?: { filled?: number | null; max?: number | null } | number;
    description?: string;
}

function toCartoServer(item: CartoServerRaw): CartoServer {
    return {
        xuid: item.xuid,
        server_name: item.server_name || '',
        map_id: item.map_id,
        map_name: item.map_name || '',
        variant: item.variant || '',
        gametype: item.gametype || '',
        players: item.players && typeof item.players === 'object' ? item.players : { filled: undefined, max: undefined },
        description: item.description || '',
    };
}

/** Fetch the list. The current rows stay visible until the new ones arrive. */
async function load(): Promise<void> {
    error.value = null;

    try {
        const data = await fetchJson<ServerListResponse<CartoServerRaw[]> | CartoServerRaw[]>(listUrl(props.apiBase, 'cartographer'));
        const list = Array.isArray(data) ? data : Array.isArray(data.servers) ? data.servers : [];

        servers.value = list.map(toCartoServer);
    } catch (err) {
        error.value = err instanceof Error ? err.message : String(err);
        console.warn('Cartographer load failed:', err);
    }
}

onMounted(() => void load());

defineExpose({ load });
</script>

<template>
    <div class="carto-browser">
        <div v-if="error" class="text-red-500">{{ error }}</div>

        <DataTable
            :columns="columns"
            :data="servers"
            :search-options="searchOptions"
            :initial-sorting="[{ id: 'players', desc: true }]"
            :players="totalPlayers"
            :servers="servers.length"
        >
            <template #left>
                <slot name="left" />
            </template>
            <template #mobile-card="{ row }">
                <div class="flex items-start justify-between gap-2">
                    <div class="min-w-0 flex-1">
                        <div class="truncate text-sm font-bold text-foreground"><UnicodeText :text="row.server_name || '—'" /></div>
                        <div class="mt-0.5 text-xs text-muted-foreground">
                            <UnicodeText :text="row.map_name" />
                            <span v-if="row.gametype" class="ml-1">· <UnicodeText :text="row.gametype" /></span>
                        </div>
                    </div>
                    <span class="flex-shrink-0 text-sm font-semibold text-foreground tabular-nums">
                        {{ row.players?.filled ?? '?' }}/{{ row.players?.max ?? '?' }}
                    </span>
                </div>
                <div v-if="row.variant || row.description" class="mt-1.5 truncate text-xs text-muted-foreground">
                    <UnicodeText v-if="row.variant" :text="row.variant" />
                    <span v-if="row.variant && row.description"> · </span>
                    <UnicodeText v-if="row.description" :text="row.description" :strip-unicode="true" />
                </div>
            </template>
        </DataTable>
    </div>
</template>
