import UnicodeText from '@/components/UnicodeText.vue';
import { fetchJson, listUrl, type ServerListResponse } from '@/lib/api';
import { column, iconHeader, MOBILE_ASIDE_CLASS, mobileCard, type ServerListDefinition } from '@/lib/serverList';
import { h } from 'vue';

interface Players {
    filled?: number | null;
    max?: number | null;
}

interface CartoServerRaw {
    xuid?: string | number;
    server_name?: string;
    map_name?: string;
    map_id?: number | string | null;
    gametype?: string;
    variant?: string;
    players?: Players | number;
    description?: string;
}

export interface CartoServer {
    xuid?: string | number;
    server_name: string;
    map_name: string;
    map_id?: number | string | null;
    gametype: string;
    variant: string;
    players: Players;
    description: string;
}

// Stock Halo 2 map ids (mirrors MAP_ID_TO_INFO in server.py); anything else is a custom map.
const KNOWN_MAP_IDS = new Set([
    1, 101, 105, 301, 305, 401, 405, 501, 505, 601, 605, 701, 801, 705, 805, 80, 1201, 100, 60, 110, 70, 1300, 10, 1302, 1400, 3001, 1200, 1001, 120,
    1002, 800, 1402, 50, 20, 444678, 91101, 1101, 1000, 1109, 40, 30,
]);

function isCustomMap(s: CartoServer): boolean {
    const id = s.map_id;

    return id === null || id === undefined || String(id).trim() === '' || !KNOWN_MAP_IDS.has(Number(id));
}

const filled = (s: CartoServer) => Number(s.players.filled ?? 0);
const count = (s: CartoServer) => `${s.players.filled ?? '?'}/${s.players.max ?? '?'}`;
const unicode = (text: string, stripUnicode = false) => h(UnicodeText, { text, stripUnicode });

function toCartoServer(item: CartoServerRaw): CartoServer {
    return {
        xuid: item.xuid,
        server_name: item.server_name || '',
        map_id: item.map_id,
        map_name: item.map_name || '',
        variant: item.variant || '',
        gametype: item.gametype || '',
        players: item.players && typeof item.players === 'object' ? item.players : {},
        description: item.description || '',
    };
}

export const cartographerList: ServerListDefinition<CartoServer> = {
    initialSorting: [{ id: 'players', desc: true }],

    search: [
        { label: 'All', value: 'all' },
        { label: 'Server', value: 'server', text: (s) => [s.server_name] },
        { label: 'Map', value: 'map', text: (s) => [s.map_name] },
        { label: 'Gametype', value: 'gametype', text: (s) => [s.gametype] },
        { label: 'Variant', value: 'variant', text: (s) => [s.variant] },
        { label: 'Description', value: 'description', text: (s) => [s.description] },
    ],

    columns: [
        column('Server', 'server_name', {
            cell: (s) => h('div', { class: 'md:whitespace-nowrap' }, h('span', { class: 'font-bold!' }, unicode(s.server_name))),
        }),
        column('Map', 'map_name', { cell: (s) => unicode(s.map_name) }),
        column(
            h('span', { class: 'inline-flex items-center' }, iconHeader('icon-download-b', 'relative top-[2px] inline-block h-4 w-4')),
            (s) => (isCustomMap(s) ? 1 : 0),
            {
                id: 'custom_map',
                header: { title: 'Custom Map', buttonClass: 'gap-0' },
                cell: (s) =>
                    isCustomMap(s)
                        ? h('span', { class: 'icon-mask icon-download-b block h-4 w-4 leading-none text-muted-foreground', title: 'Custom Map' })
                        : h('span', { class: 'block h-4 w-4' }),
            },
        ),
        column('Gametype', 'gametype', { cell: (s) => unicode(s.gametype) }),
        column('Variant', 'variant', { cell: (s) => unicode(s.variant) }),
        column('Players', filled, { id: 'players', cell: count }),
        column('Description', 'description', { cell: (s) => unicode(s.description || '—', true) }),
    ],

    async load(apiBase) {
        const data = await fetchJson<ServerListResponse<CartoServerRaw[]> | CartoServerRaw[]>(listUrl(apiBase, 'cartographer'));
        const rows = (Array.isArray(data) ? data : Array.isArray(data.servers) ? data.servers : []).map(toCartoServer);

        return { rows, players: rows.reduce((sum, s) => sum + filled(s), 0), servers: rows.length };
    },

    mobileCard: (s) =>
        mobileCard({
            title: unicode(s.server_name || '—'),
            subtitle: [unicode(s.map_name), s.gametype ? h('span', { class: 'ml-1' }, ['· ', unicode(s.gametype)]) : null],
            aside: h('span', { class: MOBILE_ASIDE_CLASS }, count(s)),
            footer:
                s.variant || s.description
                    ? h('div', { class: 'mt-1.5 truncate text-xs text-muted-foreground' }, [
                          s.variant ? unicode(s.variant) : null,
                          s.variant && s.description ? h('span', ' · ') : null,
                          s.description ? unicode(s.description, true) : null,
                      ])
                    : null,
        }),
};
