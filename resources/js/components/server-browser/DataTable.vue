<script setup lang="ts" generic="TData, TValue">

import 
{
    ColumnDef,
    ColumnFiltersState,
    FlexRender,
    SortingState,
    getCoreRowModel,
    getFilteredRowModel,
    getSortedRowModel,
    useVueTable,
} 
from '@tanstack/vue-table';

import 
{
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} 
from '@/components/ui/table';

import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';

import { valueUpdater } from '@/lib/utils';
import { ref } from 'vue';

const props = defineProps<
{
    columns: ColumnDef<TData, TValue>[]
    data: TData[]
    searchOptions?: { label: string; value: string }[]
    initialSearchMode?: string
    initialSorting?: SortingState
    players?: number | null
    servers?: number | null
}>();

const sorting = ref<SortingState>(props.initialSorting ?? [
    {
        id: 'numPlayers',
        desc: true,
    }
]);

const columnFilters = ref<ColumnFiltersState>([])
const globalFilter = ref('')
const searchMode = ref<string>(props.initialSearchMode ?? 'all')
const defaultSearchOptions = [
    { label: 'All', value: 'all' },
    { label: 'Server', value: 'name' },
    { label: 'Host', value: 'host' },
    { label: 'Mods', value: 'mods' },
]
const searchOptions = props.searchOptions ?? defaultSearchOptions;

const table = useVueTable({
    get data() { return props.data },
    get columns() { return props.columns },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: updaterOrValue => valueUpdater(updaterOrValue, sorting),
    onColumnFiltersChange: updaterOrValue => valueUpdater(updaterOrValue, columnFilters),
    onGlobalFilterChange: updaterOrValue => valueUpdater(updaterOrValue, globalFilter),
    getFilteredRowModel: getFilteredRowModel(),
    globalFilterFn: (row, columnId, filterValue) => 
    {
        const searchValue = String(filterValue).toLowerCase();
        const mode = String(searchMode.value || 'all');

        if (!searchValue) return true;

        const check = (val: any) => String(val ?? '').toLowerCase().includes(searchValue);

        if (mode === 'name' || mode === 'server') {
            return check(row.getValue('name')) || check(row.getValue('server_name')) || check(row.getValue('hostname'));
        }

        if (mode === 'host') {
            return check(row.getValue('hostPlayer'));
        }

        if (mode === 'mods') {
            const mods = row.original?.mods || [];
            return mods.some((mod: any) => check(mod?.mod_name));
        }

        if (mode === 'map') {
            return check(row.getValue('map')) || check(row.getValue('map_name')) || check(row.getValue('mapName'));
        }

        if (mode === 'gametype') {
            return check(row.getValue('gametype')) || check(row.getValue('gametype_name'));
        }

        if (mode === 'variant') {
            return check(row.getValue('variant')) || check(row.getValue('variant_name')) || check(row.getValue('variantType'));
        }

        if (mode === 'description') {
            return check(row.getValue('description')) || check(row.original?.description);
        }

        // default 'all' mode: try several common fields
        const fields = [
            row.getValue('name'),
            row.getValue('server_name'),
            row.getValue('hostPlayer'),
            row.getValue('map'),
            row.getValue('map_name'),
            row.getValue('gametype'),
            row.getValue('variant'),
            row.getValue('description'),
        ];
        if (fields.some(f => check(f))) return true;
        const mods = row.original?.mods || [];
        if (mods.some((mod: any) => check(mod?.mod_name))) return true;
        return false;
    },
    state: 
    {
        get sorting() 
        { 
            return sorting.value 
        },
        
        get columnFilters() 
        { 
            return columnFilters.value 
        },

        get globalFilter() 
        { 
            return globalFilter.value 
        },
    },
});
</script>

