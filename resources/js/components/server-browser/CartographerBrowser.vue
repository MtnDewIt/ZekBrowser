<script setup lang="ts">
import { ref, onMounted, h } from 'vue';
import DataTable from '@/components/server-browser/DataTable.vue';
import { Button } from '@/components/ui/button';
import type { ColumnDef } from '@tanstack/vue-table';

interface CartoServer {
  xuid?: string | number;
  server_name?: string;
  map_name?: string;
  gametype?: string;
  players?: { filled?: number; max?: number };
  description?: string;
  loading?: boolean;
}

const servers = ref<CartoServer[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

function normalizeList(data: any): any[] {
    if (Array.isArray(data)) return data;
    if (data && typeof data === 'object') {
        return data.servers || data.list || data.data || [];
    }
    return [];
}

const BATCH_SIZE = 8;

const SORT_ICON_BASE = 'icon-mask inline-block w-3.5 h-3.5 ml-2 align-middle opacity-70';

const renderSortIcon = (state: false | 'asc' | 'desc') => {
  const variant = state === 'asc' ? 'icon-sort-up' : state === 'desc' ? 'icon-sort-down' : 'icon-sort';
  return h('span', { class: `${SORT_ICON_BASE} ${variant}`, ariaHidden: 'true' });
};

const makeSortHeader = (label: string, buttonClass = '') => ({ column }: any) => {
  const state = column.getIsSorted();
  return h(Button,
    {
      class: ['gap-0', buttonClass].filter(Boolean).join(' '),
      onClick: () => column.toggleSorting(column.getIsSorted() === 'asc'),
    },
    () => [label, renderSortIcon(state)]
  );
};

const columns: ColumnDef<CartoServer>[] = [
  { accessorKey: 'xuid', header: makeSortHeader('XUID'), cell: ({ row }) => String(row.getValue('xuid') || '') },
  { accessorKey: 'server_name', header: makeSortHeader('Server'), cell: ({ row }) => h('div', { class: 'md:whitespace-nowrap' }, [ h('span', { class: 'font-bold!' }, row.getValue('server_name')) ]) },
  { accessorKey: 'map_name', header: makeSortHeader('Map'), cell: ({ row }) => row.getValue('map_name') },
  { accessorKey: 'gametype', header: makeSortHeader('Gametype'), cell: ({ row }) => row.getValue('gametype') },
  { accessorKey: 'variant', header: makeSortHeader('Variant'), cell: ({ row }) => row.getValue('variant') },
  { id: 'players', accessorFn: (row) => {
      const p = row.players || (row as any).players;
      if (p && typeof p === 'object') return Number(p.filled ?? 0);
      if (typeof p === 'number') return Number(p);
      return 0;
    }, header: makeSortHeader('Players'), cell: ({ row }) => {
      const val = row.getValue('players');
      // val may be the numeric filled count (accessorFn), so prefer original.players for full info
      const original = row.original || {} as any;
      let pObj: any = null;
      if (original && original.players && typeof original.players === 'object') {
        pObj = original.players;
      } else if (val && typeof val === 'object') {
        pObj = val;
      }

      let filled: any = '?';
      let max: any = '?';
      if (pObj && typeof pObj === 'object') {
        filled = (typeof pObj.filled !== 'undefined' && pObj.filled !== null) ? pObj.filled : '?';
        max = (typeof pObj.max !== 'undefined' && pObj.max !== null) ? pObj.max : '?';
      } else if (typeof val === 'number') {
        filled = val;
        max = (original.players && typeof original.players.max !== 'undefined') ? original.players.max : '?';
      }
      return `${filled}/${max}`;
    }
  },
  { accessorKey: 'description', header: makeSortHeader('Description'), cell: ({ row }) => row.getValue('description') || '—' },
];

async function fetchDetails(id: number | string): Promise<CartoServer | null> {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const res = await fetch(`/api/cartographer/servers/${id}`, { signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) throw new Error(`status=${res.status}`);
    const data = await res.json();
    const pp = data.pProperties || [];
    const props: Record<string, any> = {};
    for (const p of pp) {
      if (p && typeof p.dwPropertyId !== 'undefined') props[String(p.dwPropertyId)] = p.value;
    }

    return {
      xuid: data.xuid || data.id || data.server_id || id,
      server_name: props['1073775152'] || props['1073775141'] || data.name || '',
      map_name: props['268468743'] || props['268468746'] || '',
      variant: props['1073775144'] || props['1073775147'] || '',
      gametype: props['268468745'] || props['1073775144'] || '',
      players: { filled: data.dwFilledPublicSlots, max: data.dwMaxPublicSlots },
      description: props['1073775141'] || data.server_desc || '',
    } as CartoServer;
  } catch (err) {
    console.warn('fetchDetails failed for', id, err);
    return { xuid: id, server_name: '', map_name: '', gametype: '', players: { filled: undefined, max: undefined }, description: '<failed>' } as CartoServer;
  }
}

async function load() {
  loading.value = true;
  error.value = null;
  servers.value = [];
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const res = await fetch('/api/cartographer/list', { signal: controller.signal });
    clearTimeout(timeout);
    if (!res.ok) throw new Error(res.statusText || 'Network error');
    const data = await res.json();
    const list = normalizeList(data);

    // If the API already returned summarized server objects (from the python script),
    // use them directly. Detect by presence of `server_name` or `map_name` keys.
    if (list.length > 0 && typeof list[0] === 'object' && (list[0].server_name || list[0].map_name || list[0].gametype)) {
      console.debug('Cartographer: received summarized server objects, rendering directly', list.length);
      servers.value = list.map((item: any) => ({
        xuid: item.xuid || item.id || item.server_id,
        server_name: item.server_name || '',
        map_name: item.map_name || '',
        variant: item.variant || '',
        gametype: item.gametype || '',
        players: item.players || { filled: undefined, max: undefined },
        description: item.description || '',
        loading: false,
      } as CartoServer));
      return;
    }

    // Try to map servers directly from the list payload first (common case when raw pProperties are present)
    const mapped = list.map((item: any) => {
      const pp = item.pProperties || [];
      const props: Record<string, any> = {};
      for (const p of pp) if (p && typeof p.dwPropertyId !== 'undefined') props[String(p.dwPropertyId)] = p.value;
      return {
        raw: item,
        xuid: item.xuid || item.id || item.server_id,
        server_name: props['1073775152'] || props['1073775141'] || item.name || '',
        map_name: props['268468743'] || props['268468746'] || '',
        variant: props['1073775144'] || props['1073775147'] || '',
        gametype: props['268468745'] || props['1073775144'] || '',
        players: { filled: item.dwFilledPublicSlots, max: item.dwMaxPublicSlots },
        description: props['1073775141'] || item.server_desc || '',
      } as CartoServer;
    });

    // If the mapped list already contains usable server names, use it directly.
    const hasNames = mapped.some((m) => m.server_name && String(m.server_name).trim() !== '');
    if (hasNames) {
      console.debug('Cartographer: using mapped list (no per-server fetch needed)', mapped.length);
      servers.value = mapped;
      return;
    }

    // Otherwise fall back to extracting ids and fetching per-server details
    const ids: Array<number | string> = [];
    const seen = new Set<string>();
    for (const item of list) {
      let id: number | string | null = null;
      if (typeof item === 'number' || typeof item === 'string') id = item;
      else id = item.xuid || item.id || item.server_id || null;
      if (id != null) {
        const key = String(id);
        if (!seen.has(key)) {
          seen.add(key);
          ids.push(id);
        }
      }
    }

    if (ids.length === 0) {
      console.debug('Cartographer: no ids to fetch and mapped list empty');
      servers.value = [];
      return;
    }

    // Fetch details with a worker pool so rows update progressively
    const placeholders: CartoServer[] = ids.map((id) => ({ xuid: id, server_name: '', map_name: '', gametype: '', players: { filled: undefined, max: undefined }, description: '', loading: true }));
    servers.value = placeholders;

    const concurrency = Math.max(2, Math.min(BATCH_SIZE, 12));
    let idx = 0;

    async function worker() {
      while (true) {
        const my = idx++;
        if (my >= ids.length) return;
        const id = ids[my];
        const details = await fetchDetails(id);
        // find and update the placeholder at index `my` (should align)
        if (details) {
          servers.value[my] = { ...details, loading: false };
        } else {
          servers.value[my] = { xuid: id, server_name: '', description: '<failed>', loading: false } as CartoServer;
        }
      }
    }

    const workers: Promise<void>[] = [];
    for (let w = 0; w < concurrency; w++) workers.push(worker());
    await Promise.all(workers);
  } catch (err: any) {
    error.value = err?.message ?? String(err);
    console.warn('Cartographer load failed:', err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => load());

// expose the loader so parent can trigger refresh
defineExpose({ load });
</script>

<template>
  <div class="carto-browser">
    <div class="flex items-center justify-between mb-2">
      <!-- header intentionally left blank to match global UI -->
    </div>

    <div v-if="loading">Loading…</div>
    <div v-else-if="error" class="text-red-500">{{ error }}</div>
    <div v-else>
      <DataTable :columns="columns" :data="servers" :searchOptions="[
        { label: 'All', value: 'all' },
        { label: 'Server', value: 'server' },
        { label: 'Map', value: 'map' },
        { label: 'Gametype', value: 'gametype' },
        { label: 'Variant', value: 'variant' },
        { label: 'Description', value: 'description' },
      ]" :initialSorting="[{ id: 'players', desc: true }]" />
    </div>
  </div>
</template>

<style scoped>
.carto-browser .btn { padding: 0.25rem 0.5rem; border-radius: 0.25rem; background: #efefef }
.odd\:bg-surface:nth-child(odd) { background: #fbfbfb }
</style>
