<script setup>
import { inject } from "vue";
import { storeToRefs } from "pinia";

import { useCoreDisplayStore } from "../../stores/coreDisplayStore";
import { useOperationStore } from '../../stores/operationStore';

const $api = inject("$api");

const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const operationStore = useOperationStore();

async function deleteOperation() {
    await operationStore.deleteOperation($api, operationStore.selectedOperationID);
    modals.value.operations.showDelete = false;
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.operations.showDelete }")
    .modal-background(@click="modals.operations.showDelete = false")
    .modal-card
        header.modal-card-head 
            p.modal-card-title 删除行动？
        .modal-card-body(v-if="operationStore.currentOperation")
            p 您确定要删除行动 "{{ operationStore.currentOperation.name }}" 吗？此操作无法撤销。
        footer.modal-card-foot.has-text-right
            button.button(@click="modals.operations.showDelete = false") 取消 
            button.button.is-danger(@click="deleteOperation()") 
                span.icon
                    font-awesome-icon(icon="fa-trash")
                span 删除
</template>


<style scoped>
.modal-card-foot {
    display: block;
}
</style>
