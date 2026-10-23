<script setup lang="ts">
import DataTable from '@/components/server-browser/DataTable.vue';
import { Select } from '@/components/ui/select';
import { isBrowserType, type BrowserType } from '@/lib/api';
import type { LoadedList } from '@/lib/serverList';
import { GAME_OPTIONS, SERVER_LISTS } from '@/server-browser';
import { computed, onMounted, ref, watch } from 'vue';

const props = defineProps<{
    /** Base URL of the JSON API, e.g. "/api/". */
    apiBase: string;
}>();

const emit = defineEmits<{
    (e: 'browser-change', type: BrowserType): void;
}>();

const STORAGE_KEY = 'zekbrowser.serverBrowser';
const EMPTY: LoadedList<unknown> = { rows: [], players: 0, servers: 0 };

const selected = ref<BrowserType>('eldewrito');
const error = ref<string | null>(null);

// Last result per game, so switching back shows the previous rows until the reload lands.
const lists = ref<Record<BrowserType, LoadedList<unknown>>>({ eldewrito: EMPTY, cartographer: EMPTY, haloce: EMPTY, halopc: EMPTY });

const definition = computed(() => SERVER_LISTS[selected.value]);
const list = computed(() => lists.value[selected.value]);
const selectedOption = computed(() => GAME_OPTIONS.find((o) => o.value === selected.value) ?? GAME_OPTIONS[0]);

/** Reload the active list. The parent calls this from the refresh button and the auto-refresh timer. */
async function refresh(): Promise<void> {
    const type = selected.value;
    error.value = null;

    try {
        lists.value[type] = await SERVER_LISTS[type].load(props.apiBase);
    } catch (err) {
        error.value = err instanceof Error ? err.message : String(err);
        console.warn(`Failed to load ${type} servers:`, err);
    }
}

function select(value: string) {
    if (isBrowserType(value)) {
        selected.value = value;
    }
}

onMounted(() => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);

        if (isBrowserType(stored)) {
            selected.value = stored;
        }
    } catch {
        // localStorage unavailable
    }

    emit('browser-change', selected.value);
    void refresh();
});

watch(selected, (value) => {
    try {
        localStorage.setItem(STORAGE_KEY, value);
    } catch {
        // ignore
    }

    emit('browser-change', value);
    void refresh();
});

defineExpose({ refresh, getSelection: () => selected.value });
</script>

<template>
    <div>
        <div v-if="error" class="text-red-500">{{ error }}</div>

        <DataTable :key="selected" :definition="definition" :data="list.rows" :players="list.players" :servers="list.servers">
            <template #left>
                <Select :model-value="selected" class="min-w-[168px]" :options="GAME_OPTIONS" :full-width-trigger="true" @update:model-value="select">
                    <template #trigger-content>
                        <img :src="selectedOption.icon" :alt="selectedOption.label" class="mr-2 h-5 w-5 rounded-full object-contain" />
                    </template>
                </Select>
            </template>
        </DataTable>
    </div>
</template>
