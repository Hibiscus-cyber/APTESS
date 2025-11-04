<script setup>
import { storeToRefs } from "pinia";
import { inject, onMounted } from "vue";
import { useCoreStore } from "../stores/coreStore";

const coreStore = useCoreStore();
const { obfuscators } = storeToRefs(coreStore);

const $api = inject("$api");

onMounted(async () => {
    await coreStore.getObfuscators($api);
});
</script>

<template lang="pug">
.content
    h2 混淆器
    p 混淆器用于规避检测。在执行行动时，您可以选择一种混淆器。默认情况下会选择纯文本模式。
        | 在行动过程中，在代理获取指令之前，服务器会使用所选混淆技术对指令进行封装，
        | 并附带如何在执行前解包的说明。
hr

.is-flex.is-justify-content-center
    #obfuscators.content
        .card.block.p-4(v-for="obfuscator in obfuscators")
            h3 {{ obfuscator.name }}
            p {{ obfuscator.description }}
</template>

<style scoped>
#obfuscators {
    max-width: 800px;
}
</style>
