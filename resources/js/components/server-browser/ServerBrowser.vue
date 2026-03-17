<script setup lang="ts">

import type { ElDewritoServer } from '@/models/ElDewritoServer';
import DataTable from '@/components/server-browser/DataTable.vue';
import ModsCard from '@/components/server-browser/ModsCard.vue';
import PlayersCard from '@/components/server-browser/PlayersCard.vue';
import HaloPlayersCard from '@/components/server-browser/HaloPlayersCard.vue';
import CartographerBrowser from '@/components/server-browser/CartographerBrowser.vue';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { h, ref, defineExpose, watch, onMounted } from 'vue';
import type { ColumnDef } from '@tanstack/vue-table';

interface Props 
{
    servers: ElDewritoServer[];
}

const SORT_ICON_BASE = 'icon-mask inline-block w-3.5 h-3.5 ml-2 align-middle opacity-70';

const props = defineProps<Props>();

const STORAGE_KEY = 'zekbrowser.serverBrowser';
const selected = ref('eldewrito');
onMounted(() => {
    try {
        const v = localStorage.getItem(STORAGE_KEY);
        if (v === 'cartographer' || v === 'eldewrito' || v === 'haloce' || v === 'halopc') selected.value = v;
    } catch (e) {
        // ignore (e.g., unavailable in some environments)
    }
    // notify parent which browser is currently selected so parent
    // can sync stats view on initial load
    try { emit('browser-change', selected.value); } catch (e) { /* ignore */ }

    // emit initial counts for the active browser
    if (selected.value === 'cartographer') {
        fetchCartoCounts();
    } else if (selected.value === 'haloce' || selected.value === 'halopc') {
        // initial load for Halo browsers
        try { void loadHaloServers(selected.value as 'haloce' | 'halopc'); } catch (e) { }
    } else {
        try {
            const srv = Array.isArray(props.servers) ? props.servers : [];
            let players = 0;
            for (const s of srv) players += Number(s.numPlayers || 0);
            const servcount = srv.length;
            currentPlayers.value = players;
            currentServers.value = servcount;
            emit('counts', { players, servers: servcount });
        } catch (e) { }
    }
});
watch(selected, (v) => {
    try { localStorage.setItem(STORAGE_KEY, v); } catch (e) { }
    emit('browser-change', v);
    if (v === 'cartographer') {
        fetchCartoCounts();
    } else {
        // For non-Cartographer (ElDewrito / Halo CE) compute counts from
        // parent-provided `props.servers` for now (no API hookup yet).
        try {
            const srv = Array.isArray(props.servers) ? props.servers : [];
            let players = 0;
            for (const s of srv) players += Number(s.numPlayers || 0);
            const servcount = srv.length;
            currentPlayers.value = players;
            currentServers.value = servcount;
            emit('counts', { players, servers: servcount });
        } catch (e) { /* ignore */ }
    }
});

// update elderwrito counts when parent servers prop changes
watch(() => props.servers, (val) => {
    if (selected.value === 'eldewrito' || selected.value === 'haloce' || selected.value === 'halopc') {
        try {
            const srv = Array.isArray(val) ? val : [];
            let players = 0;
            for (const s of srv) players += Number(s.numPlayers || 0);
            const servcount = srv.length;
            currentPlayers.value = players;
            currentServers.value = servcount;
            emit('counts', { players, servers: servcount });
        } catch (e) { }
    }
}, { deep: true });
const cartoRef = ref(null as any);

const currentPlayers = ref<number>(0);
const currentServers = ref<number>(0);

// Halo CE placeholder search state (UI-only for now)
const haloSearch = ref('');
const haloSearchMode = ref('all');
const haloSearchOptions = [
    { label: 'All', value: 'all' },
    { label: 'Server Name', value: 'name' },
];

const emit = defineEmits<{
    (e: 'counts', payload: { players: number; servers: number }): void,
    (e: 'counts-loading', val: boolean): void,
    (e: 'browser-change', browserType: 'eldewrito' | 'cartographer' | 'haloce' | 'halopc'): void,
}>();

