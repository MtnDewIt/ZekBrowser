<script setup lang="ts">
import { Select } from '@/components/ui/select';
import { isBrowserType, type BrowserType } from '@/lib/api';
import { computed } from 'vue';

const model = defineModel<BrowserType>({ required: true });

const OPTIONS = [
    { label: 'ElDewrito', value: 'eldewrito', icon: '/assets/logos/eldewrito.webp', iconRounded: true },
    { label: 'Cartographer', value: 'cartographer', icon: '/assets/logos/cartographer.webp', iconRounded: true },
    { label: 'Halo CE', value: 'haloce', icon: '/assets/logos/haloce.webp', iconRounded: true },
    { label: 'Halo PC', value: 'halopc', icon: '/assets/logos/haloce.webp', iconRounded: true },
];

const selected = computed(() => OPTIONS.find((o) => o.value === model.value) ?? OPTIONS[0]);

function onUpdate(value: string) {
    if (isBrowserType(value)) {
        model.value = value;
    }
}
</script>

<template>
    <Select :model-value="model" class="min-w-[168px]" :options="OPTIONS" :full-width-trigger="true" @update:model-value="onUpdate">
        <template #trigger-content>
            <img :src="selected.icon" :alt="selected.label" class="mr-2 h-5 w-5 rounded-full object-contain" />
        </template>
    </Select>
</template>
