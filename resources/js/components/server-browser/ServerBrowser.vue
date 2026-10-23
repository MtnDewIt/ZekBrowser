<script setup lang="ts">
import BrowserSelect from '@/components/server-browser/BrowserSelect.vue';
import CartographerBrowser from '@/components/server-browser/CartographerBrowser.vue';
import DataTable from '@/components/server-browser/DataTable.vue';
import HaloPlayersCard from '@/components/server-browser/HaloPlayersCard.vue';
import ModsCard from '@/components/server-browser/ModsCard.vue';
import PlayersCard from '@/components/server-browser/PlayersCard.vue';
import { ValidationError } from '@/exceptions/ValidationError';
import { fetchJson, isBrowserType, listUrl, type BrowserType, type ServerListResponse } from '@/lib/api';
import { makeSortHeader } from '@/lib/tableHeaders';
import { ElDewritoServer, type ElDewritoServerData } from '@/models/ElDewritoServer';
import type { ColumnDef } from '@tanstack/vue-table';
import { computed, h, onMounted, ref, watch } from 'vue';

const props = defineProps<{
    /** Base URL of the JSON API, e.g. "/api/". */
    apiBase: string;
}>();

const emit = defineEmits<{
    (e: 'browser-change', type: BrowserType): void;
}>();

const STORAGE_KEY = 'zekbrowser.serverBrowser';

const selected = ref<BrowserType>('eldewrito');
const cartoRef = ref<InstanceType<typeof CartographerBrowser> | null>(null);

// --- ElDewrito ---------------------------------------------------------------

const eldewritoServers = ref<ElDewritoServer[]>([]);

const eldewritoPlayers = computed(() => eldewritoServers.value.reduce((sum, s) => sum + (Number(s.numPlayers) || 0), 0));

async function loadEldewrito(): Promise<void> {
    const data = await fetchJson<ServerListResponse<Record<string, Omit<ElDewritoServerData, 'ip'>>>>(listUrl(props.apiBase, 'eldewrito'));
    const list: ElDewritoServer[] = [];

    for (const [ip, server] of Object.entries(data.servers ?? {})) {
        try {
            list.push(new ElDewritoServer({ ip, ...server }));
        } catch (error) {
            if (error instanceof ValidationError) {
                console.warn(`Validation failed for ${ip}:`, error.errors);
            } else {
                console.error(`Unexpected error for server ${ip}:`, error);
            }
        }
    }

    eldewritoServers.value = list;
}