async function fetchCartoCounts() {
    emit('counts-loading', true);
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);
        const res = await fetch('/api/cartographer/list');
        clearTimeout(timeout);
        if (!res.ok) throw new Error('Network');
        const data = await res.json();
        const list = Array.isArray(data) ? data : (data.servers && Array.isArray(data.servers) ? data.servers : []);
        let serversNum = list.length;
        let playersNum = 0;
        for (const s of list) {
            const p = s.players;
            if (p && typeof p === 'object') playersNum += Number(p.filled ?? 0);
            else if (typeof p === 'number') playersNum += Number(p);
        }
        currentPlayers.value = playersNum;
        currentServers.value = serversNum;
        emit('counts', { players: playersNum, servers: serversNum });
    } catch (e) {
        // ignore
    } finally {
        emit('counts-loading', false);
    }
}

async function refresh() {
    if (selected.value === 'cartographer' && cartoRef.value && typeof cartoRef.value.load === 'function') {
        await cartoRef.value.load();
        await fetchCartoCounts();
        return true;
    }
    if (selected.value === 'haloce' || selected.value === 'halopc') {
        await loadHaloServers(selected.value as 'haloce' | 'halopc');
        return true;
    }
    return false;
}

defineExpose({ refresh, getSelection: () => selected.value });

const renderSortIcon = (state: false | 'asc' | 'desc') => 
{
    const variant = state === 'asc' ? 'icon-sort-up' : state === 'desc' ? 'icon-sort-down' : 'icon-sort';
    return h('span', { class: `${SORT_ICON_BASE} ${variant}`, ariaHidden: 'true' });
};

const makeSortHeader = (label: string, buttonClass = '') => ({ column }) => 
{
    const state = column.getIsSorted();

    return h(Button, 
    {
        variant: 'ghost',
        class: ['gap-1', buttonClass].filter(Boolean).join(' '),
        style: 'padding-left: 0.5rem; padding-right: 1.25rem; margin-left: -0.5rem;',
        onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
    }, 
    () => [label, renderSortIcon(state)]);
};

