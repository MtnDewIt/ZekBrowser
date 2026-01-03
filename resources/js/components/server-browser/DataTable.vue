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
}>();

const sorting = ref<SortingState>(
[
    { 
        id: 'numPlayers', 
        desc: true 
    }
]);

const columnFilters = ref<ColumnFiltersState>([])
const globalFilter = ref('')
const searchMode = ref<'all' | 'name' | 'host' | 'mods'>('all')
const searchOptions = 
[
    { 
        label: 'All', 
        value: 'all' 
    },
    { 
        label: 'Server Name', 
        value: 'name' 
    },
    { 
        label: 'Host', 
        value: 'host' 
    },
    { 
        label: 'Mods', 
        value: 'mods' 
    },
]

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
        const mode = searchMode.value;
        
        if (!searchValue) return true;
        
        if (mode === 'name') 
        {
            const name = String(row.getValue('name') || '').toLowerCase();
            return name.includes(searchValue);
        }
        
        if (mode === 'host') 
        {
            const host = String(row.getValue('hostPlayer') || '').toLowerCase();
            return host.includes(searchValue);
        }
        
        if (mode === 'mods') 
        {
            const mods = row.original?.mods || [];

            return mods.some(mod => 
                String(mod?.mod_name || '').toLowerCase().includes(searchValue)
            );
        }

        const name = String(row.getValue('name') || '').toLowerCase();
        const host = String(row.getValue('hostPlayer') || '').toLowerCase();
        const mods = row.original?.mods || [];

        const modMatch = mods.some(mod => 
            String(mod?.mod_name || '').toLowerCase().includes(searchValue)
        );
        
        return name.includes(searchValue) || host.includes(searchValue) || modMatch;
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

    <div class="flex items-center gap-2 py-4">
        <div class="relative w-full max-w-sm">
            <Input 
                class="rounded-md pr-10" 
                :placeholder="searchMode === 'all' ? 'Search servers...' : `Search by ${searchMode}...`"
                :model-value="globalFilter"
                @update:model-value="globalFilter = $event" 
            />
            <div class="absolute right-2 top-1/2 -translate-y-1/2">
                <Select v-model="searchMode" :options="searchOptions" :iconOnly="true" />
            </div>
        </div>
    </div>

    <Table class="text-md">
        <TableHeader class="border-b-2">
            <TableRow
                v-for="headerGroup in table.getHeaderGroups()"
                :key="headerGroup.id"
                class="hover:bg-transparent"
            >
                <TableHead
                    v-for="header in headerGroup.headers"
                    :key="header.id"
                >
                    <FlexRender
                        v-if="!header.isPlaceholder" :render="header.column.columnDef.header"
                        :props="header.getContext()"
                        class="font-bold p-0 text-muted-foreground! hover:text-foreground!"
                    />
                </TableHead>
            </TableRow>
        </TableHeader>
        <TableBody>
            <template v-if="table.getRowModel().rows?.length">
                <TableRow
                    v-for="row in table.getRowModel().rows" :key="row.id"
                    :data-state="row.getIsSelected() ? 'selected' : undefined"
                    class="hover:text-foreground hover:bg-transparent"
                >
                    <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id">
                        <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" class="text-wrap" />
                    </TableCell>
                </TableRow>
            </template>
            <template v-else>
                <TableRow>
                    <TableCell :colspan="columns.length" class="h-24 text-center">
                        No servers.
                    </TableCell>
                </TableRow>
            </template>
        </TableBody>
    </Table>
</template>
