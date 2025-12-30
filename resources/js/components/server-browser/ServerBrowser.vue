<script setup lang="ts">
import type { ElDewritoServer } from '@/models/ElDewritoServer';
import DataTable from '@/components/server-browser/DataTable.vue';
import ModsCard from '@/components/server-browser/ModsCard.vue';
import PlayersCard from '@/components/server-browser/PlayersCard.vue';
import { Button } from '@/components/ui/button';
// Removed icon imports; using static masked SVGs
import { h } from 'vue';
import type { ColumnDef } from '@tanstack/vue-table';

interface Props {
    servers: ElDewritoServer[];
}

defineProps<Props>();

// Shared sort icon helpers to avoid duplication and reflect sort state
const SORT_ICON_BASE = 'icon-mask inline-block w-3.5 h-3.5 ml-2 align-middle opacity-70';
const renderSortIcon = (state: false | 'asc' | 'desc') => {
    const variant = state === 'asc' ? 'icon-sort-up' : state === 'desc' ? 'icon-sort-down' : 'icon-sort';
    return h('span', { class: `${SORT_ICON_BASE} ${variant}`, ariaHidden: 'true' });
};
const makeSortHeader = (label: string, buttonClass = '') => ({ column }) => {
    const state = column.getIsSorted();
    return h(Button, {
        class: ['gap-0', buttonClass].filter(Boolean).join(' '),
        onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
    }, () => [label, renderSortIcon(state)]);
};

const columns: ColumnDef<ElDewritoServer>[] = [
    {
        id: 'passworded',
        accessorFn: (row) => (row.passworded ? 1 : 0),
        header: ({ column }) => {
            const icon = h('span', {
                class: 'block mx-auto w-5 h-5 leading-none text-muted-foreground relative top-[1px] icon-mask icon-lock',
                ariaHidden: 'true',
            });
            return h(Button, {
                class: 'block mx-auto w-8 h-8 p-0 flex items-center justify-center',
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
                title: 'Sort by password protection',
            }, () => [icon])
        },
        cell: ({ row }) => {
            const server: ElDewritoServer = row.original;
            if (!server.passworded) return h('span', { class: 'block mx-auto w-8' });
            return h('span', { class: 'flex mx-auto w-8 h-5 items-center justify-center', title: 'Password protected' },
                h('span', {
                    class: 'block mx-auto w-5 h-5 leading-none text-muted-foreground relative top-[1px] icon-mask icon-lock',
                    ariaHidden: 'true',
                })
            );
        },
    },
    {
        accessorKey: 'name',
        header: makeSortHeader('Name'),
        cell: ({ row }) => h('div', { class: 'md:whitespace-nowrap' }, [
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
        cell: ({ row }) => {
            const mods = row.original.mods;
            if (!mods || mods.length === 0) return 0;
            return h(ModsCard, {
                mods: mods,
                jsonUrl: `http://${row.original.ip}/mods`,
                showAsNumber: true,
            });
        },
    },
    {
        accessorKey: 'numPlayers',
        header: makeSortHeader('Players'),
            cell: ({ row }) => {
            const server: ElDewritoServer = row.original;
            return h(PlayersCard, {
                numPlayers: server.numPlayers,
                maxPlayers: server.maxPlayers,
                players: server.players,
                teams: server.teams,
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
        cell: ({ row }) => {
            const server = row.original;

            return h('span', { class: 'inline-flex items-center whitespace-nowrap' },
                [
                    h('a', {
                        href: `eldewrito://${server.ip}`,
                        target: '_blank',
                        title: `Click to join ${server.name}`,
                    }, server.ip),
                    h(
                        'a', {
                            href: `http://${server.ip}`,
                            target: '_blank',
                            title: `View JSON info`,
                            class: 'ml-1 inline-flex items-center',
                        },
                        h('span', {
                            class: 'icon-mask icon-external inline-block w-4 h-4 opacity-80 align-middle',
                            ariaHidden: 'true',
                        })
                    ),
                ]
            );
        },
    },
]

</script>

<template>
    <DataTable :columns="columns" :data="servers" />
</template>
