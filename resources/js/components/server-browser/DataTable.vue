<script setup lang="ts" generic="TData, TValue">
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { valueUpdater } from '@/components/ui/table/utils';
import {
    FlexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getSortedRowModel,
    useVueTable,
    type ColumnDef,
    type SortingState,
} from '@tanstack/vue-table';
import { ref } from 'vue';

const props = defineProps<{
    columns: ColumnDef<TData, TValue>[];
    data: TData[];
    searchOptions?: { label: string; value: string }[];
    initialSearchMode?: string;
    initialSorting?: SortingState;
    players?: number | null;
    servers?: number | null;
}>();

const DEFAULT_SEARCH_OPTIONS = [
    { label: 'All', value: 'all' },
    { label: 'Server', value: 'name' },
    { label: 'Host', value: 'host' },
    { label: 'Mods', value: 'mods' },
];

const sorting = ref<SortingState>(props.initialSorting ?? [{ id: 'numPlayers', desc: true }]);
const globalFilter = ref('');
const searchMode = ref<string>(props.initialSearchMode ?? 'all');
const searchOptions = props.searchOptions ?? DEFAULT_SEARCH_OPTIONS;

function debounce<T extends (...args: never[]) => void>(fn: T, wait: number): T {
    let timer: ReturnType<typeof setTimeout> | undefined;

    return ((...args: Parameters<T>) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
    }) as T;
}

const debouncedSetFilter = debounce((v: string) => {
    globalFilter.value = v;
}, 200);

type Row = Record<string, unknown>;

function matchesSearch(original: Row, mode: string, needle: string): boolean {
    const check = (val: unknown) =>
        String(val ?? '')
            .toLowerCase()
            .includes(needle);
    const mods = Array.isArray(original.mods) ? (original.mods as Row[]) : [];
    const modMatches = () => mods.some((mod) => check(mod?.mod_name));

    switch (mode) {
        case 'name':
        case 'server':
            return check(original.name) || check(original.server_name) || check(original.hostname);
        case 'host':
            return check(original.hostPlayer);
        case 'mods':
            return modMatches();
        case 'map':
            return check(original.map) || check(original.map_name) || check(original.mapName);
        case 'gametype':
            return check(original.gametype) || check(original.gametype_name);
        case 'variant':
            return check(original.variant) || check(original.variant_name) || check(original.variantType);
        case 'description':
            return check(original.description);
        default: {
            const fields = [
                original.name,
                original.server_name,
                original.hostname,
                original.hostPlayer,
                original.map,
                original.map_name,
                original.gametype,
                original.variant,
                original.description,
            ];

            return fields.some(check) || modMatches();
        }
    }
}

const table = useVueTable({
    get data() {
        return props.data;
    },
    get columns() {
        return props.columns;
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: (updaterOrValue) => valueUpdater(updaterOrValue, sorting),
    onGlobalFilterChange: (updaterOrValue) => valueUpdater(updaterOrValue, globalFilter),
    globalFilterFn: (row, _columnId, filterValue) => {
        const needle = String(filterValue ?? '').toLowerCase();

        return !needle || matchesSearch(row.original as Row, String(searchMode.value || 'all'), needle);
    },
    state: {
        get sorting() {
            return sorting.value;
        },
        get globalFilter() {
            return globalFilter.value;
        },
    },
});
</script>

<template>
    <!-- Toolbar -->
    <div class="flex flex-col gap-3 pb-4 sm:flex-row sm:items-center">
        <div class="flex items-center gap-3">
            <div class="flex-shrink-0">
                <slot name="left" />
            </div>

            <div class="relative min-w-0 flex-1 sm:max-w-sm">
                <Input
                    class="rounded-lg border-border/60 bg-muted/40 pr-10 transition-colors focus:bg-background"
                    :placeholder="searchMode === 'all' ? 'Search servers...' : `Search by ${searchMode}...`"
                    :model-value="globalFilter"
                    @update:model-value="debouncedSetFilter(String($event))"
                />
                <div class="absolute top-1/2 right-2 -translate-y-1/2">
                    <Select v-model="searchMode" :options="searchOptions" :icon-only="true" />
                </div>
            </div>
        </div>

        <div class="flex items-center gap-3 text-sm sm:ml-auto sm:justify-end">
            <div class="flex items-center gap-1.5 rounded-md bg-muted/50 px-2.5 py-1">
                <span class="font-semibold text-foreground tabular-nums">{{ props.players ?? '—' }}</span>
                <span class="text-xs text-muted-foreground">Players</span>
            </div>
            <div class="flex items-center gap-1.5 rounded-md bg-muted/50 px-2.5 py-1">
                <span class="font-semibold text-foreground tabular-nums">{{ props.servers ?? '—' }}</span>
                <span class="text-xs text-muted-foreground">Servers</span>
            </div>
        </div>
    </div>

    <!-- Desktop: table view -->
    <div class="hidden rounded-xl border border-border/60 bg-card shadow-sm md:block">
        <Table class="text-sm">
            <TableHeader>
                <TableRow
                    v-for="headerGroup in table.getHeaderGroups()"
                    :key="headerGroup.id"
                    class="border-b border-border/80 bg-muted/30 hover:bg-transparent"
                >
                    <TableHead v-for="header in headerGroup.headers" :key="header.id" class="text-xs tracking-wide uppercase">
                        <FlexRender
                            v-if="!header.isPlaceholder"
                            :render="header.column.columnDef.header"
                            :props="header.getContext()"
                            class="p-0 font-semibold text-muted-foreground! hover:text-foreground!"
                        />
                    </TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                <template v-if="table.getRowModel().rows?.length">
                    <TableRow
                        v-for="(row, idx) in table.getRowModel().rows"
                        :key="row.id"
                        class="transition-colors duration-100 hover:bg-muted/40"
                        :style="idx % 2 === 1 ? { backgroundColor: 'var(--stripe)' } : undefined"
                    >
                        <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                            <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" class="text-wrap" />
                        </TableCell>
                    </TableRow>
                </template>
                <template v-else>
                    <TableRow>
                        <TableCell :colspan="columns.length" class="h-24 text-center text-muted-foreground">No servers.</TableCell>
                    </TableRow>
                </template>
            </TableBody>
        </Table>
    </div>

    <!-- Mobile: card view -->
    <div class="flex flex-col gap-2 md:hidden">
        <template v-if="table.getRowModel().rows?.length">
            <div v-for="row in table.getRowModel().rows" :key="row.id" class="rounded-lg border border-border/60 bg-card p-3 shadow-sm">
                <slot name="mobile-card" :row="row.original" :row-model="row" />
            </div>
        </template>
        <div v-else class="rounded-lg border border-border/60 bg-card p-8 text-center text-muted-foreground shadow-sm">No servers.</div>
    </div>
</template>
