<script setup>
import { ref, inject, onMounted } from "vue";
import { storeToRefs } from "pinia";
import { toast } from 'bulma-toast'

import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import { useOperationStore } from '@/stores/operationStore';
import { useAdversaryStore } from "@/stores/adversaryStore";
import { useCoreStore } from "@/stores/coreStore";
import { useAgentStore } from "@/stores/agentStore";
import { useSourceStore } from "@/stores/sourceStore";

const $api = inject("$api");

const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const adversaryStore = useAdversaryStore();
const operationStore = useOperationStore();
const coreStore = useCoreStore();
const agentStore = useAgentStore();
const sourceStore = useSourceStore();
const { sources } = storeToRefs(sourceStore);

const props = defineProps({
    selectInterval: {
        type: Function,
    },
});

let operationName = ref("");
let selectedAdversary = ref("");
let selectedSource = ref("")
let selectedGroup = ref("");
let selectedAgentIds = ref([]);
let selectedObfuscator = ref({ name: "plain-text" });
let selectedPlanner = ref();
let isAuto = ref(true);
let isDefParser = ref(true);
let isAutoClose = ref(false);
let isPause = ref(false);
let minJitter = ref(2);
let maxJitter = ref(8);
let visibility = ref(51);
let validation = ref({
    name: "",
});

onMounted(async () => {
    await agentStore.getAgents($api);
    agentStore.updateAgentGroups();
    await adversaryStore.getAdversaries($api);
    await getSources();
    await coreStore.getObfuscators($api);
    await getPlanners();
});

async function getSources() {
    try {
        await sourceStore.getSources($api);
        selectedSource.value = sources.value.find(source => source.name === "basic");
    } catch(error) {
        console.error("Error getting sources", error);
    }
}

async function getPlanners() {
    try {
        await coreStore.getPlanners($api);
        selectedPlanner.value = coreStore.planners[0];
    } catch(error) {
        console.error("Error getting planners", error);
    }
}

async function createOperation() {
    if(!operationName.value){
        validation.value.name = "名称不能为空";
        return;
    }
    validation.value.name = "";
    if(!selectedAdversary.value.adversary_id){
        selectedAdversary.value = {adversary_id: "ad-hoc"};
    }
    const newOperation = {
        name: operationName.value,
        autonomous: Number(isAuto.value),
        use_learning_parsers: isDefParser.value,
        auto_close: isAutoClose.value,
        jitter: `${minJitter.value}/${maxJitter.value}`,
        state: isPause ? "running" : "paused",
        visibility: visibility.value,
        obfuscator: selectedObfuscator.value.name,
        source: {id: JSON.parse(JSON.stringify(selectedSource.value.id))},
        planner: {id: JSON.parse(JSON.stringify(selectedPlanner.value.id))},
        adversary: {adversary_id: JSON.parse(JSON.stringify(selectedAdversary.value.adversary_id))},
        group: selectedGroup.value,
        agent_ids: selectedAgentIds.value,
    };
    try {
        await operationStore.createOperation($api, newOperation);
        props.selectInterval();
        toast({
            message: `操作 ${operationName.value} 已创建`,
            type: 'is-success',
            dismissible: true,
            pauseOnHover: true,
            duration: 2000,
            position: "bottom-right",
        });
    } catch(error) {
        console.error("Error creating operation", error);
        toast({
            message: `创建操作时出错`,
            type: 'is-danger',
            dismissible: true,
            pauseOnHover: true,
            duration: 2000,
            position: "bottom-right",
        });
    }
    modals.value.operations.showCreate = false
}

