<script setup lang="ts">
import { useAppearance } from '@/composables/useAppearance';
import { availableGlyphs, glyphImageUrl, loadAvailableGlyphs, toHex } from '@/lib/unicodeGlyphs';
import { computed, onMounted } from 'vue';

const props = defineProps<{ text?: string; stripUnicode?: boolean }>();

// Glyph images are drawn for the dark theme; these are inverted when the light theme is active.
const INVERT_IN_LIGHT_THEME = new Set([
    0x2605, 0x2639, 0x263b, 0x2691, 0x2713, 0x2717, 0xe000, 0xe001, 0xe002, 0xe004, 0xe005, 0xe006, 0xe007, 0xe008, 0xe065, 0xe066, 0xe067, 0xe068,
    0xe069, 0xe070, 0xe071, 0xe072, 0xe073, 0xe074, 0xe075, 0xe076, 0xe077, 0xe078, 0xe079, 0xe080, 0xe081, 0xe082, 0xe083, 0xe084, 0xe085, 0xe086,
    0xe087, 0xe088, 0xe089, 0xe090, 0xe091, 0xe092, 0xe093, 0xe094, 0xe095, 0xe096, 0xe097, 0xe098, 0xe099, 0xe10a, 0xe10b, 0xe10c, 0xe10d, 0xe10e,
    0xe10f, 0xe110, 0xe111, 0xe112, 0xe113, 0xe114, 0xe115, 0xe116, 0xe117, 0xe118, 0xe119, 0xe11a, 0xe11b, 0xe11c, 0xe11d, 0xe11e, 0xe11f, 0xe120,
    0xe121, 0xe122, 0xe123, 0xe124, 0xe125, 0xe126, 0xe127, 0xe128, 0xe129, 0xe12a, 0xe12b, 0xe12c, 0xe12d, 0xe12e, 0xe12f, 0xe130, 0xe131,
]);

const { appearance } = useAppearance();
const isDark = computed(() => appearance.value === 'dark');

type Part = string | { src: string; alt: string; invert: boolean };

const parts = computed<Part[]>(() => {
    let chars = Array.from(props.text ?? '');

    if (props.stripUnicode) {
        chars = chars.filter((ch) => (ch.codePointAt(0) ?? 0) <= 127);
    }

    return chars.map((ch) => {
        const cp = ch.codePointAt(0) ?? 0;
        const hex = toHex(cp);

        if (!availableGlyphs.value.has(hex)) {
            return ch;
        }

        return { src: glyphImageUrl(hex), alt: `U+${hex}`, invert: !isDark.value && INVERT_IN_LIGHT_THEME.has(cp) };
    });
});

onMounted(() => void loadAvailableGlyphs());
</script>

<template>
    <span class="unicode-text inline-flex items-center">
        <template v-for="(p, idx) in parts" :key="idx">
            <img
                v-if="typeof p !== 'string'"
                :src="p.src"
                :alt="p.alt"
                class="mx-[2px] inline-block h-4 w-4 align-middle"
                :class="{ invert: p.invert }"
            />
            <span v-else>{{ p }}</span>
        </template>
    </span>
</template>

<style scoped>
.unicode-text img {
    display: inline-block;
}
.unicode-text img.invert {
    filter: invert(1) hue-rotate(180deg);
}
</style>
