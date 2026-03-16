<script setup lang="ts">

import { Download, Package } from 'lucide-vue-next';

import { Button } from '@/components/ui/button';
import ClickPopover from '@/components/ui/click-popover/ClickPopover.vue';
import { ref } from 'vue';

import { ScrollArea } from '@/components/ui/scroll-area'
import '../../../css/ModsCard.css';

interface Props 
{
    mods?: object[];
    jsonUrl?: string;
    showAsNumber?: boolean;
}

const props = defineProps<Props>();
const open = ref(false);
const _ignoreOpenUntil = ref(0);

function toggleOpen() {
    const now = Date.now();

    if (open.value) {
        open.value = false;
        _ignoreOpenUntil.value = now + 300;
        return;
    }

    if (now < _ignoreOpenUntil.value) return;

    open.value = true;
}
const total = props.mods?.reduce((acc, mod) => acc + mod.package_size, 0);

const size = (bytes) => 
{
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '0 b';

    const i = Number.parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
};
</script>

<template>
        <ClickPopover v-if="mods?.length > 0" v-model:modelValue="open" placement="bottom">
            <template #trigger>
                <template v-if="!showAsNumber">
                    <button type="button" class="icon-button ml-2 inline" @click.stop="toggleOpen">
                        <Package :size="18" class="opacity-40 hover:opacity-60"/>
                    </button>
                </template>
                <template v-else>
                    <button type="button" class="mods-count-button cursor-pointer hover:opacity-80" @click.stop="toggleOpen">
                        {{ mods.length }}
                    </button>
                </template>
            </template>
            <div class="w-96 rounded-xl border border-border/60 bg-card shadow-lg overflow-hidden">
            <div class="px-4 py-3 border-b border-border/40 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <Package :size="15" class="text-muted-foreground" />
                    <h4 class="text-sm font-semibold text-foreground">Mod Packs</h4>
                </div>
                <span class="text-[11px] text-muted-foreground tabular-nums">{{ mods.length }} mod{{ mods.length > 1 ? 's' : '' }} &middot; {{ size(total) }}</span>
            </div>
            <ScrollArea class="h-72 w-full">
                <div class="py-1.5 mods-card">
                    <div v-for="(mod, idx) in mods" :key="mod.id" class="mod-entry">
                        <div class="flex items-center gap-3 px-4 py-2.5 hover:bg-muted/30 transition-colors">
                            <div class="min-w-0 flex-1">
                                <div class="flex items-center gap-2">
                                    <span class="font-medium text-[13px] text-foreground truncate">{{ mod.mod_name }}</span>
                                    <span v-if="mod.mod_version" class="mod-version">{{ mod.mod_version }}</span>
                                </div>
                                <div v-if="mod.mod_author" class="text-[11px] text-muted-foreground mt-0.5">{{ mod.mod_author }}</div>
                                <div v-if="mod.mod_website" class="mt-0.5 max-w-[220px]">
                                    <a :href="mod.mod_website" target="_blank" rel="noopener noreferrer" class="text-[11px] text-muted-foreground hover:text-foreground hover:underline truncate block transition-colors" :title="mod.mod_website">{{ mod.mod_website }}</a>
                                </div>
                            </div>

                            <a
                                :href="mod.package_url"
                                target="_blank"
                                class="flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-muted/50 hover:bg-muted text-[11px] tabular-nums text-muted-foreground hover:text-foreground transition-colors"
                            >
                                <Download :size="12"/>
                                {{ size(mod.package_size) }}
                            </a>
                        </div>
                        <div v-if="idx < mods.length - 1" class="mx-4 border-b border-border/30"></div>
                    </div>
                </div>
            </ScrollArea>
            <div class="px-4 py-2 border-t border-border/40 flex justify-end">
                <a v-if="jsonUrl" :href="jsonUrl"
                   target="_blank"
                   class="text-[11px] text-muted-foreground hover:text-foreground hover:underline transition-colors">View JSON</a>
            </div>
            </div>
        </ClickPopover>
</template>