</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.operations.showCreate }")
    .modal-background(@click="modals.operations.showCreate = false")
    .modal-card
        header.modal-card-head 
            p.modal-card-title 开始新操作
        .modal-card-body
            .field.is-horizontal
                .field-label.is-normal 
                    label.label 操作名称
                .field-body 
                    input.input(placeholder="操作名称" v-model="operationName")
                    label.label.ml-3.mt-1.has-text-danger {{ `${validation.name}` }}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label 敌手
                .field-body
                    .control
                        .select
                            select(v-model="selectedAdversary")
                                option(selected value="") 无敌手（手动）
                                option(v-for="adversary in adversaryStore.adversaries" :key="adversary.id" :value="adversary") {{ `${adversary.name}` }}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label 事实源
                .field-body
                    .control
                        .select
                            select(v-model="selectedSource")
                                option(disabled selected value="") 选择事实源 
                                option(v-for="source in sources" :key="source.id" :value="source") {{ `${source.name}` }}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label 代理选择
                .field-body
                    .field.is-grouped
                        button.button(:class="{ 'is-primary': selectedGroup === '' }" @click="selectedGroup = ''; selectedAgentIds = []") 所有组
                        button.button.mx-2(v-for="group in agentStore.agentGroups" :key="group" :class="{ 'is-primary': selectedGroup === group }", @click="selectedGroup = group; selectedAgentIds = []") {{`${group}`}}
                        button.button.is-info(@click="selectedGroup = 'custom'; selectedAgentIds = []") 自定义选择
            .field.is-horizontal(v-if="selectedGroup === 'custom'")
                .field-label.is-normal 
                    label.label 选择代理
                .field-body
                    .field.is-grouped-multiline
                        .control(v-for="agent in agentStore.agents" :key="agent.paw")
                            label.checkbox.mr-3
                                input(type="checkbox" :value="agent.paw" v-model="selectedAgentIds")
                                span.ml-2 {{ agent.paw }} ({{ agent.platform }}) - {{ agent.host }}
            .field.is-horizontal
                .field-label.is-normal 
                    label.label 规划器 
                .field-body
                    .control
                        .select 
                            select(v-model="selectedPlanner")
                                option(v-for="planner in coreStore.planners" :key="planner.id" :value="planner") {{ `${planner.name}` }}
            .field.is-horizontal
                .field-label
                    label.label 混淆器 
                .field-body
                    .field.is-grouped-multiline
                        button.button.my-1.mr-2(v-for="obf in coreStore.obfuscators" :key="obf.id" :value="obf" :class="{ 'is-primary': selectedObfuscator.name === obf.name }" @click="selectedObfuscator = obf") {{ `${obf.name}` }}
            .field.is-horizontal
                .field-label
                    label.label 自主运行
                .field-body
                    .field.is-grouped
                        input.is-checkradio(type="radio" id="auto" :checked="isAuto" @click="isAuto = true")
                        label.label.ml-3.mt-1(for="auto") 自主运行
                        input.is-checkradio.ml-3(type="radio" id="manual" :checked="!isAuto" @click="isAuto = false")
                        label.label.ml-3.mt-1(for="manual") 需要手动批准
            .field.is-horizontal
                .field-label
                    label.label 解析器
                .field-body
                    .field.is-grouped 
                        input.is-checkradio(type="radio" id="defaultparser" :checked="isDefParser" @click="isDefParser = true")
                        label.label.ml-3.mt-1(for="defaultparser") 使用默认解析器
                        input.is-checkradio.ml-3(type="radio" id="nondefaultparser" :checked="!isDefParser" @click="isDefParser = false")
                        label.label.ml-3.mt-1(for="nondefaultparser") 不使用默认学习解析器
            .field.is-horizontal
                .field-label 
                    label.label 自动关闭
                .field-body.is-grouped
                    input.is-checkradio(type="radio" id="keepopen" :checked="!isAutoClose" @click="isAutoClose = false")
                    label.label.ml-3.mt-1(for="keepopen") 永远保持打开
                    input.is-checkradio.ml-3(type="radio" id="autoclose" :checked="isAutoClose" @click="isAutoClose = true")
                    label.label.ml-3.mt-1(for="autoclose") 自动关闭操作
            .field.is-horizontal 
                .field-label 
                    label.label 运行状态 
                .field-body.is-grouped
                    input.is-checkradio(type="radio" id="runimmediately" :checked="!isPause" @click="isPause = false")
                    label.label.ml-3.mt-1(for="runimmediately") 立即运行
                    input.is-checkradio.ml-3(type="radio" id="pausestart" :checked="isPause" @click="isPause = true")
                    label.label.ml-3.mt-1(for="pausestart") 启动时暂停
            .field.is-horizontal
                .field-label 
                    label.label 抖动（秒/秒）
                .field-body
                    input.input.is-small(v-model="minJitter")
                    span /
                    input.input.is-small(v-model="maxJitter")
        footer.modal-card-foot.is-justify-content-right
            button.button(@click="modals.operations.showCreate = false") 取消
            button.button.is-primary(@click="createOperation()") 开始 
</template>

<style scoped>
.modal-card {
    width: 800px;
}

.field-label label{
    font-size: 0.9rem;
}
</style>
