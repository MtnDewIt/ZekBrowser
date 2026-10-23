<script setup lang="ts">
import { useAppearance } from '@/composables/useAppearance';
import { computed } from 'vue';

const { appearance, updateAppearance } = useAppearance();

const isDark = computed(() => appearance.value === 'dark');

function toggleTheme() {
    updateAppearance(isDark.value ? 'light' : 'dark');
}
</script>

<template>
    <button class="theme-toggle" :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'" title="Toggle theme" @click="toggleTheme">
        <div class="toggle-track" :class="{ active: isDark }">
            <div class="toggle-thumb">
                <img v-if="isDark" src="/assets/icons/moon.svg" width="14" height="14" alt="Moon icon" aria-hidden="true" />
                <img v-else src="/assets/icons/sun.svg" width="14" height="14" alt="Sun icon" aria-hidden="true" />
            </div>
        </div>
    </button>
</template>

<style scoped>
/* The toggle keeps its own greys; the dark theme swaps the two track colours and inverts the thumb. */
.theme-toggle {
    --toggle-hover: rgba(0, 0, 0, 0.05);
    --toggle-track: #cbd5e0;
    --toggle-track-active: #4a5568;
    --toggle-thumb: white;
    --toggle-thumb-foreground: #4a5568;
    --toggle-thumb-active: white;
    --toggle-thumb-active-foreground: #4a5568;

    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 9999px;
    transition: background-color 0.2s;
}

:global(.dark) .theme-toggle {
    --toggle-hover: rgba(255, 255, 255, 0.1);
    --toggle-track: #4a5568;
    --toggle-track-active: #cbd5e0;
    --toggle-thumb: #2d3748;
    --toggle-thumb-foreground: #f7fafc;
    --toggle-thumb-active: white;
    --toggle-thumb-active-foreground: #2d3748;
}

.theme-toggle:hover {
    background-color: var(--toggle-hover);
}

.toggle-track {
    width: 48px;
    height: 26px;
    background-color: var(--toggle-track);
    border-radius: 9999px;
    padding: 3px;
    transition: background-color 0.3s;
    position: relative;
}

.toggle-track.active {
    background-color: var(--toggle-track-active);
}

.toggle-thumb {
    width: 20px;
    height: 20px;
    background-color: var(--toggle-thumb);
    color: var(--toggle-thumb-foreground);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s;
}

.active .toggle-thumb {
    transform: translateX(22px);
    background-color: var(--toggle-thumb-active);
    color: var(--toggle-thumb-active-foreground);
}
</style>
