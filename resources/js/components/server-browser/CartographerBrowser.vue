<script setup lang="ts">
import { ref, onMounted, h } from 'vue';
import UnicodeText from '@/components/UnicodeText.vue';
import DataTable from '@/components/server-browser/DataTable.vue';
import { Button } from '@/components/ui/button';
import type { ColumnDef } from '@tanstack/vue-table';

interface CartoServer 
{
  xuid?: string | number;
  server_name?: string;
  map_name?: string;
  map_id?: number | string;
  gametype?: string;
  variant?: string;
  players?: { filled?: number; max?: number };
  description?: string;
  decoded_properties?: any;
}

const servers = ref<CartoServer[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

// list copied from MAP_ID_TO_INFO
const KNOWN_MAP_IDS = new Set([1,101,105,301,305,401,405,501,505,601,605,701,801,705,805,80,1201,100,60,110,70,1300,10,1302,1400,3001,1200,1001,120,1002,800,1402,50,20,444678,91101,1101,1000,1109,40,30]);

const SORT_ICON_BASE = 'icon-mask inline-block w-3.5 h-3.5 ml-2 align-middle opacity-70';

const renderSortIcon = (state: false | 'asc' | 'desc') => 
{
  const variant = state === 'asc' ? 'icon-sort-up' : state === 'desc' ? 'icon-sort-down' : 'icon-sort';
  return h('span', { class: `${SORT_ICON_BASE} ${variant}`, ariaHidden: 'true' });
};

const makeSortHeader = (label: string, buttonClass = '') => ({ column }: any) => 
{
  const state = column.getIsSorted();

  return h(Button,
    {
      class: ['gap-0', buttonClass].filter(Boolean).join(' '),
      onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
    },
    () => [label, renderSortIcon(state)]
  );
};

const columns: ColumnDef<CartoServer>[] = 
[
  { 
    accessorKey: 'server_name', 
    header: makeSortHeader('Server'), 
    cell: ({ row }) => h('div', { class: 'md:whitespace-nowrap' }, [ 
      h('span', { class: 'font-bold!' }, h(UnicodeText, { text: row.getValue('server_name') })) 
    ]) 
  },

  { 
    accessorKey: 'map_name', 
    header: makeSortHeader('Map'), 
    cell: ({ row }) => h(UnicodeText, { text: row.getValue('map_name') }) 
  },

  {
    id: 'custom_map',
    accessorFn: (row: any) => 
    {
      let mid: any = row.map_id;

      if (mid !== null && mid !== undefined && String(mid).trim() !== '') 
      {
        const midNum = Number(mid);

        return (!Number.isNaN(midNum) && KNOWN_MAP_IDS.has(midNum)) ? 0 : 1;
      }
      // unknown map id -> treat as custom
      return 1;
    },
    header: ({ column }: any) => 
    {
      const state = column.getIsSorted();

      const icon = h('span', {
        class: 'icon-mask icon-download-b inline-block w-4 h-4 leading-none text-muted-foreground relative top-[2px]',
        ariaHidden: 'true',
      });

      return h(Button,
        {
          class: 'gap-0',
          onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
          title: 'Custom Map',
        },
        () => [
          h('span', { class: 'inline-flex items-center' }, [icon, renderSortIcon(state)])
        ]
      );
    },
    // Show icon only when the server's map id is NOT one of the known MAP_ID_TO_INFO ids
    cell: ({ row }) => 
    {
      const original = row.original || {} as any;

      let mid: any = original.map_id;

      if (mid !== null && mid !== undefined && String(mid).trim() !== '') 
      {
        const midNum = Number(mid);

        if (!Number.isNaN(midNum) && KNOWN_MAP_IDS.has(midNum)) 
        {
          return h('span', { class: 'block mx-auto w-8' }, '');
        }
      }

      return h('span', { class: 'inline-flex items-center pl-0 -ml-[0px]' },
        h('span', { class: 'inline-block w-4 h-4 leading-none text-muted-foreground relative top-[0px] icon-mask icon-download-b', title: 'Custom Map' })
      );
    },
  },
  
  { 
    accessorKey: 'gametype', 
    header: makeSortHeader('Gametype'), 
    cell: ({ row }) => h(UnicodeText, { text: row.getValue('gametype') }) 
  },
  
  { 
    accessorKey: 'variant', 
    header: makeSortHeader('Variant'), 
    cell: ({ row }) => h(UnicodeText, { text: row.getValue('variant') }) 
  },
  
  { 
    id: 'players', 
    accessorFn: (row) => 
    {
      const p = row.players;

      if (p && typeof p === 'object')
      {
        return Number(p.filled ?? 0);
      }

      if (typeof p === 'number')
      {
        return Number(p);
      }

      return 0;
    }, 
    header: makeSortHeader('Players'), 
    cell: ({ row }) => 
    {
      const original = row.original || {} as any;
      const p = original.players;
      
      let filled: any = '?';
      let max: any = '?';
      
      if (p && typeof p === 'object') 
      {
        filled = (typeof p.filled !== 'undefined' && p.filled !== null) ? p.filled : '?';
        max = (typeof p.max !== 'undefined' && p.max !== null) ? p.max : '?';
      }
      
      return `${filled}/${max}`;
    }
  },
  
  { 
    accessorKey: 'description', 
    header: makeSortHeader('Description'), 
    cell: ({ row }) => h(UnicodeText, { text: row.getValue('description') || '—', stripUnicode: true }) 
  },
];

async function load() {
  loading.value = true;
  error.value = null;
  // Don't clear `servers` immediately — keep the existing list visible
  // while we fetch new data to avoid a jarring disappearance.
  const newServers: CartoServer[] = [];
  
  try 
  {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    
    // Use the new unified API endpoint
    const res = await fetch('/api/cartographer/list', { signal: controller.signal });
    clearTimeout(timeout);
    
    if (!res.ok) throw new Error(res.statusText || 'Network error');
    
    const data = await res.json();
    
    // The API now returns a structured response with servers array
    let serverList = [];
    
    if (data.servers && Array.isArray(data.servers)) 
    {
      serverList = data.servers;
    } 
    else if (Array.isArray(data)) 
    {
      serverList = data;
    }
    
    // Map the servers to our interface and only replace the visible
    // `servers` after successful fetch so the UI remains stable.
    newServers.push(...serverList.map((item: any) => ({
      xuid: item.xuid,
      server_name: item.server_name || '',
      map_id: item.map_id,
      map_name: item.map_name || '',
      variant: item.variant || '',
      gametype: item.gametype || '',
      players: item.players || { filled: undefined, max: undefined },
      description: item.description || '',
      decoded_properties: item.decoded_properties,
    } as CartoServer)));
    
    // Swap in the new server list once ready.
    servers.value = newServers;
    console.debug('Cartographer: loaded', servers.value.length, 'servers');
    
  } 
  catch (err: any) 
  {
    error.value = err?.message ?? String(err);
    console.warn('Cartographer load failed:', err);
  } 
  finally 
  {
    loading.value = false;
  }
}

onMounted(() => load());

// Expose the loader so parent can trigger refresh
defineExpose({ load });
</script>

<template>
  <div class="carto-browser">
    <div v-if="error" class="text-red-500">{{ error }}</div>

    <DataTable 
      :columns="columns" 
      :data="servers" 
      :searchOptions="[
        { label: 'All', value: 'all' }, 
        { label: 'Server', value: 'server' }, 
        { label: 'Map', value: 'map' }, 
        { label: 'Gametype', value: 'gametype' }, 
        { label: 'Variant', value: 'variant' }, 
        { label: 'Description', value: 'description' }
      ]" 
      :initialSorting="[{ id: 'players', desc: true }]"
      :players="(servers || []).reduce((acc, s) => acc + (s?.players && typeof s.players === 'object' ? Number(s.players.filled ?? 0) : 0), 0)"
      :servers="(servers || []).length"
    >
      <template #left>
        <slot name="left" />
      </template>
    </DataTable>

    <!-- loading indicator intentionally removed so search and selector remain visible -->
  </div>
</template>

<style scoped>
.carto-browser .btn { padding: 0.25rem 0.5rem; border-radius: 0.25rem; background: #efefef }
.odd\:bg-surface:nth-child(odd) { background: #fbfbfb }
</style>
