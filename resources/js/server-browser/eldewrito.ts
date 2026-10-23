import ModsCard from '@/components/server-browser/ModsCard.vue';
import PlayersCard from '@/components/server-browser/PlayersCard.vue';
import { ValidationError } from '@/exceptions/ValidationError';
import { fetchJson, listUrl, type ServerListResponse } from '@/lib/api';
import { column, iconHeader, MOBILE_ASIDE_CLASS, mobileCard, type ServerListDefinition } from '@/lib/serverList';
import { ElDewritoServer, type ElDewritoServerData } from '@/models/ElDewritoServer';
import { h } from 'vue';

type Response = ServerListResponse<Record<string, Omit<ElDewritoServerData, 'ip'>>>;

function players(s: ElDewritoServer, cls?: string) {
    return h(PlayersCard, {
        numPlayers: s.numPlayers,
        maxPlayers: s.maxPlayers,
        players: s.players,
        teams: s.teams,
        teamScores: s.teamScores,
        serverVersion: s.eldewritoVersionShort ?? s.eldewritoVersion ?? '',
        passworded: !!s.passworded,
        class: cls,
    });
}

function mods(s: ElDewritoServer) {
    return s.mods?.length ? h(ModsCard, { mods: s.mods, jsonUrl: `http://${s.ip}/mods`, showAsNumber: true }) : 0;
}

export const eldewritoList: ServerListDefinition<ElDewritoServer> = {
    initialSorting: [{ id: 'numPlayers', desc: true }],

    search: [
        { label: 'All', value: 'all' },
        { label: 'Server', value: 'name', text: (s) => [s.name] },
        { label: 'Host', value: 'host', text: (s) => [s.hostPlayer] },
        { label: 'Mods', value: 'mods', text: (s) => (s.mods ?? []).map((m) => m.mod_name) },
    ],
    searchAll: (s) => [s.map, s.variant],

    columns: [
        column(iconHeader('icon-lock', 'h-5 w-5'), (s) => (s.passworded ? 1 : 0), {
            id: 'passworded',
            header: { title: 'Sort by password protection', paddingRight: '0.5rem' },
            cell: (s) =>
                s.passworded
                    ? h('span', {
                          class: 'icon-mask icon-lock block h-5 w-5 leading-none text-muted-foreground',
                          ariaHidden: 'true',
                          title: 'Password protected',
                      })
                    : h('span', { class: 'block h-5 w-5' }),
        }),
        column('Server', 'name', { cell: (s) => h('div', { class: 'md:whitespace-nowrap' }, h('span', { class: 'font-bold!' }, s.name)) }),
        column('Host', 'hostPlayer'),
        column('Status', (s) => s.statusFormatted(), { id: 'status' }),
        column('Mods', (s) => s.mods?.length ?? 0, { id: 'mods', cell: mods }),
        column('Players', 'numPlayers', { cell: (s) => players(s) }),
        column('Version', 'eldewritoVersion', { cell: (s) => s.versionWithoutTrailingZero() }),
        column('IP', 'ip', {
            header: { buttonClass: 'text-left' },
            cell: (s) =>
                h('span', { class: 'inline-flex items-center whitespace-nowrap' }, [
                    h('a', { href: `eldewrito://${s.ip}`, target: '_blank', title: `Click to join ${s.name}` }, s.ip),
                    h(
                        'a',
                        { href: `http://${s.ip}`, target: '_blank', title: 'View JSON info', class: 'ml-1 inline-flex items-center' },
                        h('span', { class: 'icon-mask icon-external inline-block h-4 w-4 align-middle opacity-80', ariaHidden: 'true' }),
                    ),
                ]),
        }),
    ],

    async load(apiBase) {
        const data = await fetchJson<Response>(listUrl(apiBase, 'eldewrito'));
        const rows: ElDewritoServer[] = [];

        for (const [ip, server] of Object.entries(data.servers ?? {})) {
            try {
                rows.push(new ElDewritoServer({ ip, ...server }));
            } catch (error) {
                if (error instanceof ValidationError) {
                    console.warn(`Validation failed for ${ip}:`, error.errors);
                } else {
                    console.error(`Unexpected error for server ${ip}:`, error);
                }
            }
        }

        return { rows, players: rows.reduce((sum, s) => sum + (Number(s.numPlayers) || 0), 0), servers: rows.length };
    },

    mobileCard: (s) =>
        mobileCard({
            lock: !!s.passworded,
            title: s.name,
            subtitle: [s.statusFormatted(), s.hostPlayer ? h('span', { class: 'ml-1' }, `· ${s.hostPlayer}`) : null],
            aside: players(s, MOBILE_ASIDE_CLASS),
            footer: h('div', { class: 'mt-1.5 flex items-center gap-2 text-xs text-muted-foreground' }, [
                s.eldewritoVersion ? h('span', `v${s.versionWithoutTrailingZero()}`) : null,
                s.mods?.length
                    ? h(
                          'span',
                          {
                              class: 'inline-flex cursor-pointer items-center',
                              onClick: (e: MouseEvent) => {
                                  e.stopPropagation();
                                  (e.currentTarget as HTMLElement).querySelector<HTMLElement>('.mods-count-button')?.click();
                              },
                          },
                          ['Mods: ', mods(s)],
                      )
                    : null,
            ]),
        }),
};
