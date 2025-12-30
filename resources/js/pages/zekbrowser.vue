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
    fetch(props.zekBrowserApi)
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
                <ThemeToggle />
            </div>

            <ServerBrowser v-if="showBrowser" :servers="servers" />

            <h2 class="title is-3">Stats</h2>
            <p class="subtitle">{{ statsStatus }}</p>

            <Chart v-if="chartOptions.series" :options="chartOptions"></Chart>
        </div>
    </section>

</template>

<style scoped>
.header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.header-left {
    display: flex;
    flex-direction: column;
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
