<script setup>
import { inject, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";
import { useAbilityStore } from '@/stores/abilityStore.js';
import { useAdversaryStore } from '@/stores/adversaryStore.js';

const $api = inject("$api");

const abilityStore = useAbilityStore();
const { abilities } = storeToRefs(abilityStore);
const adversaryStore = useAdversaryStore();
const { adversaries } = storeToRefs(adversaryStore);

onMounted(async () => {
    await abilityStore.getAbilities($api);
    await adversaryStore.getAdversaries($api);
});

const stockpileAbilities = computed(() => abilities.value.filter((ability) => ability.plugin === "stockpile"));
const stockpileAdversaries = computed(() => adversaries.value.filter((adversary) => adversary.plugin === "stockpile"));
</script>

<template lang="pug">
.content    
    h2 库存库（Stockpile）
    p Stockpile 插件包含一系列 TTP（能力）、对手画像、数据源和规划器。这些资源可用于针对目标主机构建动态作战行动。
hr

.is-flex.is-align-items-center.is-justify-content-center
    .card.is-flex.is-flex-direction-column.is-align-items-center.p-4.m-4
        h1.is-size-1.mb-0 {{ stockpileAbilities.length || "---" }}
        p 能力
        router-link.button.is-primary.mt-4(to="/abilities?plugin=stockpile") 
            span 查看能力
            span.icon
                font-awesome-icon(icon="fas fa-angle-right")
    .card.is-flex.is-flex-direction-column.is-align-items-center.p-4.m-4
        h1.is-size-1.mb-0 {{ stockpileAdversaries.length || "---" }}
        p 对手
        router-link.button.is-primary.mt-4(to="/adversaries") 
            span 查看对手
            span.icon
                font-awesome-icon(icon="fas fa-angle-right")
</template>
