/**
 * A server list is described by one object per game: how to load it, its columns,
 * what the search box looks at, and how a row renders as a mobile card.
 * ServerBrowser.vue + DataTable.vue render any of them.
 */

import { makeSortHeader } from '@/lib/tableHeaders';
import type { ColumnDef, SortingState } from '@tanstack/vue-table';
import { Fragment, h, type VNode, type VNodeChild } from 'vue';

export interface SearchOption<T> {
    label: string;
    value: string;
    /** Strings this mode matches against. Omitted for "All", which is the union of the others. */
    text?: (row: T) => unknown[];
}

export interface LoadedList<T> {
    rows: T[];
    players: number;
    servers: number;
}

export interface ServerListDefinition<T> {
    columns: ColumnDef<T, unknown>[];
    search: SearchOption<T>[];
    /** Extra fields the "All" mode also matches. */
    searchAll?: (row: T) => unknown[];
    initialSorting: SortingState;
    load(apiBase: string): Promise<LoadedList<T>>;
    mobileCard(row: T): VNode;
}

export function searchText<T>(definition: ServerListDefinition<T>, row: T, mode: string): unknown[] {
    const options = definition.search.filter((o) => o.text && (mode === 'all' || o.value === mode));
    const extra = mode === 'all' && definition.searchAll ? definition.searchAll(row) : [];

    return [...options.flatMap((o) => o.text!(row)), ...extra];
}

interface ColumnOptions<T> {
    id?: string;
    cell?: (row: T) => VNodeChild;
    header?: Parameters<typeof makeSortHeader>[1];
}

/** Sortable column: `accessor` is a row key or a function; `cell` defaults to the accessor value. */
export function column<T>(
    label: string | VNode,
    accessor: (keyof T & string) | ((row: T) => unknown),
    options: ColumnOptions<T> = {},
): ColumnDef<T, unknown> {
    const def: ColumnDef<T, unknown> =
        typeof accessor === 'string'
            ? { accessorKey: accessor }
            : { id: options.id ?? (typeof label === 'string' ? label.toLowerCase() : 'column'), accessorFn: accessor };

    def.header = makeSortHeader<T>(label, options.header);

    if (options.cell) {
        const cell = options.cell;
        def.cell = ({ row }) => cell(row.original);
    }

    return def;
}

export function iconHeader(icon: string, extra = ''): VNode {
    return h('span', { class: `icon-mask ${icon} leading-none text-muted-foreground ${extra}`.trim(), ariaHidden: 'true' });
}

interface MobileCardParts {
    title: VNodeChild;
    lock?: boolean;
    subtitle?: VNodeChild;
    /** Right-hand side, usually the player count. */
    aside?: VNodeChild;
    /** Optional second line, already wrapped in its own element. */
    footer?: VNodeChild;
}

/** The shared mobile card layout: title row with the count on the right, then an optional footer line. */
export function mobileCard(parts: MobileCardParts): VNode {
    return h(Fragment, [
        h('div', { class: 'flex items-start justify-between gap-2' }, [
            h('div', { class: 'min-w-0 flex-1' }, [
                h('div', { class: 'flex items-center gap-1.5' }, [
                    parts.lock ? h('span', { class: 'icon-mask icon-lock h-3.5 w-3.5 flex-shrink-0 text-muted-foreground' }) : null,
                    h('span', { class: 'truncate text-sm font-bold text-foreground' }, [parts.title]),
                ]),
                h('div', { class: 'mt-0.5 text-xs text-muted-foreground' }, [parts.subtitle]),
            ]),
            parts.aside,
        ]),
        parts.footer ?? null,
    ]);
}

export const MOBILE_ASIDE_CLASS = 'flex-shrink-0 text-sm font-semibold tabular-nums text-foreground';
