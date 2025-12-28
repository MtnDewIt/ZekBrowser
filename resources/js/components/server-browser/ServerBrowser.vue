<script setup lang="ts">
import type { ElDewritoServer } from '@/models/ElDewritoServer';
import DataTable from '@/components/server-browser/DataTable.vue';
import ModsCard from '@/components/server-browser/ModsCard.vue';
import { Button } from '@/components/ui/button';
import { ArrowUpDown, ExternalLink } from 'lucide-vue-next';
import { h, reactive } from 'vue';
import { HoverCard, HoverCardTrigger, HoverCardContent } from '@/components/ui/hover-card';
import generateEmblem from '@/lib/emblemGenerator';

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

interface Props {
    servers: ElDewritoServer[];
}

defineProps<Props>();

const columns: ColumnDef<ElDewritoServer>[] = [
    {
        accessorKey: 'name',
        header: ({ column }) => {
            return h(Button, {
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['Name', h(ArrowUpDown, { size: 14 })])
        },
        cell: ({ row }) => h('div', { class: 'md:whitespace-nowrap' }, [
            h('span', { class: 'font-bold!' }, row.getValue('name')),
        ]),
    },
    {
        accessorKey: 'hostPlayer',
        header: ({ column }) => {
            return h(Button, {
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['Host', h(ArrowUpDown, { size: 14 })])
        },
        cell: ({ row }) => row.getValue('hostPlayer'),
    },
    {
        id: 'status',
        header: ({ column }) => {
            return h(Button, {
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['Status', h(ArrowUpDown, { size: 14 })])
        },
        accessorFn: (row) => row.statusFormatted(),
        cell: ({ row }) => row.original.statusFormatted(),
    },
    {
        accessorKey: 'mods',
        header: ({ column }) => {
            return h(Button, {
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['Mods', h(ArrowUpDown, { size: 14 })])
        },
        accessorFn: (row) => row.mods?.length ?? 0,
        cell: ({ row }) => {
            const mods = row.original.mods;
            if (!mods || mods.length === 0) return null;
            return h(ModsCard, {
                mods: mods,
                jsonUrl: `http://${row.original.ip}/mods`,
                showAsNumber: true,
            });
        },
    },
    {
        accessorKey: 'numPlayers',
        header: ({ column }) => {
            return h(Button, {
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['Players', h(ArrowUpDown, { size: 14 })])
        },
        cell: ({ row }) => {
            const server: ElDewritoServer = row.original;

            const countText = `${server.numPlayers}/${server.maxPlayers}`;

            const players = server.players ?? [];

            return h(HoverCard, null, () => [
                h(HoverCardTrigger, { asChild: true }, () => h('span', null, countText)),
                h(HoverCardContent, null, () => {
                    if (!players || players.length === 0) {
                        return h('div', 'No players');
                    }

                    return h('div', { class: 'text-sm' }, [
                        h('div', { class: 'font-semibold mb-2' }, 'Players'),
                        h('ul', { class: 'list-none p-0 space-y-1' },
                            players.map((p: any) => {
                                    const name = typeof p === 'string' ? p : (p.name ?? p.playerName ?? p.displayName ?? p.player_name ?? JSON.stringify(p));

                                    const tag = (typeof p === 'object' && p !== null) ? (
                                        p.serviceTag ?? p.service_tag ?? p.tag ?? p.playerTag ?? p.player_tag ?? p.stag ?? null
                                    ) : null;

                                    // try to find an emblem string on common properties
                                    const emblemStr = (typeof p === 'object' && p !== null) ? (p.emblem ?? p.emblemUrl ?? p.emblem_url ?? p.emblemString ?? null) : null;
                                    if (emblemStr) { void ensureEmblem(emblemStr); }
                                    const emblemSrc = emblemStr ? getEmblemSrc(emblemStr) : '';

                                    return h('li', { class: 'flex items-center text-sm space-x-2' }, [
                                        (emblemStr && emblemSrc) ? h('img', { src: emblemSrc, class: 'w-7 h-7 rounded-sm mr-2 flex-shrink-0', alt: 'emblem' }) : null,
                                        h('span', { class: 'truncate' }, name),
                                        tag ? h('span', { class: 'text-xs text-muted-foreground' }, `[${tag}]`) : null,
                                    ]);
                                })
                        ),
                    ]);
                }),
            ]);
        },
    },
    {
        accessorKey: 'eldewritoVersion',
        header: ({ column }) => {
            return h(Button, {
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['Version', h(ArrowUpDown, { size: 14 })])
        },
        cell: ({ row }) => row.original.versionWithoutTrailingZero(),
    },
    {
        accessorKey: 'ip',
        header: ({ column }) => {
            return h(Button, {
                class: 'text-left',
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
            }, () => ['IP', h(ArrowUpDown, { size: 14 })])
        },
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
                            class: 'ml-1 inline-flex items-start',
                        }, h(ExternalLink, {
                            size: 16,
                            class: 'inline-block translate-y-[-0.25em]',
                        }),
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
