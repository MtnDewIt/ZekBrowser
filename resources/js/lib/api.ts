/**
 * Typed access to the ZekBrowser JSON API (the Laravel routes under /api/).
 */

export type BrowserType = 'eldewrito' | 'cartographer' | 'haloce' | 'halopc';

export const BROWSER_TYPES: readonly BrowserType[] = ['eldewrito', 'cartographer', 'haloce', 'halopc'];

export function isBrowserType(value: unknown): value is BrowserType {
    return typeof value === 'string' && (BROWSER_TYPES as readonly string[]).includes(value);
}

export interface CountSummary {
    players: number;
    servers: number;
}

export interface ServerListResponse<TServers> {
    count?: CountSummary;
    updatedAt?: string;
    servers: TServers;
}

export type SeriesPoint = [number, number];

export interface StatsSeries {
    players: SeriesPoint[];
    servers: SeriesPoint[];
}

const LIST_PATHS: Record<BrowserType, string> = {
    eldewrito: '',
    cartographer: 'cartographer/list',
    haloce: 'haloce/list',
    halopc: 'halopc/list',
};

const STATS_PATHS: Record<BrowserType, string> = {
    eldewrito: 'stats',
    cartographer: 'cartographer/stats',
    haloce: 'haloce/stats',
    halopc: 'halopc/stats',
};

export function listUrl(apiBase: string, type: BrowserType): string {
    return apiBase + LIST_PATHS[type];
}

export function statsUrl(apiBase: string, type: BrowserType): string {
    return apiBase + STATS_PATHS[type];
}

/**
 * fetch() + JSON parse with a timeout. Non-2xx responses reject.
 */
export async function fetchJson<T>(url: string, timeoutMs = 15000): Promise<T> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, { signal: controller.signal });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`.trim());
        }

        return (await response.json()) as T;
    } finally {
        clearTimeout(timer);
    }
}

export function sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