const eldewritoColumns: ColumnDef<ElDewritoServer>[] = [
    {
        id: 'passworded',
        accessorFn: (row) => (row.passworded ? 1 : 0),
        header: makeSortHeader(h('span', { class: 'w-5 h-5 leading-none text-muted-foreground icon-mask icon-lock', ariaHidden: 'true' }), {
            title: 'Sort by password protection',
            paddingRight: '0.5rem',
        }),
        cell: ({ row }) =>
            row.original.passworded
                ? h('span', {
                      class: 'block w-5 h-5 leading-none text-muted-foreground icon-mask icon-lock',
                      ariaHidden: 'true',
                      title: 'Password protected',
                  })
                : h('span', { class: 'block w-5 h-5' }),
    },
    {
        accessorKey: 'name',
        header: makeSortHeader('Server'),
        cell: ({ row }) => h('div', { class: 'md:whitespace-nowrap' }, [h('span', { class: 'font-bold!' }, row.original.name)]),
    },
    {
        accessorKey: 'hostPlayer',
        header: makeSortHeader('Host'),
        cell: ({ row }) => row.original.hostPlayer,
    },
    {
        id: 'status',
        header: makeSortHeader('Status'),
        accessorFn: (row) => row.statusFormatted(),
        cell: ({ row }) => row.original.statusFormatted(),
    },
    {
        id: 'mods',
        header: makeSortHeader('Mods'),
        accessorFn: (row) => row.mods?.length ?? 0,
        cell: ({ row }) => {
            const mods = row.original.mods;

            if (!mods || mods.length === 0) {
                return 0;
            }

            return h(ModsCard, { mods, jsonUrl: `http://${row.original.ip}/mods`, showAsNumber: true });
        },
    },
    {
        accessorKey: 'numPlayers',
        header: makeSortHeader('Players'),
        cell: ({ row }) => {
            const server = row.original;

            return h(PlayersCard, {
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
        header: makeSortHeader('IP', { buttonClass: 'text-left' }),
        cell: ({ row }) => {
            const server = row.original;

            return h('span', { class: 'inline-flex items-center whitespace-nowrap' }, [
                h('a', { href: `eldewrito://${server.ip}`, target: '_blank', title: `Click to join ${server.name}` }, server.ip),
                h(
                    'a',
                    { href: `http://${server.ip}`, target: '_blank', title: 'View JSON info', class: 'ml-1 inline-flex items-center' },
                    h('span', { class: 'icon-mask icon-external inline-block w-4 h-4 opacity-80 align-middle', ariaHidden: 'true' }),
                ),
            ]);
        },
    },
];

// --- Halo CE / Halo PC -------------------------------------------------------

type GameSpyInfo = Record<string, string | number | undefined>;

interface HaloServerRaw {
    address?: string;
    ip?: string;
    host?: string;
    port?: number | string;
    game?: string;
    info?: GameSpyInfo;
    players?: number;
}

interface HaloServer {
    address: string;
    port: number | string;
    info: GameSpyInfo;
    players: number;
    name: string;
    variant: string;
    gametype: string;
    map: string;
}

const haloServers = ref<HaloServer[]>([]);
const haloPlayers = ref(0);
const haloServerCount = ref(0);

function text(value: unknown): string {
    return value === undefined || value === null ? '' : String(value);
}

function toHaloServer(s: HaloServerRaw): HaloServer {
    const info = s.info ?? {};

    return {
        address: s.address || s.ip || s.host || '',
        port: s.port || info.port || '',
        info,
        players: Number(info.numplayers ?? s.players ?? 0),
        name: text(info.hostname || info.server_name),
        variant: text(info.gamevariant || info.game_variant || info.variant),
        gametype: text(info.gametype || info.gametype_name),
        map: text(info.mapname || info.map_name || info.map),
    };
}

async function loadHalo(type: 'haloce' | 'halopc'): Promise<void> {
    const data = await fetchJson<ServerListResponse<HaloServerRaw[]>>(listUrl(props.apiBase, type), 10000);
    const list = Array.isArray(data.servers) ? data.servers.map(toHaloServer) : [];

    haloServers.value = list;
    haloPlayers.value = Number(data.count?.players ?? list.reduce((sum, s) => sum + s.players, 0));
    haloServerCount.value = Number(data.count?.servers ?? list.length);
}

const haloSearchOptions = [
    { label: 'All', value: 'all' },
    { label: 'Server', value: 'name' },
    { label: 'Variant', value: 'variant' },
    { label: 'Gametype', value: 'gametype' },
    { label: 'Map', value: 'map' },
];

const haloColumns: ColumnDef<HaloServer>[] = [
    {
        accessorKey: 'name',
        header: makeSortHeader('Server'),
        cell: ({ row }) => row.original.name,
    },
    {
        accessorKey: 'map',
        header: makeSortHeader('Map'),
        cell: ({ row }) => row.original.map,
    },
    {
        accessorKey: 'gametype',
        header: makeSortHeader('Gametype'),
        cell: ({ row }) => {
            const gt = row.original.gametype;

            return gt.trim().toLowerCase() === 'king' ? 'KOTH' : gt;
        },
    },
    {
        accessorKey: 'variant',
        header: makeSortHeader('Variant'),
        cell: ({ row }) => row.original.variant,
    },
    {
        id: 'players',
        header: makeSortHeader('Players'),
        accessorFn: (row) => row.players,
        cell: ({ row }) =>
            h(HaloPlayersCard, {
                numPlayers: row.original.players,
                maxPlayers: Number(row.original.info.maxplayers ?? 0),
                info: row.original.info,
            }),
    },
    {
        id: 'ipport',
        header: makeSortHeader('IP:Port', { buttonClass: 'text-left' }),
        cell: ({ row }) => h('span', { class: 'inline-flex items-center whitespace-nowrap' }, [`${row.original.address}:${row.original.port}`]),
    },
];

// --- Selection & refresh -----------------------------------------------------

/** Reload the active list. The parent calls this from the refresh button and the auto-refresh timer. */
async function refresh(): Promise<void> {
    switch (selected.value) {
        case 'eldewrito':
            return loadEldewrito();
        case 'haloce':
        case 'halopc':
            return loadHalo(selected.value);
        case 'cartographer':
            return cartoRef.value?.load();
    }
}

async function safeRefresh(): Promise<void> {
    try {
        await refresh();
    } catch (error) {
        console.warn(`Failed to load ${selected.value} servers:`, error);
    }
}

onMounted(() => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);

        if (isBrowserType(stored)) {
            selected.value = stored;
        }
    } catch {
        // localStorage unavailable
    }

    emit('browser-change', selected.value);

    // CartographerBrowser loads itself on mount; the other lists are loaded here.
    if (selected.value !== 'cartographer') {
        void safeRefresh();
    }
});