const columns: ColumnDef<ElDewritoServer>[] = 
[
    {
        id: 'passworded',
        accessorFn: (row) => (row.passworded ? 1 : 0),
        header: ({ column }) => 
        {
            const state = column.getIsSorted();
            const icon = h('span', 
            {
                class: 'w-5 h-5 leading-none text-muted-foreground icon-mask icon-lock',
                ariaHidden: 'true',
            });

            return h(Button, 
            {
                variant: 'ghost',
                class: 'gap-1',
                style: 'padding-left: 0.5rem; padding-right: 0.5rem; margin-left: -0.5rem;',
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
                title: 'Sort by password protection',
            }, 
            () => [icon, renderSortIcon(state)])
        },
        cell: ({ row }) => 
        {
            const server: ElDewritoServer = row.original;

            if (!server.passworded) 
            {
                return h('span', { class: 'block w-5 h-5' });
            }

            return h('span', 
                {
                    class: 'block w-5 h-5 leading-none text-muted-foreground icon-mask icon-lock',
                    ariaHidden: 'true',
                    title: 'Password protected',
                }
            );
        },
    },
    {
        accessorKey: 'name',
        header: makeSortHeader('Server'),
        cell: ({ row }) => h('div', { class: 'md:whitespace-nowrap' }, 
        [
            h('span', { class: 'font-bold!' }, row.getValue('name')),
        ]),
    },
    {
        accessorKey: 'hostPlayer',
        header: makeSortHeader('Host'),
        cell: ({ row }) => row.getValue('hostPlayer'),
    },
    {
        id: 'status',
        header: makeSortHeader('Status'),
        accessorFn: (row) => row.statusFormatted(),
        cell: ({ row }) => row.original.statusFormatted(),
    },
    {
        accessorKey: 'mods',
        header: makeSortHeader('Mods'),
        accessorFn: (row) => row.mods?.length ?? 0,
        cell: ({ row }) => 
        {
            const mods = row.original.mods;

            if (!mods || mods.length === 0) 
            {
                return 0;
            }

            return h(ModsCard, 
            {
                mods: mods,
                jsonUrl: `http://${row.original.ip}/mods`,
                showAsNumber: true,
            });
        },
    },
    {
        accessorKey: 'numPlayers',
        header: makeSortHeader('Players'),
        cell: ({ row }) => 
        {
            const server: ElDewritoServer = row.original;

            return h(PlayersCard, 
            {
                numPlayers: server.numPlayers,
                maxPlayers: server.maxPlayers,
                players: server.players,
                teams: server.teams,
                teamScores: server.teamScores,
                serverVersion: server.eldewritoVersionShort ?? server.eldewritoVersion ?? '',
                passworded: !!server.passworded,
            });
        },
    },
    {
        accessorKey: 'eldewritoVersion',
        header: makeSortHeader('Version'),
        cell: ({ row }) => row.original.versionWithoutTrailingZero(),
    },
    {
        accessorKey: 'ip',
        header: makeSortHeader('IP', 'text-left'),
        cell: ({ row }) => 
        {
            const server = row.original;

            return h('span', { class: 'inline-flex items-center whitespace-nowrap' },
                [
                    h('a', 
                    {
                        href: `eldewrito://${server.ip}`,
                        target: '_blank',
                        title: `Click to join ${server.name}`,
                    }, server.ip),
                    h(
                        'a', 
                        {
                            href: `http://${server.ip}`,
                            target: '_blank',
                            title: `View JSON info`,
                            class: 'ml-1 inline-flex items-center',
                        },
                        h('span', 
                        {
                            class: 'icon-mask icon-external inline-block w-4 h-4 opacity-80 align-middle',
                            ariaHidden: 'true',
                        })
                    ),
                ]
            );
        },
    },
]

// Columns for Halo CE / Halo PC server lists (gamespy-style)
const haloColumns: ColumnDef<any>[] = [
    {
        accessorKey: 'name',
        header: makeSortHeader('Server'),
        cell: ({ row }) => row.getValue('name') || row.original.info?.server_name || row.original.info?.hostname || ''
    },
    {
        accessorKey: 'map',
        header: makeSortHeader('Map'),
        cell: ({ row }) => {
            const info = row.original.info || {};
            return info.mapname || info.map_name || info.map_name_2 || info.map || '';
        }
    },
    {
        accessorKey: 'gametype',
        header: makeSortHeader('Gametype'),
        cell: ({ row }) => {
            const info = row.original.info || {};
            const gt = info.gametype_name ?? info.gametype ?? '';
            if (typeof gt === 'string' && gt.trim().toLowerCase() === 'king') return 'KOTH';
            return gt || '';
        }
    },
    {
        accessorKey: 'variant',
        header: makeSortHeader('Variant'),
        cell: ({ row }) => {
            const info = row.original.info || {};
            return info.gamevariant || info.game_variant || info.variant || info.variant_name || info.gamevariant || '';
        }
    },
    {
        id: 'players',
        header: makeSortHeader('Players'),
        // accessor returns a numeric value so sorting works correctly
        accessorFn: (row) => Number(row.info?.numplayers ?? row.players ?? 0),
        cell: ({ row }) => {
            const info = row.original.info || {};
            const filled = Number(info.numplayers ?? row.original.players ?? 0);
            const max = Number(info.maxplayers ?? 0);
            return h(HaloPlayersCard, {
                numPlayers: filled,
                maxPlayers: max,
                info: info,
            });
        }
    },
    {
        id: 'ipport',
        header: makeSortHeader('IP:Port', 'text-left'),
        cell: ({ row }) => {
            const ip = row.original.address || row.original.ip || row.original.ipaddr || '';
            const port = row.original.port || row.original.info?.port || '';
            return h('span', { class: 'inline-flex items-center whitespace-nowrap' }, [`${ip}:${port}`]);
        }
    },
];

