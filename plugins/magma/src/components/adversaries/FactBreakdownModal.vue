<script setup>
import { useCoreDisplayStore } from "../../stores/coreDisplayStore";
import { storeToRefs } from "pinia";

const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);

const props = defineProps(['breakdown']);
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.adversaries.showFactBreakdown }")
    .modal-background(@click="modals.adversaries.showFactBreakdown = false")
    .modal-card 
        header.modal-card-head 
            p.modal-card-title 事实分解（Fact Breakdown）
        .modal-card-body 
            p.help.tags.mb-1.has-text-centered
                span.tag.is-success 已收集且为必需项
                span.tag.is-warning 未收集但为必需项
                span.tag.is-black 已收集但非必需项
            hr.mt-2
            .tags(v-if="breakdown.length")
                span.tag(
                    v-for="fact in breakdown"
                    :class="{ 'is-warning': fact.type === 'unmet', 'is-success': fact.type === 'met', 'is-black': fact.type === 'extra' }"
                )
                    span.icon
                        font-awesome-icon(v-if="fact.type === 'unmet'" icon="fas fa-exclamation-triangle")
                        font-awesome-icon(v-if="fact.type === 'met'" icon="fas fa-check")
                        font-awesome-icon(v-if="fact.type === 'extra'" icon="fas fa-minus")
                    span {{ fact.fact }}
            p(v-else) 暂无可显示的事实
        footer.modal-card-foot.is-flex.is-justify-content-flex-end 
            button.button(@click="modals.adversaries.showFactBreakdown = false") 关闭
</template>

