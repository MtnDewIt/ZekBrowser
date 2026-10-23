<script setup lang="ts" generic="TData">
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { searchText, type ServerListDefinition } from '@/lib/serverList';
import {
    FlexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getSortedRowModel,
    useVueTable,
    type SortingState,
    type Updater,
} from '@tanstack/vue-table';
import { onBeforeUnmount, onMounted, ref, type Ref, type VNode } from 'vue';

/** Sortable, searchable server table with a card layout on small screens. */
const props = defineProps<{
    definition: ServerListDefinition<TData>;
    data: TData[];
    players?: number | null;
    servers?: number | null;
}>();

const sorting = ref<SortingState>(props.definition.initialSorting);
const globalFilter = ref('');
const searchMode = ref('all');

let filterTimer: ReturnType<typeof setTimeout> | undefined;

function setFilter(value: string) {
    clearTimeout(filterTimer);
    filterTimer = setTimeout(() => (globalFilter.value = value), 200);
}

const update =
    <T,>(target: Ref<T>) =>
    (updaterOrValue: Updater<T>) => {
        target.value = typeof updaterOrValue === 'function' ? (updaterOrValue as (old: T) => T)(target.value) : updaterOrValue;
    };

const table = useVueTable({
    get data() {
        return props.data;
    },
    get columns() {
        return props.definition.columns;
    },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: update(sorting),
    onGlobalFilterChange: update(globalFilter),
    globalFilterFn: (row, _columnId, filterValue) => {
        const needle = String(filterValue ?? '').toLowerCase();

        return (
            !needle ||
            searchText(props.definition, row.original, searchMode.value).some((v) =>
                String(v ?? '')
                    .toLowerCase()
                    .includes(needle),
            )
        );
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

const MobileCard = (p: { render: (row: TData) => VNode; row: TData }) => p.render(p.row);

// Horizontal wheel scrolls the table when it overflows; vertical wheel stays with the page.
const container = ref<HTMLElement | null>(null);

function onWheel(e: WheelEvent) {
    const el = container.value;

    if (el && Math.abs(e.deltaX) > Math.abs(e.deltaY) && el.scrollWidth > el.clientWidth) {
        e.preventDefault();
        el.scrollLeft += e.deltaX;
    }
}

onMounted(() => container.value?.addEventListener('wheel', onWheel, { passive: false }));
onBeforeUnmount(() => container.value?.removeEventListener('wheel', onWheel));

const CELL = 'px-3 py-2.5 align-middle whitespace-nowrap';
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
                    @update:model-value="setFilter(String($event))"
                />
                <div class="absolute top-1/2 right-2 -translate-y-1/2">
                    <Select v-model="searchMode" :options="definition.search" :icon-only="true" />
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
        <div ref="container" class="relative w-full overflow-x-auto">
            <table class="w-full caption-bottom text-sm">
                <thead class="[&_tr]:border-b">
                    <tr
                        v-for="headerGroup in table.getHeaderGroups()"
                        :key="headerGroup.id"
                        class="border-b border-border/80 bg-muted/30 transition-colors hover:bg-transparent"
                    >
                        <th
                            v-for="header in headerGroup.headers"
                            :key="header.id"
                            class="h-10 px-3 text-left align-middle text-xs font-medium tracking-wide whitespace-nowrap text-muted-foreground uppercase"
                        >
                            <FlexRender
                                v-if="!header.isPlaceholder"
                                :render="header.column.columnDef.header"
                                :props="header.getContext()"
                                class="p-0 font-semibold text-muted-foreground! hover:text-foreground!"
                            />
                        </th>
                    </tr>
                </thead>
                <tbody class="[&_tr:last-child]:border-0">
                    <template v-if="table.getRowModel().rows?.length">
                        <tr
                            v-for="(row, idx) in table.getRowModel().rows"
                            :key="row.id"
                            class="border-b border-border/40 transition-colors duration-100 hover:bg-muted/40"
                            :style="idx % 2 === 1 ? { backgroundColor: 'var(--stripe)' } : undefined"
                        >
                            <td v-for="cell in row.getVisibleCells()" :key="cell.id" :class="CELL">
                                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" class="text-wrap" />
                            </td>
                        </tr>
                    </template>
                    <tr v-else class="border-b border-border/40">
                        <td :colspan="definition.columns.length" :class="[CELL, 'h-24 text-center text-muted-foreground']">No servers.</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Mobile: card view -->
    <div class="flex flex-col gap-2 md:hidden">
        <template v-if="table.getRowModel().rows?.length">
            <div v-for="row in table.getRowModel().rows" :key="row.id" class="rounded-lg border border-border/60 bg-card p-3 shadow-sm">
                <MobileCard :render="definition.mobileCard" :row="row.original" />
            </div>
        </template>
        <div v-else class="rounded-lg border border-border/60 bg-card p-8 text-center text-muted-foreground shadow-sm">No servers.</div>
    </div>
</template>
