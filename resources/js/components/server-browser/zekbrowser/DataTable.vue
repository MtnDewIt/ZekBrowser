<script setup lang="ts" generic="TData, TValue">
import type {
    ColumnDef,
    SortingState,
} from '@tanstack/vue-table';
import {
    FlexRender,
    getCoreRowModel,
    getFilteredRowModel,
    getSortedRowModel,
    useVueTable,
} from '@tanstack/vue-table';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { valueUpdater } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { ref } from 'vue';

const props = defineProps<{
    columns: ColumnDef<TData, TValue>[]
    data: TData[]
}>();

const sorting = ref<SortingState>([
    { id: 'numPlayers', desc: true } // Sort by number of players descending by default
]);

const columnFilters = ref<ColumnFiltersState>([])

const table = useVueTable({
    get data() { return props.data },
    get columns() { return props.columns },
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: updaterOrValue => valueUpdater(updaterOrValue, sorting),
    onColumnFiltersChange: updaterOrValue => valueUpdater(updaterOrValue, columnFilters),
    getFilteredRowModel: getFilteredRowModel(),
    state: {
        get sorting() { return sorting.value },
        get columnFilters() { return columnFilters.value },
    },
});
</script>

<template>

    <!--<div class="flex items-center py-4">
        <Input class="max-w-sm rounded-none" placeholder="Filter servers..."
               :model-value="table.getColumn('name')?.getFilterValue() as string"
               @update:model-value=" table.getColumn('name')?.setFilterValue($event)" />
    </div>-->

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
