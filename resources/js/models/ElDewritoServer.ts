import { ValidationError } from '@/exceptions/ValidationError';

export class ElDewritoServer {
    ip: string;
    name: string;
    port: number;
    fileServerPort?: number;
    hostPlayer: string;
    sprintState?: '0' | '1' | '2';
    sprintUnlimitedEnabled: '0' | '1';
    assassinationEnabled: '0' | '1';
    voteSystemType?: number;
    teams: boolean;
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
    players?: array;
    isDedicated: boolean;
    gameVersion: string;
    eldewritoVersion: string;
    mods?: array;

    eldewritoVersionShort: string;
    firstSeenAt: string;
    reverseDns?: string;

    constructor(data: {
        ip: string;
        name: string;
        port: number;
        fileServerPort?: number;
        hostPlayer: string;
        sprintState?: '0' | '1' | '2';
        sprintUnlimitedEnabled: '0' | '1';
        assassinationEnabled: '0' | '1';
        voteSystemType?: number;
        teams: boolean;
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
        players?: any[];
        isDedicated: boolean;
        gameVersion: string;
        eldewritoVersion: string;
        eldewritoVersionShort: string;
        firstSeenAt: string;
        reverseDns?: string;
        mods?: object;
    }) {
        ElDewritoServer.validate(data);
        Object.assign(this, data);

        if (typeof data.mods === 'object') {
            this.mods = [];

            Object.entries(data.mods).forEach(([id, data]) => {
                this.mods.push({
                    id: id,
                    ...data,
                });
            });
        }
    }

    static validate(data: any): void {
        const errors: string[] = [];

        if (typeof data !== 'object' || data === null) {
            errors.push('data is not an object');
            throw new ValidationError('Server validation failed', errors);
        }

        const rules: [string, boolean][] = [
            ['ip', typeof data.ip === 'string'],
            ['name', typeof data.name === 'string'],
            ['port', typeof data.port === 'number'],
            ['fileServerPort', typeof data.fileServerPort === 'undefined' || typeof data.fileServerPort === 'number'],
            ['hostPlayer', typeof data.hostPlayer === 'string'],
            ['sprintState', typeof data.sprintState === 'undefined' || ['0', '1', '2'].includes(data.sprintState)],
            ['sprintUnlimitedEnabled', ['0', '1'].includes(data.sprintUnlimitedEnabled)],
            ['assassinationEnabled', ['0', '1'].includes(data.assassinationEnabled)],
            ['voteSystemType', typeof data.voteSystemType === 'undefined' || typeof data.voteSystemType === 'number'],
            ['teams', typeof data.teams === 'boolean'],
            ['map', typeof data.map === 'string'],
            ['mapFile', typeof data.mapFile === 'string'],
            ['variant', typeof data.variant === 'string'],
            ['variantType', typeof data.variantType === 'string'],
            ['status', ['InLobby', 'Loading', 'InGame'].includes(data.status)],
            ['numPlayers', typeof data.numPlayers === 'number'],
            ['maxPlayers', typeof data.maxPlayers === 'number'],
            ['modCount', typeof data.modCount === 'undefined' || typeof data.modCount === 'number'],
            ['modPackageName', typeof data.modPackageName === 'undefined' || typeof data.modPackageName === 'string'],
            ['modPackageAuthor', typeof data.modPackageAuthor === 'undefined' || typeof data.modPackageAuthor === 'string'],
            ['modPackageHash', typeof data.modPackageHash === 'undefined' || typeof data.modPackageHash === 'string'],
            ['modPackageVersion', typeof data.modPackageVersion === 'undefined' || typeof data.modPackageVersion === 'string'],
            ['xnkid', typeof data.xnkid === 'undefined' || typeof data.xnkid === 'string'],
            ['xnaddress', typeof data.xnaddress === 'undefined' || typeof data.xnaddress === 'string'],
            ['players', typeof data.players === 'undefined' || Array.isArray(data.players)],
            ['isDedicated', typeof data.isDedicated === 'boolean'],
            ['gameVersion', typeof data.gameVersion === 'string'],
            ['eldewritoVersion', typeof data.eldewritoVersion === 'string'],
            ['eldewritoVersionShort', typeof data.eldewritoVersionShort === 'string'],
            ['firstSeenAt', typeof data.firstSeenAt === 'string'],
            ['reverseDns', typeof data.reverseDns === 'undefined' || typeof data.reverseDns === 'string'],
            ['mods', typeof data.mods === 'undefined' || typeof data.mods === 'object'],
        ];

        for (const [field, passed] of rules) {
            if (!passed) {
                errors.push(`${field} "${data[field]}" is invalid`);
            }
        }

        if (errors.length > 0) {
            throw new ValidationError('Server validation failed', errors);
        }
    }

    statusFormatted(): string {
        if (this.numPlayers > 0) {
            if (this.status === 'InLobby') {
                return 'In lobby';
            } else {
                return `Playing ${this.variant} on ${this.map}`;
            }
        } else {
            return 'Waiting for players...';
        }
    }

    versionWithoutTrailingZero(): string {
        if (this.eldewritoVersionShort.endsWith('.0')) {
            return this.eldewritoVersionShort.slice(0, -2);
        }

        return this.eldewritoVersionShort;
    }
}
