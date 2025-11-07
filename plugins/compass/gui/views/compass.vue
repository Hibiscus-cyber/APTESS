<script setup>
import { ref, onMounted, inject, reactive } from "vue";
import { useAdversaryStore } from "@/stores/adversaryStore.js";
import { storeToRefs } from "pinia";

const $api = inject("$api");
const selectedAdversaryID = ref("");
const openModal = ref(false);
const adversaryCreated = reactive({
  name: "",
  response: "",
  unmatched_techniques: [],
});
const adversaryStore = useAdversaryStore();

const { adversaries } = storeToRefs(adversaryStore);
onMounted(async () => {
  await adversaryStore.getAdversaries($api);
});

function downloadObjectAsJson(data) {
  let exportName = "layer";
  let dataStr = `data:text/json;charset=utf-8,${encodeURIComponent(
    JSON.stringify(data, null, 2)
  )}`;
  let downloadAnchorNode = document.createElement("a");
  downloadAnchorNode.setAttribute("href", dataStr);
  downloadAnchorNode.setAttribute("download", `${exportName}.json`);
  document.body.appendChild(downloadAnchorNode); // required for firefox
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
}
const generateLayer = async () => {
  const payload = selectedAdversaryID.value
    ? {
        index: "adversary",
        adversary_id: selectedAdversaryID.value,
      }
    : { index: "all" };
  try {
    const res = await $api.post("/plugin/compass/layer", payload);
    downloadObjectAsJson(res.data);
  } catch (err) {
    console.error(err);
  }
};

const uploadAdversaryLayer = async (e) => {
  if (!e || !e.files || !e.files[0].name)
    toast("Error loading layer file", false);

  let formData = new FormData();
  formData.append("file", e.files[0]);
  try {
    const res = await $api.post("/plugin/compass/adversary", formData);
    const data = res.data;
    adversaryCreated.name = data.name;
    adversaryCreated.response = data.description;
    adversaryCreated.unmatched_techniques = data.unmatched_techniques.map(
      (item) => {
        return { technique_id: item.technique_id, tactic: item.tactic };
      }
    );
    openModal.value = true;
  } catch (error) {
    console.error(error);
  }
};
</script>

<template lang="pug">

.content
  h2 指南针
p
  | 为任意对手生成一个图层文件，可叠加到下方矩阵中 
  b 或 
  | 直接在矩阵中创建一个对手，然后上传该图层文件以生成可在行动中使用的对手
hr
.content
  .is-flex.is-flex-direction-row.mb-4
    .is-flex.is-flex-direction-column
      label.pb-2.is-size-6(for="layer-selection-adversary") 生成图层文件
      .is-flex.is-flex-direction-row
        .field.has-addons
          .control
            #layerSelectionAdversary.select.is-small
              select#layer-selection-adversary(v-model="selectedAdversaryID")
                option(value="", selected) 选择一个对手（全部）
                option(v-for="adv in adversaries", :value="adv.adversary_id") {{ adv.name }}
          .control
            label(for="generateLayer")
              button#generateLayer.button.is-primary.is-small(type="button", @click="generateLayer")
                i.pr-1.fas.fa-download
                span.has-tooltip-multiline.has-tooltip-bottom(v-tooltip="'在 Navigator 中选择 Open Existing Layer -> Upload from local -> 上传生成的图层文件。'") 生成图层
    .is-flex.is-flex-direction-column.ml-6
      label.pb-2.is-size-6 生成对手
      .is-flex.is-flex-direction-row
        input#generateAdversary(type="file", @change="uploadAdversaryLayer($event.target)", hidden)
        button.button.is-primary.is-small(for="generateAdversary")
          i.pr-1.fas.fa-upload
          span.has-tooltip-multiline.has-tooltip-bottom(v-tooltip="'在下方 ATT&CK 矩阵中选择技术 -> 下载为 JSON 图层 -> 上传该对手图层文件。现在你可以在 Caldera 中使用此对手配置，名称即为该图层文件名。'")
            label(for="generateAdversary") 创建行动
        input#adversaryLayerInput(type="file", hidden)
div
  iframe.frame(src="https://mitre-attack.github.io/attack-navigator/enterprise/")
template(v-if="openModal")
  .modal.is-active
    .modal-background(@click="openModal = false")
    .modal-card
      header.modal-card-head
        p.modal-card-title 对手已创建
        h3() {{ adversaryCreated.name}}
        h3(x-text="adversaryCreated.response") {{adversaryCreated.response}}
      section.modal-card-body
        div
          table.table.is-striped
            thead
              tr
                th#missing-abilities-tactic.has-text-grey 策略
                th#missing-abilities-technique.has-text-grey 技术 ID
            tbody#missing-abilities-body
              // Pug iteration for unmatched techniques
              template(v-for="(index, item) in adversaryCreated.unmatched_techniques", :key="index")
                tr
                td {{item.tactic}}
                td {{item.technique_id}}
          p.has-text-centered 对手的强大取决于其能力。APT 图层会涵盖相同的策略与技术。准确反映 APT 行为的过程来源于合理策划与构建。
      footer.modal-card-foot
        nav.level
          .level-left
          .level-right
            .level-item
              button.button.is-small(@click="openModal = false") 关闭
</template>


<style scoped>
.frame {
  display: flex;
  width: 100%;
  border-radius: 5px;
  overflow: auto;
  height: 900px;
  border: 2px solid #666666;
}
</style>
