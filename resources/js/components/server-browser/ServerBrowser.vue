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
        class: ['gap-0', buttonClass].filter(Boolean).join(' '),
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
            const icon = h('span', 
            {
                class: 'block mx-auto w-5 h-5 leading-none text-muted-foreground relative top-[1px] icon-mask icon-lock',
                ariaHidden: 'true',
            });

            return h(Button, 
            {
                class: 'block mx-auto w-8 h-8 p-0 flex items-center justify-center',
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
                title: 'Sort by password protection',
            }, 
            () => [icon])
        },
        cell: ({ row }) => 
        {
            const server: ElDewritoServer = row.original;

            if (!server.passworded) 
            {
                return h('span', { class: 'block mx-auto w-8' });
            }

            return h('span', { class: 'flex mx-auto w-8 h-5 items-center justify-center', title: 'Password protected' },
                h('span', 
                {
                    class: 'block mx-auto w-5 h-5 leading-none text-muted-foreground relative top-[1px] icon-mask icon-lock',
                    ariaHidden: 'true',
                })
            );
        },
    },
    {
        accessorKey: 'name',
        header: makeSortHeader('Name'),
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
        header: makeSortHeader('Hostname'),
        cell: ({ row }) => row.getValue('name') || row.original.info?.server_name || row.original.info?.hostname || ''
    },
    {
        accessorKey: 'variant',
        header: makeSortHeader('GameVariant'),
        cell: ({ row }) => {
            const info = row.original.info || {};
            return info.gamevariant || info.game_variant || info.variant || info.variant_name || info.gamevariant || '';
        }
    },
    {
        accessorKey: 'gametype',
        header: makeSortHeader('Gametype'),
        cell: ({ row }) => row.original.info?.gametype_name || row.original.info?.gametype || ''
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
                    <div class="min-w-[160px] h-10 flex items-center rounded-md border border-input bg-background">
                        <Select v-model="selected" class="h-full bg-transparent border-0" :options="[
                            { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.png', iconRounded: true },
                            { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.png', iconRounded: true },
                            { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.png', iconRounded: true },
                            { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.png', iconRounded: true },
                        ]" :full-width-trigger="true">
                            <template #trigger-content>
                                <img v-if="selected === 'eldewrito'" src="/assets/logos/eldewrito.png" alt="ElDewrito" class="w-6 h-6 mr-2 object-contain rounded-full" />
                                <img v-else-if="selected === 'haloce' || selected === 'halopc'" src="/assets/logos/haloce.png" alt="Halo" class="w-6 h-6 mr-2 object-contain rounded-full" />
                                <img v-else src="/assets/logos/cartographer.png" alt="Cartographer" class="w-6 h-6 mr-2 object-contain rounded-full" />
                            </template>
                        </Select>
                    </div>
                </template>
            </DataTable>
        </div>

        <div v-else-if="selected === 'haloce' || selected === 'halopc'">
            <DataTable :columns="haloColumns" :data="haloServers" :players="currentPlayers" :servers="currentServers" :initial-sorting="[{ id: 'players', desc: true }]" :searchOptions="[
                { label: 'All', value: 'all' },
                { label: 'Hostname', value: 'name' },
                { label: 'GameVariant', value: 'variant' },
                { label: 'Gametype', value: 'gametype' },
                { label: 'Map', value: 'map' },
            ]">
                <template #left>
                    <div class="min-w-[160px] h-10 flex items-center rounded-md border border-input bg-background">
                        <Select v-model="selected" class="h-full bg-transparent border-0" :options="[
                            { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.png', iconRounded: true },
                            { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.png', iconRounded: true },
                            { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.png', iconRounded: true },
                            { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.png', iconRounded: true },
                        ]" :full-width-trigger="true">
                            <template #trigger-content>
                                <img v-if="selected === 'eldewrito'" src="/assets/logos/eldewrito.png" alt="ElDewrito" class="w-6 h-6 mr-2 object-contain rounded-full" />
                                <img v-else-if="selected === 'haloce' || selected === 'halopc'" src="/assets/logos/haloce.png" alt="Halo" class="w-6 h-6 mr-2 object-contain rounded-full" />
                                <img v-else src="/assets/logos/cartographer.png" alt="Cartographer" class="w-6 h-6 mr-2 object-contain rounded-full" />
                            </template>
                        </Select>
                    </div>
                </template>
            </DataTable>
        </div>

        <div v-else>
            <CartographerBrowser ref="cartoRef">
                <template #left>
                    <div class="min-w-[160px] h-10 flex items-center rounded-md border border-input bg-background">
                        <Select v-model="selected" class="h-full bg-transparent border-0" :options="[
                            { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.png', iconRounded: true },
                            { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.png', iconRounded: true },
                            { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.png', iconRounded: true },
                            { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.png', iconRounded: true },
                        ]" :full-width-trigger="true">
                            <template #trigger-content>
                                <img v-if="selected === 'eldewrito'" src="/assets/logos/eldewrito.png" alt="ElDewrito" class="w-6 h-6 mr-2 object-contain rounded-full" />
                                <img v-else-if="selected === 'haloce' || selected === 'halopc'" src="/assets/logos/haloce.png" alt="Halo" class="w-6 h-6 mr-2 object-contain rounded-full" />
                                <img v-else src="/assets/logos/cartographer.png" alt="Cartographer" class="w-6 h-6 mr-2 object-contain rounded-full" />
                            </template>
                        </Select>
                    </div>
                </template>
            </CartographerBrowser>
        </div>
    </div>
</template>