<template>

    <!-- Toolbar: stacks on mobile -->
    <div class="flex flex-col gap-3 pb-4 sm:flex-row sm:items-center">
        <div class="flex items-center gap-3">
            <div class="flex-shrink-0">
                <slot name="left" />
            </div>

            <div class="relative flex-1 min-w-0 sm:max-w-sm">
                <Input 
                    class="rounded-lg pr-10 bg-muted/40 border-border/60 focus:bg-background transition-colors" 
                    :placeholder="searchMode === 'all' ? 'Search servers...' : `Search by ${searchMode}...`"
                    :model-value="globalFilter"
                    @update:model-value="globalFilter = $event" 
                />
                <div class="absolute right-2 top-1/2 -translate-y-1/2">
                    <Select v-model="searchMode" :options="searchOptions" :iconOnly="true" />
                </div>
            </div>
        </div>

        <div class="flex items-center gap-3 text-sm sm:ml-auto sm:justify-end">
            <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/50">
                <span class="font-semibold tabular-nums text-foreground">{{ props.players ?? '—' }}</span>
                <span class="text-muted-foreground text-xs">Players</span>
            </div>
            <div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/50">
                <span class="font-semibold tabular-nums text-foreground">{{ props.servers ?? '—' }}</span>
                <span class="text-muted-foreground text-xs">Servers</span>
            </div>
        </div>
    </div>

    <!-- Desktop: table view -->
    <div class="hidden md:block rounded-xl border border-border/60 bg-card shadow-sm">
        <Table class="text-sm">
            <TableHeader>
                <TableRow
                    v-for="headerGroup in table.getHeaderGroups()"
                    :key="headerGroup.id"
                    class="hover:bg-transparent border-b border-border/80 bg-muted/30"
                >
                    <TableHead
                        v-for="header in headerGroup.headers"
                        :key="header.id"
                        class="text-xs uppercase tracking-wide"
                    >
                        <FlexRender
                            v-if="!header.isPlaceholder" :render="header.column.columnDef.header"
                            :props="header.getContext()"
                            class="font-semibold p-0 text-muted-foreground! hover:text-foreground!"
                        />
                    </TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                <template v-if="table.getRowModel().rows?.length">
                    <TableRow
                        v-for="(row, idx) in table.getRowModel().rows" :key="row.id"
                        :data-state="row.getIsSelected() ? 'selected' : undefined"
                        :class="[
                            'transition-colors duration-100 hover:bg-muted/40',
                        ]"
                        :style="idx % 2 === 1 ? { backgroundColor: 'var(--stripe)' } : undefined"
                    >
                        <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                            <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" class="text-wrap" />
                        </TableCell>
                    </TableRow>
                </template>
                <template v-else>
                    <TableRow>
                        <TableCell :colspan="columns.length" class="h-24 text-center text-muted-foreground">
                            No servers.
                        </TableCell>
                    </TableRow>
                </template>
            </TableBody>
        </Table>
    </div>

    <!-- Mobile: card view -->
    <div class="md:hidden flex flex-col gap-2">
        <template v-if="table.getRowModel().rows?.length">
            <div
                v-for="row in table.getRowModel().rows"
                :key="row.id"
                class="rounded-lg border border-border/60 bg-card p-3 shadow-sm"
            >
                <slot name="mobile-card" :row="row.original" :row-model="row">
                    <!-- Default mobile card fallback -->
                    <div class="flex items-start justify-between gap-2">
                        <div class="min-w-0 flex-1">
                            <div class="font-bold text-sm text-foreground truncate">
                                {{ row.original.name || row.original.server_name || row.original.hostname || '—' }}
                            </div>
                            <div class="text-xs text-muted-foreground mt-0.5">
                                {{ row.original.map || row.original.map_name || row.original.mapName || '' }}
                                <span v-if="row.original.gametype || row.original.gametype_name" class="ml-1">
                                    · {{ row.original.gametype || row.original.gametype_name }}
                                </span>
                            </div>
                        </div>
                        <div class="text-right flex-shrink-0">
                            <span class="text-sm font-semibold tabular-nums text-foreground">
                                {{ typeof row.original.numPlayers !== 'undefined' 
                                    ? `${row.original.numPlayers}/${row.original.maxPlayers}` 
                                    : (row.original.players && typeof row.original.players === 'object'
                                        ? `${row.original.players.filled ?? '?'}/${row.original.players.max ?? '?'}`
                                        : '') }}
                            </span>
                        </div>
                    </div>
                    <div v-if="row.original.variant || row.original.variant_name || row.original.hostPlayer" class="text-xs text-muted-foreground mt-1.5 flex flex-wrap gap-x-3">
                        <span v-if="row.original.variant || row.original.variant_name">{{ row.original.variant || row.original.variant_name }}</span>
                        <span v-if="row.original.hostPlayer">Host: {{ row.original.hostPlayer }}</span>
                    </div>
                </slot>
            </div>
        </template>
        <div v-else class="rounded-lg border border-border/60 bg-card p-8 text-center text-muted-foreground shadow-sm">
            No servers.
        </div>
    </div>
</template>
