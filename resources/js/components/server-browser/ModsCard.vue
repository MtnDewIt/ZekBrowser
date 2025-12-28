<script setup lang="ts">
import { Download, Package } from 'lucide-vue-next';

import { Button } from '@/components/ui/button';
import { HoverCard, HoverCardContent, HoverCardTrigger } from '@/components/ui/hover-card';

import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'

interface Props {
    mods?: object[];
    jsonUrl?: string;
    showAsNumber?: boolean;
}

const props = defineProps<Props>();

const total = props.mods?.reduce((acc, mod) => acc + mod.package_size, 0);

const size = (bytes) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '0 b';

    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + sizes[i];
};
</script>

<template>
    <HoverCard v-if="mods?.length > 0">
        <HoverCardTrigger as-child>
            <Package v-if="!showAsNumber" :size="18" class="ml-2 inline opacity-40 hover:opacity-60"/>
            <span v-else class="cursor-default hover:opacity-80">{{ mods.length }}</span>
        </HoverCardTrigger>
        <HoverCardContent class="w-90 p-0 bg-background/100 dark:bg-background/100 backdrop-blur-xs">
            <ScrollArea class="h-48 w-full">
                <div class="p-4">
                    <h4 class="mb-4 text-foreground has-text-weight-semibold">
                        Mod Packs
                    </h4>

                    <div v-for="mod in mods" :key="mod.id">
                        <div class="flex justify-between text-sm items-center">
                            <div>
                                {{ mod.mod_name }}

                                <span v-if="mod.mod_version" class="ml-1 text-xs opacity-50">
                                    v{{ mod.mod_version }}
                                </span>
                            </div>

                            <Button
                                as="a"
                                size="sm"
                                :href="mod.package_url"
                                target="_blank"
                                variant="outline"
                                class="min-w-22 flex px-2 text-xs font-normal text-muted-foreground!"
                            >
                                <Download :size="16"/>
                                {{ size(mod.package_size) }}
                            </Button>
                        </div>
                        <Separator class="my-2" />
                    </div>

                    <div class="flex justify-between mt-5 text-xs opacity-60">
                        <p>{{ mods.length}} mod{{ mods.length > 1 ? 's' : '' }}, {{ size(total) }} total</p>
                        <a v-if="jsonUrl"
                           :href="jsonUrl"
                           target="_blank"
                           class="text-muted-foreground! hover:underline!">JSON</a>
                    </div>
                </div>
            </ScrollArea>
        </HoverCardContent>
    </HoverCard>
</template>
