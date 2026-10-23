import type { BrowserType } from '@/lib/api';
import type { ServerListDefinition } from '@/lib/serverList';
import { cartographerList } from './cartographer';
import { eldewritoList } from './eldewrito';
import { gamespyList } from './gamespy';

export interface GameOption {
    label: string;
    value: BrowserType;
    icon: string;
    iconRounded: boolean;
}

export const GAME_OPTIONS: GameOption[] = [
    { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.webp', iconRounded: true },
    { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.webp', iconRounded: true },
    { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.webp', iconRounded: true },
    { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.webp', iconRounded: true },
];

export const SERVER_LISTS: Record<BrowserType, ServerListDefinition<any>> = {
    eldewrito: eldewritoList,
    cartographer: cartographerList,
    haloce: gamespyList('haloce'),
    halopc: gamespyList('halopc'),
};
