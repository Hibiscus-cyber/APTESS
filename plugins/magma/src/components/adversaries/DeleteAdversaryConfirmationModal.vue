<script setup>
import { ref, inject } from "vue";
import { useCoreDisplayStore } from "../../stores/coreDisplayStore";
import { storeToRefs } from "pinia";
import { useAdversaryStore } from "../../stores/adversaryStore";

const $api = inject("$api");

const adversaryStore = useAdversaryStore();
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.adversaries.showDeleteConfirm }")
    .modal-background(@click="modals.adversaries.showDeleteConfirm = false")
    .modal-card 
        header.modal-card-head 
            p.modal-card-title 删除对手
        .modal-card-body 
            br
            p.block 确定要删除此对手吗？该操作无法撤销。
            br

        footer.modal-card-foot.is-flex.is-justify-content-flex-end 
            button.button(@click="modals.adversaries.showDeleteConfirm = false") 取消
            button.button.is-danger(@click="adversaryStore.deleteAdversary($api) && (modals.adversaries.showDeleteConfirm = false)")
                span.icon
                    font-awesome-icon(icon="fas fa-trash")
                span 删除
</template>
