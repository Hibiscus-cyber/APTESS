<script setup>
import { ref, reactive, computed, inject, onMounted } from 'vue';
import { storeToRefs } from "pinia";

import { useAbilityStore } from "@/stores/abilityStore";
import CreateEditAbility from "@/components/abilities/CreateEditAbility.vue";
import AutoSuggest from "@/components/core/AutoSuggest.vue";

const props = defineProps({ 
    active: Boolean,
    canCreate: Boolean
});
const emit = defineEmits(['select', 'close']);

const $api = inject("$api");

const abilityStore = useAbilityStore();
const { abilities, tactics, techniqueIds, techniqueNames } = storeToRefs(abilityStore);

let filters = reactive({
    searchQuery: "",
    tactic: "",
    techniqueId: "",
    techniqueName: ""
});
let showFilters = ref(false);
let showCreateAbilityModal = ref(false);

const filteredAbilities = computed(() => {
    return abilities.value.filter((ability) => (
        ability.name.toLowerCase().includes(filters.searchQuery.toLowerCase()) &&
        ability.tactic.toLowerCase().includes(filters.tactic.toLowerCase()) &&
        ability.technique_id.toLowerCase().includes(filters.techniqueId.toLowerCase()) &&
        ability.technique_name.toLowerCase().includes(filters.techniqueName.toLowerCase())
    ));
});

const hasFiltersApplied = computed(() => {
    return filters.searchQuery || filters.tactic || filters.techniqueId || filters.techniqueName;
});

onMounted(async () => {
    await abilityStore.getAbilities($api);
});

function clearFilters() {
    filters.searchQuery = "";
    filters.tactic = "";
    filters.techniqueId = "";
    filters.techniqueName = "";
}

function createAbility() {
    showCreateAbilityModal.value = true;
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': props.active }")
    .modal-background(@click="emit('close')")
    .modal-card
        header.modal-card-head
            p.modal-card-title 选择能力
        .modal-card-body
            form
                .field
                    .control.has-icons-left
                        input.input(v-model="filters.searchQuery" type="text" placeholder="搜索能力…")
                        span.icon.is-left
                            font-awesome-icon(icon="fas fa-search")
                .field(v-if="showFilters")
                    label.label 策略
                    .control
                        AutoSuggest(v-model="filters.tactic" :items="tactics" placeholder="策略")
                .field(v-if="showFilters")
                    label.label 技术编号
                    .control
                        AutoSuggest(v-model="filters.techniqueId" :items="techniqueIds" placeholder="技术编号")
                .field(v-if="showFilters")
                    label.label 技术名称
                    .control
                        AutoSuggest(v-model="filters.techniqueName" :items="techniqueNames" placeholder="技术名称")
            .is-flex.is-justify-content-space-between.mt-2
                a(@click="showFilters = !showFilters") {{ showFilters ? "隐藏" : "显示" }} 筛选
                a(v-if="hasFiltersApplied" @click="clearFilters()") 清除筛选
            hr.mt-3
            .card.p-3.mb-2.pointer(v-for="ability in filteredAbilities" @click="emit('select', ability)")
                .is-flex.is-justify-content-space-between.is-align-items-center
                    span.tag.is-small {{ ability.tactic }} 
                    p.help.mt-0 {{ ability.technique_id }} - {{ ability.technique_name }}
                p.mt-1 {{ ability.name }}
                p.help {{ ability.description }}
        footer.modal-card-foot.is-flex.is-justify-content-space-between
            button.button(v-if="props.canCreate" @click="createAbility()")
                span.icon
                    font-awesome-icon(icon="fas fa-plus")
                span 新建能力
            button.button(@click="emit('close')") 关闭

//- Modals
CreateEditAbility(v-if="props.canCreate" :ability="{}" :active="showCreateAbilityModal" :creating="true" @close="showCreateAbilityModal = false")
</template>


<style scoped>
.card {
    border: 1px solid transparent;
    user-select: none;
}
.card:hover {
    border: 1px solid white;
}

.modal-card {
    width: 800px;
}
</style> 
    
