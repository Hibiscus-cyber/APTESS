<script setup>
import { storeToRefs } from "pinia";
import { inject, onMounted } from "vue";
import { useCoreStore } from "../stores/coreStore";

const coreStore = useCoreStore();
const { planners } = storeToRefs(coreStore);

const $api = inject("$api");

onMounted(async () => {
    await coreStore.getPlanners($api);
});
</script>

<template lang="pug">
.content
    h2 策略规划器
    p 策略规划器是一个模块，用于定义运行中的行动应如何决策——
        | 包括选择哪些能力以及执行顺序。
        | 具体而言，规划器的逻辑负责决定如何执行行动的单个阶段。
hr

.is-flex.is-justify-content-center
    #planners.content
        .card.block.p-4(v-for="planner in planners")
            h3 {{ planner.name }}
            p {{ planner.description }}
</template>


<style scoped>
#planners {
    max-width: 800px;
}
</style>
