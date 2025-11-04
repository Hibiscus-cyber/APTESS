<script setup>
import { ref, inject, onMounted , watch} from "vue";
import { storeToRefs } from "pinia";

import { useSourceStore } from "@/stores/sourceStore.js";
import FactTable from "@/components/sources/FactTable.vue";
import RelationshipTable from "@/components/sources/RelationshipTable.vue";
import RuleTable from "@/components/sources/RuleTable.vue";

const $api = inject("$api");

const sourceStore = useSourceStore();
const { sources, selectedSource } = storeToRefs(sourceStore);

watch(sources, (newVal) => {
  if (newVal.length > 0 && !selectedSource.value) {
    selectedSource.value = newVal[0];   // 注意这里是整个对象
  }
});

let isEditingName = ref(false);
let newSourceName = ref("");

onMounted(() => {
  sourceStore.getSources($api);
});

function saveSource() {
  selectedSource.value.name = newSourceName.value;
  sourceStore.saveSource($api, selectedSource);
  isEditingName.value = false;
}

async function createSource(duplicate) {
  const newSource = await sourceStore.createSource($api, duplicate);
  selectedSource.value = newSource;
}

async function deleteSource() {
  await sourceStore.deleteSource($api);
  selectedSource.value = {};
}

function downloadSource() {
  $api.get(`/api/v2/sources/${selectedSource.value.id}`)
    .then((res) => {
      const dataURL = `data:text/json;charset=utf-8,${encodeURIComponent(
        JSON.stringify(res, null, 2)
      )}`;
      const fileName = `${selectedSource.value.name}.json`;
      const elem = document.createElement("a");
      elem.setAttribute("href", dataURL);
      elem.setAttribute("download", fileName);
      elem.click();
      elem.remove();
    })
    .catch((error) => {
      console.error(error);
    });
}
</script>

<template lang="pug">
//- Header
.columns.mb-0
    .column.is-4.m-0.content
        h2.m-0 Fact源
    .column.is-4.m-0
        .is-flex.is-justify-content-center.is-flex-wrap-wrap
            .control.mr-2
                .select
                    select.has-text-centered(v-model="selectedSource")
                        option(disabled selected value="") New Source
                        option(v-for="source in sources" :value="source") {{ source.name }}
            button.button.is-primary.mr-2(type="button" @click="createSource(false)") 
                span.icon
                    font-awesome-icon(icon="fas fa-plus") 
                span 新建来源
    .column.is-4.m-0
        .buttons.is-justify-content-right(v-if="selectedSource.id")
            button.button.mr-2(@click="downloadSource" type="button")
                span.icon
                    font-awesome-icon(icon="fas fa-save")
                span 下载报告
            button.button.mr-2(type="button" @click="createSource(true)")
                span.icon
                    font-awesome-icon(icon="far fa-copy")
                span 复制来源
            button.button.is-danger.is-outlined(type="button" @click="deleteSource()")
                span.icon
                    font-awesome-icon(icon="fas fa-trash")
                span 删除来源
hr.mt-2

.content(v-if="selectedSource.id")
    .is-flex(v-if="!isEditingName")
        h3 {{ selectedSource.name }}
        button.button.ml-3(@click="newSourceName = selectedSource.name; isEditingName = true;")
            span.icon
                font-awesome-icon(icon="fas fa-pencil-alt")
            span 重命名
    .is-flex(v-else)
        .field.mr-2
            .control
                input.input(type="text" v-model="newSourceName" placeholder="输入新的来源名称")
        button.button.is-primary.mr-2(@click="saveSource()") 保存
        button.button.mr-2(@click="isEditingName = false") 取消

    .tile.is-ancestor.is-flex-wrap-wrap
        .tile.is-parent
            article.tile.is-child
                .box.content
                    h3 Facts
                    FactTable
        .tile.is-parent
            article.tile.is-child
                .box.content
                    h3 规则
                    RuleTable
        .tile.is-parent
            article.tile.is-child
                .box.content
                    h3 关系
                    RelationshipTable
</template>

