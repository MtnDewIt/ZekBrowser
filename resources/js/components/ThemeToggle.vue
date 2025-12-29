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
                <svg
                    v-if="isDark"
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                </svg>
                <svg
                    v-else
                    xmlns="http://www.w3.org/2000/svg"
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                >
                    <circle cx="12" cy="12" r="5"></circle>
                    <line x1="12" y1="1" x2="12" y2="3"></line>
                    <line x1="12" y1="21" x2="12" y2="23"></line>
                    <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                    <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                    <line x1="1" y1="12" x2="3" y2="12"></line>
                    <line x1="21" y1="12" x2="23" y2="12"></line>
                    <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                    <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                </svg>
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
