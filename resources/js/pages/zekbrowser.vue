<script setup lang="ts">
import ServerBrowser from '@/components/server-browser/ServerBrowser.vue';
import ThemeToggle from '@/components/ThemeToggle.vue';
import { ValidationError } from '@/exceptions/ValidationError';
import { ElDewritoServer } from '@/models/ElDewritoServer';
import { Head } from '@inertiajs/vue3';
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
const activeBrowser = ref<'eldewrito' | 'cartographer' | 'haloce' | 'halopc'>('eldewrito');

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

                if (active !== 'cartographer' && active !== 'haloce' && active !== 'halopc') 
                {
                    updateCounts(data.count);
                }
            } 
            catch (e) 
            {
                // If child ref isn't available yet, respect the parent's reactive `activeBrowser`
                if (activeBrowser.value !== 'cartographer' && activeBrowser.value !== 'haloce' && activeBrowser.value !== 'halopc') {
                    updateCounts(data.count);
                }
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

            // Build a fresh list of ElDewritoServer instances
            const newList: any[] = [];
            serverArray.forEach((serverData) => {
                try {
                    newList.push(new ElDewritoServer(serverData));
                } catch (error) {
                    if (error instanceof ValidationError) {
                        console.warn(`Validation failed for ${serverData.ip}:`, error.errors);
                    } else {
                        console.error(`Unexpected error for server ${serverData.ip}:`, error);
                    }
                }
            });
            servers.value = newList;

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

    if (activeBrowser.value === 'haloce') 
    {
        statsURL = `${props.zekBrowserApi}haloce/stats`;
    } 

    if (activeBrowser.value === 'halopc') 
    {
        statsURL = `${props.zekBrowserApi}halopc/stats`;
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

const REFRESH_INTERVAL = 30000; // 30 seconds
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

function handleBrowserChange(browserType: 'eldewrito' | 'cartographer' | 'haloce' | 'halopc') {
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
        // Refresh stats after the server list/counts refresh so charts stay in sync
        try {
            fetchStats();
        } catch (e) {
            console.warn('fetchStats() failed after refresh:', e);
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
    // attempt to synchronize `activeBrowser` with the child `ServerBrowser`
    try {
        const sel = serverBrowser.value && typeof serverBrowser.value.getSelection === 'function'
            ? serverBrowser.value.getSelection()
            : null;

        if (sel === 'cartographer' || sel === 'eldewrito' || sel === 'haloce' || sel === 'halopc') {
            activeBrowser.value = sel;
        }
    } catch (e) { /* ignore */ }

    fetchZekBrowser();
    fetchStats();
    
    // Set up auto-refresh every interval; delegate to the shared handler
    refreshTimer = globalThis.setInterval(() => 
    {
        // Use the same refresh flow as manual refresh so Cartographer
        // (via ServerBrowser.refresh) will be triggered when active.
        try {
            void handleRefresh();
        } catch (e) {
            console.warn('Auto-refresh failed:', e);
        }
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

    <section class="px-4 py-6 sm:px-6 lg:px-8">
        <div class="mx-auto flex flex-col items-center">
            <div class="flex flex-col w-full max-w-[1800px]">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex flex-col">
                        <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">ZekBrowser</h1>
                    </div>
                    <div class="flex items-center gap-2 relative z-30">
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
            
                <div class="flex items-center justify-between mt-8 mb-4">
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
.refresh-button 
{
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

.refresh-button:hover 
{
    background-color: var(--muted);
    color: var(--foreground);
}

.refresh-button:active 
{
    transform: scale(0.93);
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
    animation: spin 0.8s linear infinite;
}

@keyframes spin 
{
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
