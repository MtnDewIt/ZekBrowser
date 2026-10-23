import { Button } from '@/components/ui/button';
import type { Column } from '@tanstack/vue-table';
import { h, type VNode } from 'vue';

const SORT_ICON_BASE = 'icon-mask inline-block w-3.5 h-3.5 ml-2 align-middle opacity-70';

export function renderSortIcon(state: false | 'asc' | 'desc'): VNode {
    const variant = state === 'asc' ? 'icon-sort-up' : state === 'desc' ? 'icon-sort-down' : 'icon-sort';

    return h('span', { class: `${SORT_ICON_BASE} ${variant}`, ariaHidden: 'true' });
}

interface SortHeaderOptions {
    /** Extra classes for the header button. */
    buttonClass?: string;
    /** Tooltip for icon-only headers. */
    title?: string;
    /** Right padding; icon-only headers use less. */
    paddingRight?: string;
}

/**
 * Column header renderer: a ghost button that toggles sorting and shows the sort state.
 * `label` can be text or a VNode (for icon headers).
 */
export function makeSortHeader<TData>(label: string | VNode, options: SortHeaderOptions = {}) {
    const { buttonClass = '', title, paddingRight = '1.25rem' } = options;

    return ({ column }: { column: Column<TData, unknown> }) =>
        h(
            Button,
            {
                variant: 'ghost',
                class: ['gap-1', buttonClass].filter(Boolean).join(' '),
                style: `padding-left: 0.5rem; padding-right: ${paddingRight}; margin-left: -0.5rem;`,
                onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
                title,
            },
            () => [label, renderSortIcon(column.getIsSorted())],
        );
}
