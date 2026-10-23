import type { VNodeChild } from 'vue';

export interface ScoreboardColumn {
    label: string;
    /** Extra class on every cell of the column (used to hide columns on small screens). */
    class?: string;
}

export interface ScoreboardPlayer {
    /** Contents of the name cell. */
    cell: VNodeChild;
    /** One value per ScoreboardColumn. */
    stats: VNodeChild[];
    /** Row background. */
    color: string;
    /** Malformed entry: `cell` spans the whole row. */
    raw?: boolean;
}

export interface ScoreboardGroup {
    team: number | null;
    label?: string;
    /** One value per ScoreboardColumn for the team header row; '' leaves the cell empty. */
    totals: VNodeChild[];
    players: ScoreboardPlayer[];
}

/** Sort groups by score with the "no team" group last. */
export function sortGroups<T extends { team: number | null }>(groups: T[], compare: (a: T, b: T) => number): T[] {
    return groups.sort((a, b) => {
        if (a.team === null && b.team !== null) return 1;
        if (b.team === null && a.team !== null) return -1;

        return compare(a, b);
    });
}

export function groupBy<T>(items: T[], key: (item: T) => number | null): Map<number | null, T[]> {
    const groups = new Map<number | null, T[]>();

    for (const item of items) {
        const k = key(item);
        groups.set(k, [...(groups.get(k) ?? []), item]);
    }

    return groups;
}