const haloServers = ref<any[]>([]);
const haloLoading = ref(false);

async function loadHaloServers(browserType: 'haloce' | 'halopc') {
    emit('counts-loading', true);
    haloLoading.value = true;
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10000);
        const res = await fetch(`/api/${browserType}/list`, { signal: controller.signal });
        clearTimeout(timeout);
        if (!res.ok) throw new Error('Network');
        const data = await res.json();

        const list = Array.isArray(data.servers) ? data.servers : (data.servers || []);

        // Map to simplified objects for the DataTable
        haloServers.value = list.map((s: any) => ({
            address: s.address || s.ip || s.host || '',
            port: s.port || (s.info && s.info.port) || '',
            info: s.info || {},
            players: s.info?.numplayers || s.players || 0,
            name: s.info?.hostname || s.info?.server_name || '',
            variant: s.info?.gamevariant || s.info?.game_variant || s.info?.variant || '',
            gametype: s.info?.gametype || s.info?.gametype_name || '',
            map: s.info?.mapname || s.info?.map_name || s.info?.map || '',
        }));

        // Emit counts if available
        if (data.count) {
            currentPlayers.value = Number(data.count.players || 0);
            currentServers.value = Number(data.count.servers || haloServers.value.length);
            emit('counts', { players: currentPlayers.value, servers: currentServers.value });
        }
    } catch (e) {
        // ignore
    } finally {
        haloLoading.value = false;
        emit('counts-loading', false);
    }
}

// Load halo servers when selection changes to haloce/halopc
watch(selected, (v) => {
    if (v === 'haloce' || v === 'halopc') {
        void loadHaloServers(v as 'haloce' | 'halopc');
    }
});

</script>

