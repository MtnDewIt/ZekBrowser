import HaloPlayersCard from '@/components/server-browser/HaloPlayersCard.vue';
import { fetchJson, listUrl, type ServerListResponse } from '@/lib/api';
import { column, MOBILE_ASIDE_CLASS, mobileCard, type ServerListDefinition } from '@/lib/serverList';
import { h } from 'vue';

/** Halo CE / Halo PC lists come from the GameSpy master server (see server.py). */

type GameSpyInfo = Record<string, string | number | undefined>;

interface HaloServerRaw {
    address?: string;
    ip?: string;
    host?: string;
    port?: number | string;
    info?: GameSpyInfo;
    players?: number;
}

export interface HaloServer {
    address: string;
    port: number | string;
    info: GameSpyInfo;
    players: number;
    maxPlayers: number;
    name: string;
    variant: string;
    gametype: string;
    map: string;
}

const text = (value: unknown) => (value === undefined || value === null ? '' : String(value));

function toHaloServer(s: HaloServerRaw): HaloServer {
    const info = s.info ?? {};

    return {
        address: s.address || s.ip || s.host || '',
        port: s.port || info.port || '',
        info,
        players: Number(info.numplayers ?? s.players ?? 0),
        maxPlayers: Number(info.maxplayers ?? 0),
        name: text(info.hostname || info.server_name),
        variant: text(info.gamevariant || info.game_variant || info.variant),
        gametype: text(info.gametype || info.gametype_name),
        map: text(info.mapname || info.map_name || info.map),
    };
}

const players = (s: HaloServer, cls?: string) => h(HaloPlayersCard, { numPlayers: s.players, maxPlayers: s.maxPlayers, info: s.info, class: cls });

export function gamespyList(type: 'haloce' | 'halopc'): ServerListDefinition<HaloServer> {
    return {
        initialSorting: [{ id: 'players', desc: true }],

        search: [
            { label: 'All', value: 'all' },
            { label: 'Server', value: 'name', text: (s) => [s.name] },
            { label: 'Variant', value: 'variant', text: (s) => [s.variant] },
            { label: 'Gametype', value: 'gametype', text: (s) => [s.gametype] },
            { label: 'Map', value: 'map', text: (s) => [s.map] },
        ],

        columns: [
            column('Server', 'name'),
            column('Map', 'map'),
            column('Gametype', 'gametype', { cell: (s) => (s.gametype.trim().toLowerCase() === 'king' ? 'KOTH' : s.gametype) }),
            column('Variant', 'variant'),
            column('Players', (s) => s.players, { id: 'players', cell: (s) => players(s) }),
            column('IP:Port', (s) => `${s.address}:${s.port}`, {
                id: 'ipport',
                header: { buttonClass: 'text-left' },
                cell: (s) => h('span', { class: 'inline-flex items-center whitespace-nowrap' }, `${s.address}:${s.port}`),
            }),
        ],

        async load(apiBase) {
            const data = await fetchJson<ServerListResponse<HaloServerRaw[]>>(listUrl(apiBase, type), 10000);
            const rows = Array.isArray(data.servers) ? data.servers.map(toHaloServer) : [];

            return {
                rows,
                players: Number(data.count?.players ?? rows.reduce((sum, s) => sum + s.players, 0)),
                servers: Number(data.count?.servers ?? rows.length),
            };
        },

        mobileCard: (s) =>
            mobileCard({
                title: s.name || '—',
                subtitle: [s.map, s.gametype ? h('span', { class: 'ml-1' }, `· ${s.gametype}`) : null],
                aside: players(s, MOBILE_ASIDE_CLASS),
                footer: s.variant ? h('div', { class: 'mt-1.5 text-xs text-muted-foreground' }, s.variant) : null,
            }),
    };
}