watch(selected, (value) => {
    try {
        localStorage.setItem(STORAGE_KEY, value);
    } catch {
        // ignore
    }

    emit('browser-change', value);

    if (value !== 'cartographer') {
        void safeRefresh();
    }
});

defineExpose({ refresh, getSelection: () => selected.value });
</script>

<template>
    <div>
        <div v-if="selected === 'eldewrito'">
            <DataTable :columns="eldewritoColumns" :data="eldewritoServers" :players="eldewritoPlayers" :servers="eldewritoServers.length">
                <template #left>
                    <BrowserSelect v-model="selected" />
                </template>
                <template #mobile-card="{ row }">
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0 flex-1">
                            <div class="flex items-center gap-1.5">
                                <span v-if="row.passworded" class="icon-mask icon-lock h-3.5 w-3.5 flex-shrink-0 text-muted-foreground" />
                                <span class="truncate text-sm font-bold text-foreground">{{ row.name }}</span>
                            </div>
                            <div class="mt-0.5 text-xs text-muted-foreground">
                                {{ row.statusFormatted() }}
                                <span v-if="row.hostPlayer" class="ml-1">· {{ row.hostPlayer }}</span>
                            </div>
                        </div>
                        <PlayersCard
                            :num-players="row.numPlayers"
                            :max-players="row.maxPlayers"
                            :players="row.players"
                            :teams="row.teams"
                            :team-scores="row.teamScores"
                            :server-version="row.eldewritoVersionShort ?? row.eldewritoVersion ?? ''"
                            :passworded="!!row.passworded"
                            class="flex-shrink-0 text-sm font-semibold text-foreground tabular-nums"
                        />
                    </div>
                    <div class="mt-1.5 flex items-center gap-2 text-xs text-muted-foreground">
                        <span v-if="row.eldewritoVersion">v{{ row.versionWithoutTrailingZero() }}</span>
                        <span
                            v-if="row.mods?.length"
                            class="inline-flex cursor-pointer items-center"
                            @click.stop="($event.currentTarget as HTMLElement).querySelector<HTMLElement>('.mods-count-button')?.click()"
                        >
                            Mods:&nbsp;<ModsCard :mods="row.mods" :json-url="`http://${row.ip}/mods`" :show-as-number="true" />
                        </span>
                    </div>
                </template>
            </DataTable>
        </div>

        <div v-else-if="selected === 'haloce' || selected === 'halopc'">
            <DataTable
                :columns="haloColumns"
                :data="haloServers"
                :players="haloPlayers"
                :servers="haloServerCount"
                :initial-sorting="[{ id: 'players', desc: true }]"
                :search-options="haloSearchOptions"
            >
                <template #left>
                    <BrowserSelect v-model="selected" />
                </template>
                <template #mobile-card="{ row }">
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0 flex-1">
                            <div class="truncate text-sm font-bold text-foreground">{{ row.name || '—' }}</div>
                            <div class="mt-0.5 text-xs text-muted-foreground">
                                {{ row.map }}
                                <span v-if="row.gametype" class="ml-1">· {{ row.gametype }}</span>
                            </div>
                        </div>
                        <HaloPlayersCard
                            :num-players="row.players"
                            :max-players="Number(row.info.maxplayers ?? 0)"
                            :info="row.info"
                            class="flex-shrink-0 text-sm font-semibold text-foreground tabular-nums"
                        />
                    </div>
                    <div v-if="row.variant" class="mt-1.5 text-xs text-muted-foreground">
                        {{ row.variant }}
                    </div>
                </template>
            </DataTable>
        </div>

        <div v-else>
            <CartographerBrowser ref="cartoRef" :api-base="apiBase">
                <template #left>
                    <BrowserSelect v-model="selected" />
                </template>
            </CartographerBrowser>
        </div>
    </div>
</template>
