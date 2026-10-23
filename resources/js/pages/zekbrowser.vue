<script setup lang="ts">
import ServerBrowser from '@/components/server-browser/ServerBrowser.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import { fetchJson, sleep, statsUrl, type BrowserType, type StatsSeries } from '@/lib/api';
import { Head } from '@inertiajs/vue3';
import type { Options } from 'highcharts';
import { Chart } from 'highcharts-vue';
import 'highcharts/css/highcharts.css';
// Stock module only for dataGrouping: the history has tens of thousands of
// points, grouping renders a few hundred and regroups on zoom.
import 'highcharts/modules/stock';
import { onMounted, onUnmounted, ref } from 'vue';

const props = defineProps<{
    /** Base URL of the JSON API, e.g. "/api/". */
    zekBrowserApi: string;
}>();

const REFRESH_INTERVAL_MS = 30_000;
const MIN_SPIN_MS = 600;

const activeBrowser = ref<BrowserType>('eldewrito');
const serverBrowser = ref<InstanceType<typeof ServerBrowser> | null>(null);
const isRefreshing = ref(false);

const statsStatus = ref('Loading...');
const chartOptions = ref<Options>({
    accessibility: { enabled: false },
    chart: { styledMode: true, zooming: { type: 'x' }, animation: false },
    credits: { enabled: false },
    title: { text: undefined },
    xAxis: { type: 'datetime' },
    yAxis: { title: { text: undefined } },
    legend: { enabled: false },
    tooltip: { valueDecimals: 0 },
    plotOptions: {
        series: {
            animation: false,
            turboThreshold: 0,
            marker: { enabled: false },
            states: { hover: { lineWidthPlus: 0 } },
            dataGrouping: { enabled: true, approximation: 'average', groupPixelWidth: 3 },
        },
    },
});

/** Identity of the series currently drawn, so an unchanged poll does not redraw 20k+ points. */
let drawnStats = '';

function statsKey(game: BrowserType, data: StatsSeries): string {
    const last = (s: [number, number][]) => (s.length ? `${s.length}:${s[s.length - 1][0]}:${s[s.length - 1][1]}` : '0');

    return `${game}|${last(data.players)}|${last(data.servers)}`;
}

async function fetchStats(): Promise<void> {
    const game = activeBrowser.value;

    try {
        const data = await fetchJson<StatsSeries>(statsUrl(props.zekBrowserApi, game));
        const key = statsKey(game, data);

        if (key !== drawnStats) {
            drawnStats = key;
            chartOptions.value = {
                ...chartOptions.value,
                series: [
                    { type: 'line', name: 'Players', data: data.players },
                    { type: 'line', name: 'Servers', data: data.servers },
                ],
            };
        }

        statsStatus.value = '';
    } catch (error) {
        statsStatus.value = 'Whoops, something bad happened.';
        console.error(error);
    }
}

/** Reload the active server list and its stats. The spinner shows for at least MIN_SPIN_MS. */
async function refresh(): Promise<void> {
    if (isRefreshing.value) {
        return;
    }

    isRefreshing.value = true;

    try {
        await Promise.all([serverBrowser.value?.refresh(), sleep(MIN_SPIN_MS)]);
    } catch (error) {
        console.warn('Refresh failed:', error);
    }

    await fetchStats();
    isRefreshing.value = false;
}

// The child emits this on mount (with the remembered selection) and on every change.
function onBrowserChange(type: BrowserType) {
    activeBrowser.value = type;
    void fetchStats();
}

let refreshTimer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
    refreshTimer = setInterval(() => void refresh(), REFRESH_INTERVAL_MS);
});

onUnmounted(() => {
    if (refreshTimer !== null) {
        clearInterval(refreshTimer);
    }
});
</script>

<template>
    <Head title="ZekBrowser">
        <meta
            name="description"
            content="Find and join halo servers with the server browser. Play unique maps, game modes, and mods from the community."
        />
    </Head>

    <section class="px-4 py-6 sm:px-6 lg:px-8">
        <div class="mx-auto flex flex-col items-center">
            <div class="flex w-full max-w-[1800px] flex-col">
                <div class="mb-6 flex items-center justify-between">
                    <div class="flex flex-col">
                        <h1 class="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">ZekBrowser</h1>
                    </div>
                    <div class="relative z-30 flex items-center gap-2">
                        <button
                            class="refresh-button"
                            :title="isRefreshing ? 'Refreshing...' : 'Refresh server list'"
                            :aria-label="isRefreshing ? 'Refreshing...' : 'Refresh server list'"
                            @click="refresh"
                        >
                            <span class="icon-mask icon-refresh" :class="{ 'animate-spin': isRefreshing }" aria-hidden="true"></span>
                        </button>
                        <ThemeToggle />
                    </div>
                </div>

                <ServerBrowser ref="serverBrowser" :api-base="zekBrowserApi" @browser-change="onBrowserChange" />

                <div class="mt-8 mb-4 flex items-center justify-between">
                    <h2 class="text-xl font-semibold tracking-tight text-foreground">Stats</h2>
                    <p v-if="statsStatus" class="text-sm text-muted-foreground">{{ statsStatus }}</p>
                </div>

                <div v-if="chartOptions.series" class="rounded-xl border border-border/60 bg-card p-4 shadow-sm">
                    <Chart :options="chartOptions"></Chart>
                </div>
            </div>
        </div>
    </section>
</template>

<style scoped>
.refresh-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 6px;
    border-radius: 8px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
    height: 36px;
    width: 36px;
    color: var(--muted-foreground);
}

.refresh-button:hover {
    background-color: var(--muted);
    color: var(--foreground);
}

.refresh-button:active {
    transform: scale(0.93);
}

.icon-mask {
    display: inline-block;
    width: 20px;
    height: 20px;
    background-color: currentColor;
    mask-size: contain;
    mask-repeat: no-repeat;
    mask-position: center;
}

.icon-refresh {
    mask-image: url('/assets/icons/refresh.svg');
}

.animate-spin {
    animation: spin 0.8s linear infinite;
}

@keyframes spin {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}
</style>
