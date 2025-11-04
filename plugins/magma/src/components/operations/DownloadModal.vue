<script setup>
import { inject, ref } from "vue";
import { storeToRefs } from "pinia";
import { useCoreDisplayStore } from "../../stores/coreDisplayStore";
import { useOperationStore } from "../../stores/operationStore";
const $api = inject("$api");
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const operationStore = useOperationStore();
let reportType = ref(1);
let isAgentOutput = ref(false);

async function downloadOperation() {
  await operationStore.downloadOperationInfo(
    $api,
    reportType.value,
    operationStore.selectedOperationID,
    isAgentOutput.value
  );
  modals.value.operations.showDownload = false;
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.operations.showDownload }")
    .modal-background(@click="modals.operations.showDownload = false")
    .modal-card
        header.modal-card-head 
            p.modal-card-title 行动报告
        .modal-card-body
            form(@submit.prevent)
                .field.is-horizontal 
                    label.label.checkbox
                        input(type="checkbox" v-model="isAgentOutput")
                        span.ml-2 包含代理输出
                .field.is-horizontal
                    input.is-checkradio(:checked="reportType == 0 ? true : false" type="radio" id="full" @click="reportType = 0")
                    label.label.ml-3.mt-1(for="full") 完整报告
                    input.is-checkradio.ml-3(:checked="reportType == 1 ? true : false" type="radio" id="event" @click="reportType = 1")
                    label.label.ml-3.mt-1(for="event") 事件日志
                    input.is-checkradio.ml-3(:checked="reportType == 2 ? true : false" type="radio" id="csv" @click="reportType = 2")
                    label.label.ml-3.mt-1(for="csv") CSV 格式
        footer.modal-card-foot.has-text-right
            button.button(@click="modals.operations.showDownload = false") 取消
            button.button.is-primary(@click="downloadOperation()") 
                span.icon
                    font-awesome-icon(icon="fa-download")
                span 下载
</template>


<style scoped>
.modal-card-foot {
  display: block;
}
</style>
