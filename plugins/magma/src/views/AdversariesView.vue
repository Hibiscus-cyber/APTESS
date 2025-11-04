<script setup>
import { inject, reactive, ref, onMounted, computed } from "vue";
import { storeToRefs } from "pinia";

import { useAdversaryStore } from "@/stores/adversaryStore";
import { useAbilityStore } from "@/stores/abilityStore";
import { useObjectiveStore } from "@/stores/objectiveStore";
import DetailsTable from "@/components/adversaries/DetailsTable.vue";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import ImportModal from "@/components/adversaries/ImportModal.vue";

const $api = inject("$api");

const adversaryStore = useAdversaryStore();
const { adversaries, selectedAdversary } = storeToRefs(adversaryStore);
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const abilityStore = useAbilityStore();
const objectiveStore = useObjectiveStore();

let isAdversaryDropdownOpen = ref(false);
let adversarySearchQuery = ref("");

let filteredAdversaries = computed(() => {
    return adversaries.value.filter((adversary) => adversary.name.toLowerCase().includes(adversarySearchQuery.value.toLowerCase()));
});

onMounted(async () => {
    await abilityStore.getAbilities($api);
    await adversaryStore.getAdversaries($api);
    await objectiveStore.getObjectives($api);
});

function selectAdversary(adversary) {
    selectedAdversary.value = adversary; 
    adversaryStore.updateSelectedAdversaryAbilities();
    isAdversaryDropdownOpen.value = false;
    adversarySearchQuery.value = "";
}
</script>

<template lang="pug">
//- Header
.content
    h2 对手档案
    p 对手档案是由 ATT&CK TTPs（战术、技术与程序）组成的集合，用于在主机或网络上产生特定效果。档案可用于进攻性或防御性场景。
hr

//- Adversary Selection
#select-adversary.is-flex.is-align-items-center.mb-4
    .dropdown.searchable.is-flex-grow-1.mr-2(:class="{ 'is-active': isAdversaryDropdownOpen }" @mouseenter="isAdversaryDropdownOpen = true" @mouseleave="isAdversaryDropdownOpen = false")
        .dropdown-trigger
            button.button.is-fullwidth(type="button" aria-haspopup="true" aria-controls="dropdown-menu")
                span {{ selectedAdversary.name || '选择一个对手档案' }} 
                span.icon.is-small
                    font-awesome-icon(icon="fas fa-angle-down" aria-hidden="true")
        .dropdown-menu.is-fullwidth(role="menu")
            .dropdown-content
                .dropdown-item 
                    input.input(v-model="adversarySearchQuery" placeholder="搜索对手档案…")
                .dropdown-divider
                a.dropdown-item(v-for="adversary in filteredAdversaries" @click="selectAdversary(adversary)" :class="{ 'is-active': adversary.adversary_id === selectedAdversary.adversary_id }") {{ adversary.name }}
                p.has-text-centered(v-if="!filteredAdversaries.length") 无搜索结果
    button.button.is-primary.mr-2(type="button" @click="adversaryStore.createAdversary($api)")
        span.icon 
            font-awesome-icon(icon="fas fa-plus") 
        span 新建档案
    button.button.mr-2(type="button" @click="modals.adversaries.showImport = true")
        span.icon
            font-awesome-icon(icon="fas fa-file-import") 
        span 导入

//- Adversary details table
DetailsTable(v-if="selectedAdversary.adversary_id")

//- Modals
ImportModal
</template>

<style scoped>
#select-adversary {
    max-width: 800px;
    margin: 0 auto;
}
</style>