<template>
    <div>
        <!-- server selector will be rendered into DataTable's `left` slot -->

        <div v-if="selected === 'eldewrito'">
            <DataTable :columns="columns" :data="servers" :players="currentPlayers" :servers="currentServers">
                <template #left>
                    <Select v-model="selected" class="min-w-[168px]" :options="[
                        { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.webp', iconRounded: true },
                        { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.webp', iconRounded: true },
                        { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.webp', iconRounded: true },
                        { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.webp', iconRounded: true },
                    ]" :full-width-trigger="true">
                        <template #trigger-content>
                            <img v-if="selected === 'eldewrito'" src="/assets/logos/eldewrito.webp" alt="ElDewrito" class="w-5 h-5 mr-2 object-contain rounded-full" />
                            <img v-else-if="selected === 'haloce' || selected === 'halopc'" src="/assets/logos/haloce.webp" alt="Halo" class="w-5 h-5 mr-2 object-contain rounded-full" />
                            <img v-else src="/assets/logos/cartographer.webp" alt="Cartographer" class="w-5 h-5 mr-2 object-contain rounded-full" />
                        </template>
                    </Select>
                </template>
                <template #mobile-card="{ row }">
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0 flex-1">
                            <div class="flex items-center gap-1.5">
                                <span v-if="row.passworded" class="icon-mask icon-lock w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                                <span class="font-bold text-sm text-foreground truncate">{{ row.name }}</span>
                            </div>
                            <div class="text-xs text-muted-foreground mt-0.5">
                                {{ row.statusFormatted() }}
                                <span v-if="row.hostPlayer" class="ml-1">· {{ row.hostPlayer }}</span>
                            </div>
                        </div>
                        <PlayersCard
                            :numPlayers="row.numPlayers"
                            :maxPlayers="row.maxPlayers"
                            :players="row.players"
                            :teams="row.teams"
                            :teamScores="row.teamScores"
                            :serverVersion="row.eldewritoVersionShort ?? row.eldewritoVersion ?? ''"
                            :passworded="!!row.passworded"
                            class="text-sm font-semibold tabular-nums text-foreground flex-shrink-0"
                        />
                    </div>
                    <div class="flex items-center gap-2 mt-1.5 text-xs text-muted-foreground">
                        <span v-if="row.eldewritoVersion">v{{ row.versionWithoutTrailingZero() }}</span>
                        <span v-if="row.mods?.length" class="inline-flex items-center cursor-pointer" @click.stop="$event.currentTarget.querySelector('.mods-count-button')?.click()">Mods:&nbsp;<ModsCard :mods="row.mods" :jsonUrl="`http://${row.ip}/mods`" :showAsNumber="true" /></span>
                    </div>
                </template>
            </DataTable>
        </div>

        <div v-else-if="selected === 'haloce' || selected === 'halopc'">
            <DataTable :columns="haloColumns" :data="haloServers" :players="currentPlayers" :servers="currentServers" :initial-sorting="[{ id: 'players', desc: true }]" :searchOptions="[
                { label: 'All', value: 'all' },
                { label: 'Server', value: 'name' },
                { label: 'Variant', value: 'variant' },
                { label: 'Gametype', value: 'gametype' },
                { label: 'Map', value: 'map' },
            ]">
                <template #left>
                    <Select v-model="selected" class="min-w-[168px]" :options="[
                        { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.webp', iconRounded: true },
                        { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.webp', iconRounded: true },
                        { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.webp', iconRounded: true },
                        { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.webp', iconRounded: true },
                    ]" :full-width-trigger="true">
                        <template #trigger-content>
                            <img v-if="selected === 'eldewrito'" src="/assets/logos/eldewrito.webp" alt="ElDewrito" class="w-5 h-5 mr-2 object-contain rounded-full" />
                            <img v-else-if="selected === 'haloce' || selected === 'halopc'" src="/assets/logos/haloce.webp" alt="Halo" class="w-5 h-5 mr-2 object-contain rounded-full" />
                            <img v-else src="/assets/logos/cartographer.webp" alt="Cartographer" class="w-5 h-5 mr-2 object-contain rounded-full" />
                        </template>
                    </Select>
                </template>
                <template #mobile-card="{ row }">
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0 flex-1">
                            <div class="font-bold text-sm text-foreground truncate">{{ row.name || row.info?.hostname || '—' }}</div>
                            <div class="text-xs text-muted-foreground mt-0.5">
                                {{ row.map || row.info?.mapname || '' }}
                                <span v-if="row.gametype" class="ml-1">· {{ row.gametype }}</span>
                            </div>
                        </div>
                        <HaloPlayersCard
                            :numPlayers="Number(row.info?.numplayers ?? row.players ?? 0)"
                            :maxPlayers="Number(row.info?.maxplayers ?? 0)"
                            :info="row.info"
                            class="text-sm font-semibold tabular-nums text-foreground flex-shrink-0"
                        />
                    </div>
                    <div v-if="row.variant || row.info?.gamevariant" class="text-xs text-muted-foreground mt-1.5">
                        {{ row.variant || row.info?.gamevariant }}
                    </div>
                </template>
            </DataTable>
        </div>

        <div v-else>
            <CartographerBrowser ref="cartoRef">
                <template #left>
                    <Select v-model="selected" class="min-w-[168px]" :options="[
                        { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.webp', iconRounded: true },
                        { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.webp', iconRounded: true },
                        { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.webp', iconRounded: true },
                        { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.webp', iconRounded: true },
                    ]" :full-width-trigger="true">
                        <template #trigger-content>
                            <img v-if="selected === 'eldewrito'" src="/assets/logos/eldewrito.webp" alt="ElDewrito" class="w-5 h-5 mr-2 object-contain rounded-full" />
                            <img v-else-if="selected === 'haloce' || selected === 'halopc'" src="/assets/logos/haloce.webp" alt="Halo" class="w-5 h-5 mr-2 object-contain rounded-full" />
                            <img v-else src="/assets/logos/cartographer.webp" alt="Cartographer" class="w-5 h-5 mr-2 object-contain rounded-full" />
                        </template>
                    </Select>
                </template>
            </CartographerBrowser>
        </div>
    </div>
</template>
