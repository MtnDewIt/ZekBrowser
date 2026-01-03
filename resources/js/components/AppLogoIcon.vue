<script setup lang="ts">

import type { HTMLAttributes } from 'vue';

defineOptions({
    inheritAttrs: false,
});

interface Props 
{
    className?: HTMLAttributes['class'];
}

defineProps<Props>();

</script>

<template>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2493 2142.02" :class="className" v-bind="$attrs">
        <path fill="currentColor" d="M1246.52,0c-49.51,84.01-99.01,168.01-148.52,252.02l936,1629h-729l-144,261h1332C2077.51,1428.01,1662.01,714.01,1246.52,0Z"/>
        <path fill="currentColor" d="M603,1611.02h954L945,522.02,0,2142.02h846l135-261H459l144-270ZM954,1026.02l189,342h-378l189-342Z"/>
    </svg>
</template>
