/**
 * Which private-use / symbol code points have an image under public/assets/unicode.
 * Loaded once per page (shared by every UnicodeText instance) and cached in sessionStorage.
 */

import { ref } from 'vue';

const STORAGE_KEY = 'zekbrowser.unicodeFiles';

// Used until the listing API has answered (or when it is unavailable).
const FALLBACK_CODES = [0x2611, 0x2713, 0x2605, 0x2691, 0xe050];

export const availableGlyphs = ref<Set<string>>(new Set(FALLBACK_CODES.map(toHex)));

let loading: Promise<void> | null = null;

export function toHex(codePoint: number): string {
    return codePoint.toString(16).toUpperCase();
}

export function glyphImageUrl(hex: string): string {
    return `/assets/unicode/${hex}.webp`;
}

export function loadAvailableGlyphs(): Promise<void> {
    loading ??= load();

    return loading;
}

async function load(): Promise<void> {
    try {
        const raw = sessionStorage.getItem(STORAGE_KEY);

        if (raw) {
            availableGlyphs.value = new Set((JSON.parse(raw) as string[]).map((s) => s.toUpperCase()));
            return;
        }
    } catch {
        // sessionStorage unavailable; fall through to the network.
    }

    try {
        const response = await fetch('/api/unicode/list');

        if (!response.ok) {
            return;
        }

        const list = (await response.json()) as unknown;

        if (!Array.isArray(list)) {
            return;
        }

        const upper = list.map((s) => String(s).toUpperCase());
        availableGlyphs.value = new Set(upper);

        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify(upper));
        } catch {
            // ignore
        }
    } catch {
        // keep the fallback set
    }
}
