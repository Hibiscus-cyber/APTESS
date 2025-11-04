<script setup>
import { ref, inject, onMounted , watch} from "vue";
import { storeToRefs } from "pinia";

import { useAdversaryStore } from "@/stores/adversaryStore.js";
import GoalsTable from "@/components/objectives/GoalsTable.vue";

const $api = inject("$api");

const adversaryStore = useAdversaryStore();
const { objectives, selectedObjective } = storeToRefs(adversaryStore);

const tabNameMapN = {
  "New objective": "新目标",
};
  

const tabNameMapD = {
  "Enter a description": "输入一段描述", 
};

watch(objectives, (newVal) => {
  if (newVal.length > 0 && !selectedObjective.value) {
    selectedObjective.value = newVal[0];   // 注意这里是整个对象
  }
});

let isEditingNameDesc = ref(false);
let newObjectiveName = ref("");
let newObjectiveDescription = ref("");

onMounted(async () => {
    await adversaryStore.getObjectives($api);
});

function editNameDesc() {
    newObjectiveName.value = selectedObjective.value.name;
    newObjectiveDescription.value = selectedObjective.value.description;
    isEditingNameDesc.value = true;
}

async function saveObjective() {
    selectedObjective.value.name = newObjectiveName.value;
    selectedObjective.value.description = newObjectiveDescription.value;
    await adversaryStore.saveObjective($api);
    isEditingNameDesc.value = false;
}
</script>

<template lang="pug">
.columns.mb-0
    .column.is-4.m-0.content
        h2.m-0 目标
    .column.is-4.m-0
        .is-flex.is-justify-content-center.is-flex-wrap-wrap
            .control.mr-2
                .select
                    select.has-text-centered(v-model="selectedObjective")
                        option(disabled selected value="") 选择目标 
                        option(v-for="objective in objectives" :value="objective") {{ objective.name }}
            button.button.is-primary.mr-2(type="button" @click="adversaryStore.createObjective($api)") 
                span.icon
                    font-awesome-icon(icon="fas fa-plus") 
                span 新建目标
    .column.is-4.m-0
hr.mt-2

.content(v-if="selectedObjective.id")
    div(v-if="!isEditingNameDesc")
        .is-flex
            h3 {{ tabNameMapN[selectedObjective.name] || selectedObjective.name }}
            button.button.ml-3(@click="editNameDesc()")
                span.icon
                    font-awesome-icon(icon="fas fa-pencil-alt")
                span 编辑
        p {{ tabNameMapD[selectedObjective.description] || selectedObjective.description }}
    div(v-else)
        .field
            .control
                input.input(type="text" v-model="newObjectiveName" placeholder="请输入目标名称")
        .field
            .control
                textarea.textarea(type="text" v-model="newObjectiveDescription" placeholder="请输入目标描述")
        .buttons
            button.button.is-primary.mr-2(@click="saveObjective()") 保存
            button.button.mr-2(@click="isEditingNameDesc = false") 取消

    .mt-5
        GoalsTable
</template>

