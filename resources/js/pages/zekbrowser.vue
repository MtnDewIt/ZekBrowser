<script setup lang="ts">
import ServerBrowser from '@/components/server-browser/ServerBrowser.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import { ValidationError } from '@/exceptions/ValidationError';
import { ElDewritoServer } from '@/models/ElDewritoServer';
import { Head } from '@inertiajs/vue3';
import 'bulma/css/bulma.min.css';
import 'highcharts/css/highcharts.css';
import { Chart } from 'highcharts-vue';
import { onMounted, onUnmounted, ref } from 'vue';

interface Props {
    zekBrowserApi: string;
}

const props = defineProps<Props>();

const playerCount = ref(0);
const serverCount = ref(0);
const servers = ref<ElDewritoServer[]>([]);

const showBrowser = ref(false);
const browserStatus = ref('Loading...');

const statsStatus = ref('Loading...');
const chartOptions = ref({
    accessibility: {
        enabled: false,
    },
    chart: {
        styledMode: true,
        zoomType: 'x',
    },
    credits: {
        enabled: false,
    },
    title: {
        text: null,
    },
    xAxis: {
        type: 'datetime',
    },
    yAxis: {
        title: {
            text: null,
        },
    },
    legend: {
        enabled: false,
    },
    time: {
        useUTC: false,
    },
});

function fetchZekBrowser() {
    return fetch(props.zekBrowserApi)
        .then((response) => response.json())
        .then((data) => {
            updateCounts(data.count);

            const serverArray: object[] = [];

            Object.entries(data.servers).forEach(([ip, server]) => {
                serverArray.push({
                    ip: ip,
                    name: server.name,
                    port: server.port,
                    fileServerPort: server.fileServerPort,
                    hostPlayer: server.hostPlayer,
                    passworded: server.passworded,
                    sprintState: server.sprintState,
                    sprintUnlimitedEnabled: server.sprintUnlimitedEnabled,
                    assassinationEnabled: server.assassinationEnabled,
                    voteSystemType: server.voteSystemType,
                    teams: server.teams,
                    map: server.map,
                    mapFile: server.mapFile,
                    variant: server.variant,
                    variantType: server.variantType,
                    status: server.status,
                    numPlayers: server.numPlayers,
                    maxPlayers: server.maxPlayers,
                    modCount: server.modCount,
                    modPackageName: server.modPackageName,
                    modPackageAuthor: server.modPackageAuthor,
                    modPackageHash: server.modPackageHash,
                    modPackageVersion: server.modPackageVersion,
                    xnkid: server.xnkid,
                    xnaddress: server.xnaddress,
                    players: server.players,
                    isDedicated: server.isDedicated,
                    gameVersion: server.gameVersion,
                    eldewritoVersion: server.eldewritoVersion,
                    firstSeenAt: server.firstSeenAt,
                    eldewritoVersionShort: server.eldewritoVersionShort,
                    reverseDns: server.reverseDns,
                    mods: server.mods,
                });
            });

            servers.value = [];
            serverArray.forEach((serverData) => {
                try {
                    const server = new ElDewritoServer(serverData);
                    servers.value.push(server);
                } catch (error) {
                    if (error instanceof ValidationError) {
                        console.warn(`Validation failed for ${serverData.ip}:`, error.errors);
                    } else {
                        console.error(`Unexpected error for server ${serverData.ip}:`, error);
                    }
                }
            });

            showBrowser.value = true;
        })
        .catch((error) => {
            browserStatus.value = 'Whoops, something bad happened.';
            console.error(error);
        });
}

function updateCounts(count) {
    playerCount.value = count.players;
    serverCount.value = count.servers;
    const rip = playerCount.value === 0 ? ' rip' : '';

    browserStatus.value = `${playerCount.value} players on ${serverCount.value} servers.${rip}`;
}

function fetchStats() {
    fetch(`${props.zekBrowserApi}stats`)
        .then((response) => response.json())
        .then((data) => {
            chartOptions.value.series = [
                {
                    name: 'Players',
                    data: data.players,
                    turboThreshold: 10000,
                    marker: {
                        enabled: false
                    },
                },
                {
                    name: 'Servers',
                    data: data.servers,
                    turboThreshold: 10000,
                    marker: {
                        enabled: false
                    },
                },
            ];

            statsStatus.value = '';
        })
        .catch((error) => {
            statsStatus.value = 'Whoops, something bad happened.';
            console.error(error);
        });
}

const REFRESH_INTERVAL = 15000; // 30 seconds
let refreshTimer: number | null = null;

const isRefreshing = ref(false);

async function handleRefresh() {
    isRefreshing.value = true;
    const minDelay = new Promise(resolve => setTimeout(resolve, 600));
    try {
        await Promise.all([fetchZekBrowser(), minDelay]);
    } catch (error) {
        console.error('Manual refresh failed:', error);
    } finally {
        isRefreshing.value = false;
    }
}

onMounted(async () => {
    fetchZekBrowser();
    fetchStats();
    
    // Set up auto-refresh every 30 seconds
    refreshTimer = window.setInterval(() => {
        fetchZekBrowser();
    }, REFRESH_INTERVAL);
});

onUnmounted(() => {
    // Clean up the timer when component is destroyed
    if (refreshTimer !== null) {
        clearInterval(refreshTimer);
    }
});
</script>

<template>
    <Head title="ZekBrowser">
        <meta
            name="description"
            content="Find and join ElDewrito servers with the server browser. Play unique maps, game modes, and mods from the community."
        />
    </Head>

    <section class="section">
        <div class="container">
            <div class="header-container">
                <div class="header-left">
                    <h1 class="title is-2">ZekBrowser</h1>
                    <p class="subtitle is-spaced">{{ browserStatus }}</p>
                </div>
                <div class="header-right">
                    <button
                        @click="handleRefresh"
                        class="refresh-button"
                        :title="isRefreshing ? 'Refreshing...' : 'Refresh server list'"
                        :aria-label="isRefreshing ? 'Refreshing...' : 'Refresh server list'"
                    >
                        <span
                            class="icon-mask icon-refresh"
                            :class="{ 'animate-spin': isRefreshing }"
                            aria-hidden="true"
                        ></span>
                    </button>
                    <ThemeToggle />
                </div>
            </div>

            <ServerBrowser v-if="showBrowser" :servers="servers" />

            <div class="header-container-stats">
                <h2 class="title is-3">Stats</h2>
                <p class="subtitle">{{ statsStatus }}</p>
            </div>

            <Chart v-if="chartOptions.series" :options="chartOptions"></Chart>
        </div>
    </section>

</template>

<style scoped>
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-container-stats {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 2.25rem;
    margin-bottom: 1rem;
}

.header-left {
    display: flex;
    flex-direction: column;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.refresh-button {
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
}

.refresh-button:hover {
    background-color: rgba(0, 0, 0, 0.08);
}

.refresh-button:active {
    transform: scale(0.95);
}

:global(.dark) .refresh-button:hover {
    background-color: rgba(255, 255, 255, 0.12);
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
    animation: spin 1s linear infinite;
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

<style>
:root {
    --background: var(--bulma-body-background-color);
}

/* Bulma dark mode overrides */
:global(.dark) {
    --bulma-body-background-color: #0a0a0a;
    --bulma-body-color: #f5f5f5;
    --bulma-text-strong: #f5f5f5;
    --bulma-title-color: #f5f5f5;
    --bulma-subtitle-color: #b5b5b5;
}

:global(.dark) .section {
    background-color: #0a0a0a;
}

:global(.dark) .title,
:global(.dark) .subtitle {
    color: #f5f5f5;
}
</style>
