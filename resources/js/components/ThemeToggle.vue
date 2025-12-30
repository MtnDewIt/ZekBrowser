<script setup lang="ts">
import { useAppearance } from '@/composables/useAppearance';
import { computed } from 'vue';

const { appearance, updateAppearance } = useAppearance();

const isDark = computed(() => appearance.value === 'dark');

const toggleTheme = () => {
    const newTheme = isDark.value ? 'light' : 'dark';
    updateAppearance(newTheme);
};
</script>

<template>
    <button
        @click="toggleTheme"
        class="theme-toggle"
        :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
        title="Toggle theme"
    >
        <div class="toggle-track" :class="{ active: isDark }">
            <div class="toggle-thumb">
                <img
                    v-if="isDark"
                    src="/assets/icons/moon.svg"
                    width="14"
                    height="14"
                    alt="Moon icon"
                    aria-hidden="true"
                />
                <img
                    v-else
                    src="/assets/icons/sun.svg"
                    width="14"
                    height="14"
                    alt="Sun icon"
                    aria-hidden="true"
                />
            </div>
        </div>
    </button>
</template>

<style scoped>
.theme-toggle {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 9999px;
    transition: background-color 0.2s;
}

.theme-toggle:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

:global(.dark) .theme-toggle:hover {
    background-color: rgba(255, 255, 255, 0.1);
}

.toggle-track {
    width: 48px;
    height: 26px;
    background-color: #cbd5e0;
    border-radius: 9999px;
    padding: 3px;
    transition: background-color 0.3s;
    position: relative;
}

.toggle-track.active {
    background-color: #4a5568;
}

:global(.dark) .toggle-track {
    background-color: #4a5568;
}

:global(.dark) .toggle-track.active {
    background-color: #cbd5e0;
}

.toggle-thumb {
    width: 20px;
    height: 20px;
    background-color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s;
    color: #4a5568;
}

.active .toggle-thumb {
    transform: translateX(22px);
}

:global(.dark) .toggle-thumb {
    background-color: #2d3748;
    color: #f7fafc;
}

:global(.dark) .active .toggle-thumb {
    background-color: white;
    color: #2d3748;
}
</style>
