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

interface Props 
{
    zekBrowserApi: string;
}

const props = defineProps<Props>();

const playerCount = ref(0);
const serverCount = ref(0);
const servers = ref<ElDewritoServer[]>([]);

const showBrowser = ref(false);
const browserStatus = ref('Loading...');
const activeBrowser = ref<'eldewrito' | 'cartographer'>('eldewrito');

const statsStatus = ref('Loading...');
const chartOptions = ref({
    accessibility: 
    {
        enabled: false,
    },
    chart: 
    {
        styledMode: true,
        zoomType: 'x',
    },
    credits: 
    {
        enabled: false,
    },
    title: 
    {
        text: null,
    },
    xAxis: 
    {
        type: 'datetime',
    },
    yAxis: 
    {
        title: 
        {
            text: null,
        },
    },
    legend: 
    {
        enabled: false,
    },
    time: 
    {
        useUTC: false,
    },
});

async function fetchZekBrowser() 
{
    return fetch(props.zekBrowserApi)
        .then((response) => response.json())
        .then((data) => 
        {
            // Only update the header counts from ElDewrito data when the
            // active server browser is not Cartographer. If the user is
            // viewing Cartographer, that component will emit its own counts.
            try 
            {
                const active = serverBrowser.value && typeof serverBrowser.value.getSelection === 'function' ? serverBrowser.value.getSelection() : null;

                if (active !== 'cartographer') 
                {
                    updateCounts(data.count);
                }
            } 
            catch (e) 
            {
                updateCounts(data.count);
            }

            const serverArray: object[] = [];

            Object.entries(data.servers).forEach(([ip, server]) => 
            {
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
            serverArray.forEach((serverData) => 
            {
                try 
                {
                    const server = new ElDewritoServer(serverData);
                    servers.value.push(server);
                } 
                catch (error) 
                {
                    if (error instanceof ValidationError) 
                    {
                        console.warn(`Validation failed for ${serverData.ip}:`, error.errors);
                    } 
                    else 
                    {
                        console.error(`Unexpected error for server ${serverData.ip}:`, error);
                    }
                }
            });

            showBrowser.value = true;
        })
        .catch((error) => 
        {
            browserStatus.value = 'Whoops, something bad happened.';
            console.error(error);
        });
}

function updateCounts(count) 
{
    playerCount.value = count.players;
    serverCount.value = count.servers;
    const rip = playerCount.value === 0 ? ' rip' : '';

    browserStatus.value = `${playerCount.value} players on ${serverCount.value} servers.${rip}`;
}

function fetchStats() 
{
    var statsURL = '';

    if (activeBrowser.value === 'eldewrito') 
    {
        statsURL = `${props.zekBrowserApi}stats`;
    } 

    if (activeBrowser.value === 'cartographer') 
    {
        statsURL = `${props.zekBrowserApi}cartographer/stats`;
    }

    fetch(statsURL)
        .then((response) => response.json())
        .then((data) => 
        {
            chartOptions.value.series = 
            [
                {
                    name: 'Players',
                    data: data.players,
                    turboThreshold: 10000,
                    marker: 
                    {
                        enabled: false
                    },
                },
                {
                    name: 'Servers',
                    data: data.servers,
                    turboThreshold: 10000,
                    marker: 
                    {
                        enabled: false
                    },
                },
            ];

            statsStatus.value = '';
        })
        .catch((error) => 
        {
            statsStatus.value = 'Whoops, something bad happened.';
            console.error(error);
        });
}

const REFRESH_INTERVAL = 15000; // 30 seconds
let refreshTimer: number | null = null;

const isRefreshing = ref(false);
const serverBrowser = ref<any>(null);
const cartoCountsLoading = ref(false);

function handleChildCounts(payload: { players: number; servers: number }) {
    playerCount.value = payload.players;
    serverCount.value = payload.servers;
    const rip = playerCount.value === 0 ? ' rip' : '';
    browserStatus.value = `${playerCount.value} players on ${serverCount.value} servers.${rip}`;
}

function handleChildCountsLoading(val: boolean) {
    cartoCountsLoading.value = val;
}

function handleBrowserChange(browserType: 'eldewrito' | 'cartographer') {
    activeBrowser.value = browserType;
    fetchStats();
}

async function handleRefresh() 
{
    isRefreshing.value = true;
    const minDelay = new Promise(resolve => setTimeout(resolve, 600));
    try 
    {
        // Give the ServerBrowser a chance to handle the refresh (e.g., Cartographer view)
        let handled = false;
        if (serverBrowser.value && typeof serverBrowser.value.refresh === 'function') {
            try {
                handled = await serverBrowser.value.refresh();
            } catch (e) {
                console.warn('serverBrowser.refresh() failed:', e);
            }
        }

        if (!handled) {
            await Promise.all([fetchZekBrowser(), minDelay]);
        } else {
            await minDelay;
        }
    } 
    catch (error) 
    {
        console.error('Manual refresh failed:', error);
    } 
    finally 
    {
        isRefreshing.value = false;
    }
}

onMounted(async () => 
{
    fetchZekBrowser();
    fetchStats();
    
    // Set up auto-refresh every 30 seconds
    refreshTimer = globalThis.setInterval(() => 
    {
        fetchZekBrowser();
    }, REFRESH_INTERVAL);
});

onUnmounted(() => 
{
    // Clean up the timer when component is destroyed
    if (refreshTimer !== null) 
    {
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

    <section class="section">
        <div class="container-flex">
            <div class="container-flex-flex">
                <div class="header-container">
                    <div class="header-left">
                        <h1 class="title is-2">ZekBrowser</h1>
                        <p class="subtitle is-spaced"></p>
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
            
                <ServerBrowser ref="serverBrowser" v-if="showBrowser" :servers="servers" @counts="handleChildCounts" @counts-loading="handleChildCountsLoading" @browser-change="handleBrowserChange" />
            
                <div class="header-container-stats">
                    <h2 class="title is-3">Stats</h2>
                    <p class="subtitle">{{ statsStatus }}</p>
                </div>
            
                <Chart v-if="chartOptions.series" :options="chartOptions"></Chart>
            </div>
        </div>
    </section>
</template>

<style scoped>
.container-flex 
{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
}

.container-flex-flex 
{
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: left;

    /*TODO: Maybe add better handling for weird resolutions*/
    width: min(100%, calc(100vh * 16 / 9));
}

.header-container 
{
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.header-container-stats 
{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 2.25rem;
    margin-bottom: 1rem;
}

.header-left 
{
    display: flex;
    flex-direction: column;
}

.header-right 
{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    /* ensure header actions sit above translated search-row so they're clickable */
    position: relative;
    z-index: 30;
}

.refresh-button 
{
    background: none;
    border: none;
    cursor: pointer;
    padding: 4px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: all 0.15s ease;
    height: 36px;
    width: 36px;
}

.refresh-button:hover 
{
    background-color: rgba(0, 0, 0, 0.08);
}

.refresh-button:active 
{
    transform: scale(0.95);
}

.icon-mask 
{
    display: inline-block;
    width: 20px;
    height: 20px;
    background-color: currentColor;
    mask-size: contain;
    mask-repeat: no-repeat;
    mask-position: center;
}

.icon-refresh 
{
    mask-image: url('/assets/icons/refresh.svg');
}

.animate-spin 
{
    animation: spin 1s linear infinite;
}

:deep(.header-right .theme-toggle) {
    height: 36px;
    width: 36px;
}

@keyframes spin 
{
    from 
    {
        transform: rotate(0deg);
    }
    to 
    {
        transform: rotate(360deg);
    }
}
</style>

<style>
:root 
{
    --background: var(--bulma-body-background-color);
}

.dark 
{
    background-color: var(--background);
}
</style>
