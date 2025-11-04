<script setup>
import { ref, inject, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { useCoreDisplayStore } from "../../stores/coreDisplayStore";
import { useOperationStore } from '../../stores/operationStore';
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const operationStore = useOperationStore();
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.operations.showDetails }")
    .modal-background(@click="modals.operations.showDetails = false")
    .modal-card
        header.modal-card-head 
            p.modal-card-title 行动详情
        .modal-card-body(v-if="operationStore.selectedOperationID")
            table.table.is-fullwidth.is-striped
                tbody
                    tr
                        th 名称
                        td {{`${operationStore.operations[operationStore.selectedOperationID].name}`}}
                    tr
                        th 对手
                        td {{`${operationStore.operations[operationStore.selectedOperationID].adversary.name}`}}
                    tr
                        th 知识源
                        td {{`${operationStore.operations[operationStore.selectedOperationID].source.name}`}}
                    tr
                        th 分组
                        td {{operationStore.operations[operationStore.selectedOperationID].group || "全部"}}
                    tr
                        th 策划器
                        td {{`${operationStore.operations[operationStore.selectedOperationID].planner.name}`}}
                    tr
                        th 混淆器
                        td {{`${operationStore.operations[operationStore.selectedOperationID].obfuscator}`}}
                    tr
                        th 执行模式
                        td {{operationStore.operations[operationStore.selectedOperationID].autonomous ? "自动" : "手动"}}
                    tr
                        th 解析器学习
                        td {{`${operationStore.operations[operationStore.selectedOperationID].use_learning_parsers}`}}
                    tr
                        th 自动结束
                        td {{`${operationStore.operations[operationStore.selectedOperationID].auto_close}`}}
                    tr
                        th 抖动间隔（Jitter）
                        td {{`${operationStore.operations[operationStore.selectedOperationID].jitter}`}}
        footer.modal-card-foot.is-justify-content-right
            button.button(@click="modals.operations.showDetails = false") 关闭 
</template>

