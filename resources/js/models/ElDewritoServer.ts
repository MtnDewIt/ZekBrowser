import { ValidationError } from '@/exceptions/ValidationError';

export interface ElDewritoMod {
    id: string;
    mod_name?: string;
    mod_version?: string;
    mod_author?: string;
    mod_website?: string;
    package_url?: string;
    package_size?: number;
    [key: string]: unknown;
}

/** One entry of the /api/ "servers" map, with its "ip:port" key added as `ip`. */
export interface ElDewritoServerData {
    ip: string;
    name: string;
    port: number;
    fileServerPort?: number;
    hostPlayer: string;
    passworded?: boolean;
    sprintState?: '0' | '1' | '2';
    sprintUnlimitedEnabled: '0' | '1';
    assassinationEnabled: '0' | '1';
    voteSystemType?: number;
    teams: boolean;
    teamScores?: number[];
    map: string;
    mapFile: string;
    variant: string;
    variantType: string;
    status: 'InLobby' | 'Loading' | 'InGame';
    numPlayers: number;
    maxPlayers: number;
    modCount?: number;
    modPackageName?: string;
    modPackageAuthor?: string;
    modPackageHash?: string;
    modPackageVersion?: string;
    xnkid?: string;
    xnaddress?: string;
    players?: unknown[];
    isDedicated: boolean;
    gameVersion: string;
    eldewritoVersion: string;
    eldewritoVersionShort: string;
    firstSeenAt: string;
    reverseDns?: string;
    /** Keyed by mod id as served by the game server's /mods endpoint. */
    mods?: Record<string, Omit<ElDewritoMod, 'id'>>;
}

export class ElDewritoServer {
    ip!: string;
    name!: string;
    port!: number;
    fileServerPort?: number;
    hostPlayer!: string;
    passworded?: boolean;
    sprintState?: '0' | '1' | '2';
    sprintUnlimitedEnabled!: '0' | '1';
    assassinationEnabled!: '0' | '1';
    voteSystemType?: number;
    teams!: boolean;
    teamScores?: number[];
    map!: string;
    mapFile!: string;
    variant!: string;
    variantType!: string;
    status!: 'InLobby' | 'Loading' | 'InGame';
    numPlayers!: number;
    maxPlayers!: number;
    modCount?: number;
    modPackageName?: string;
    modPackageAuthor?: string;
    modPackageHash?: string;
    modPackageVersion?: string;
    xnkid?: string;
    xnaddress?: string;
    players?: unknown[];
    isDedicated!: boolean;
    gameVersion!: string;
    eldewritoVersion!: string;
    eldewritoVersionShort!: string;
    firstSeenAt!: string;
    reverseDns?: string;
    mods?: ElDewritoMod[];

    constructor(data: ElDewritoServerData) {
        ElDewritoServer.validate(data);

        const { mods, ...rest } = data;
        Object.assign(this, rest);

        if (mods && typeof mods === 'object') {
            this.mods = Object.entries(mods).map(([id, mod]) => ({ id, ...mod }));
        }
    }

    static validate(data: unknown): asserts data is ElDewritoServerData {
        if (typeof data !== 'object' || data === null) {
            throw new ValidationError('Server validation failed', ['data is not an object']);
        }

        const d = data as Record<string, unknown>;
        const optional = (key: string, check: (v: unknown) => boolean) => d[key] === undefined || check(d[key]);
        const isString = (v: unknown) => typeof v === 'string';
        const isNumber = (v: unknown) => typeof v === 'number';
        const isBoolean = (v: unknown) => typeof v === 'boolean';
        const oneOf = (values: unknown[]) => (v: unknown) => values.includes(v);

        const rules: [string, boolean][] = [
            ['ip', isString(d.ip)],
            ['name', isString(d.name)],
            ['port', isNumber(d.port)],
            ['fileServerPort', optional('fileServerPort', isNumber)],
            ['hostPlayer', isString(d.hostPlayer)],
            ['passworded', optional('passworded', isBoolean)],
            ['sprintState', optional('sprintState', oneOf(['0', '1', '2']))],
            ['sprintUnlimitedEnabled', oneOf(['0', '1'])(d.sprintUnlimitedEnabled)],
            ['assassinationEnabled', oneOf(['0', '1'])(d.assassinationEnabled)],
            ['voteSystemType', optional('voteSystemType', isNumber)],
            ['teams', isBoolean(d.teams)],
            ['teamScores', optional('teamScores', Array.isArray)],
            ['map', isString(d.map)],
            ['mapFile', isString(d.mapFile)],
            ['variant', isString(d.variant)],
            ['variantType', isString(d.variantType)],
            ['status', oneOf(['InLobby', 'Loading', 'InGame'])(d.status)],
            ['numPlayers', isNumber(d.numPlayers)],
            ['maxPlayers', isNumber(d.maxPlayers)],
            ['modCount', optional('modCount', isNumber)],
            ['modPackageName', optional('modPackageName', isString)],
            ['modPackageAuthor', optional('modPackageAuthor', isString)],
            ['modPackageHash', optional('modPackageHash', isString)],
            ['modPackageVersion', optional('modPackageVersion', isString)],
            ['xnkid', optional('xnkid', isString)],
            ['xnaddress', optional('xnaddress', isString)],
            ['players', optional('players', Array.isArray)],
            ['isDedicated', isBoolean(d.isDedicated)],
            ['gameVersion', isString(d.gameVersion)],
            ['eldewritoVersion', isString(d.eldewritoVersion)],
            ['eldewritoVersionShort', isString(d.eldewritoVersionShort)],
            ['firstSeenAt', isString(d.firstSeenAt)],
            ['reverseDns', optional('reverseDns', isString)],
            ['mods', optional('mods', (v) => typeof v === 'object')],
        ];

        const errors = rules.filter(([, passed]) => !passed).map(([field]) => `${field} "${d[field]}" is invalid`);

        if (errors.length > 0) {
            throw new ValidationError('Server validation failed', errors);
        }
    }

    statusFormatted(): string {
        if (this.numPlayers <= 0) {
            return 'Waiting for players...';
        }

        if (this.status === 'InLobby') {
            return 'In lobby';
        }

        return `Playing ${this.variant} on ${this.map || this.mapFile}`;
    }

    versionWithoutTrailingZero(): string {
        return this.eldewritoVersionShort.endsWith('.0') ? this.eldewritoVersionShort.slice(0, -2) : this.eldewritoVersionShort;
    }
}
