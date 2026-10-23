<script setup lang="ts">
import { Download, Package } from 'lucide-vue-next';

import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { ScrollArea } from '@/components/ui/scroll-area';
import { usePopoverToggle } from '@/composables/usePopoverToggle';
import type { ElDewritoMod } from '@/models/ElDewritoServer';
import { computed } from 'vue';
import '../../../css/ModsCard.css';

const props = defineProps<{
    mods?: ElDewritoMod[];
    jsonUrl?: string;
    showAsNumber?: boolean;
}>();

const { open, toggle } = usePopoverToggle();

const mods = computed(() => props.mods ?? []);
const totalSize = computed(() => mods.value.reduce((acc, mod) => acc + (Number(mod.package_size) || 0), 0));

function formatSize(bytes: number | undefined): string {
    const units = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const value = Number(bytes) || 0;

    if (value <= 0) {
        return '0 b';
    }

    const i = Math.min(units.length - 1, Math.floor(Math.log(value) / Math.log(1024)));

    return (value / Math.pow(1024, i)).toFixed(1) + ' ' + units[i];
}
</script>

<template>
    <ClickPopover v-if="mods.length > 0" v-model:model-value="open" placement="bottom">
        <template #trigger>
            <button v-if="!showAsNumber" type="button" class="icon-button ml-2 inline" @click.stop="toggle">
                <Package :size="18" class="opacity-40 hover:opacity-60" />
            </button>
            <button v-else type="button" class="mods-count-button cursor-pointer hover:opacity-80" @click.stop="toggle">
                {{ mods.length }}
            </button>
        </template>
        <div class="w-96 overflow-hidden rounded-xl border border-border/60 bg-card shadow-lg">
            <div class="flex items-center justify-between border-b border-border/40 px-4 py-3">
                <div class="flex items-center gap-2">
                    <Package :size="15" class="text-muted-foreground" />
                    <h4 class="text-sm font-semibold text-foreground">Mod Packs</h4>
                </div>
                <span class="text-[11px] text-muted-foreground tabular-nums">
                    {{ mods.length }} mod{{ mods.length > 1 ? 's' : '' }} &middot; {{ formatSize(totalSize) }}
                </span>
            </div>
            <ScrollArea class="h-72 w-full">
                <div class="mods-card py-1.5">
                    <div v-for="(mod, idx) in mods" :key="mod.id" class="mod-entry">
                        <div class="flex items-center gap-3 px-4 py-2.5 transition-colors hover:bg-muted/30">
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2">
                                    <span class="truncate text-[13px] font-medium text-foreground">{{ mod.mod_name }}</span>
                                    <span v-if="mod.mod_version" class="mod-version">{{ mod.mod_version }}</span>
                                </div>
                                <div v-if="mod.mod_author" class="mt-0.5 text-[11px] text-muted-foreground">{{ mod.mod_author }}</div>
                                <div v-if="mod.mod_website" class="mt-0.5 max-w-[220px]">
                                    <a
                                        :href="mod.mod_website"
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        class="block truncate text-[11px] text-muted-foreground transition-colors hover:text-foreground hover:underline"
                                        :title="mod.mod_website"
                                    >
                                        {{ mod.mod_website }}
                                    </a>
                                </div>
                            </div>

                            <a
                                :href="mod.package_url"
                                target="_blank"
                                class="flex flex-shrink-0 items-center gap-1.5 rounded-md bg-muted/50 px-2.5 py-1 text-[11px] text-muted-foreground tabular-nums transition-colors hover:bg-muted hover:text-foreground"
                            >
                                <Download :size="12" />
                                {{ formatSize(mod.package_size) }}
                            </a>
                        </div>
                        <div v-if="idx < mods.length - 1" class="mx-4 border-b border-border/30"></div>
                    </div>
                </div>
            </ScrollArea>
            <div class="flex justify-end border-t border-border/40 px-4 py-2">
                <a
                    v-if="jsonUrl"
                    :href="jsonUrl"
                    target="_blank"
                    class="text-[11px] text-muted-foreground transition-colors hover:text-foreground hover:underline"
                >
                    View JSON
                </a>
            </div>
        </div>
    </ClickPopover>
</template>
