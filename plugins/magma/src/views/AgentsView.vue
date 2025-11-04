<script setup>
import { inject, onMounted, onBeforeUnmount, ref } from "vue";
import { storeToRefs } from "pinia";

import { useAgentStore } from '@/stores/agentStore';
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import DeployModal from '@/components/agents/DeployModal.vue';
import ConfigModal from '@/components/agents/ConfigModal.vue';
import DetailsModal from "@/components/agents/DetailsModal.vue";
import { getAgentStatus } from "@/utils/agentUtil.js";

const $api = inject("$api");

const agentStore = useAgentStore();
const { agents, selectedAgent } = storeToRefs(agentStore);
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);

let agentRefreshInterval = ref(null);

onMounted(async () => {
    await agentStore.getAgents($api);
    await agentStore.getAgentConfig($api);
    agentRefreshInterval.value = setInterval(async () => {
        await agentStore.getAgents($api);
    }, 3000);
});

onBeforeUnmount(() => {
    clearInterval(agentRefreshInterval.value);
})

function removeDeadAgents() {
    agents.value.forEach((agent, index) => {
        if (getAgentStatus(agent) === "dead") {
            agentStore.deleteAgent($api, agent.paw, index);
        }
    });
}

function removeAllAgents() {
    agents.value.forEach((agent, index) => agentStore.deleteAgent($api, agent.paw, index));
}

function killAllAgents() {
    agents.value.forEach((agent) => agentStore.killAgent($api, agent.paw));
}
</script>

<template lang="pug">
//- Header
.content
    h2 代理
    p 要运行一次行动，必须至少部署一个代理。分组是代理的集合，使多个主机可以同时被攻陷。
hr

//- Button row
.columns.mb-4
    .column.is-4.is-flex.buttons.mb-0
        button.button.is-primary.level-item(@click="modals.agents.showDeploy = true")
            span.icon
                font-awesome-icon(icon="fas fa-plus") 
            span 部署代理
        button.button.is-primary.level-item(@click="modals.agents.showConfig = true")
            span.icon
                font-awesome-icon(icon="fas fa-cog")
            span 配置
    .column.is-4.is-flex.is-justify-content-center
        span.tag.is-medium.m-0
            span.mr-4.has-text-success 
                span.has-text-weight-bold.mr-3 {{ agents.filter((a) => getAgentStatus(a) === 'alive' || getAgentStatus(a) === 'pending kill').length }} 存活
                span.has-text-weight-bold {{ agents.filter((a) => a.trusted).length }} 已信任
            strong.mr-4 {{ agents.length }} 个代理
            span.mr-4.has-text-warning 
                span.has-text-weight-bold.mr-3 {{ agents.filter((a) => getAgentStatus(a) === 'dead').length }} 已死亡
                span.has-text-weight-bold {{ agents.filter((a) => !a.trusted).length }} 未信任
    .column.is-4.is-flex.is-justify-content-end
        .dropdown.is-right.is-hoverable
            .dropdown-trigger 
                button.button.is-primary(aria-haspopup="true" aria-controls="bulk-actions")
                    span 批量操作 
                    span.icon 
                        font-awesome-icon(icon="fas fa-angle-down" aria-hidden="true")
            .dropdown-menu(role="menu")
                .dropdown-content 
                    a.dropdown-item(@click="removeDeadAgents()") 移除已死亡代理
                    a.dropdown-item(@click="removeAllAgents()") 移除所有代理
                    a.dropdown-item(@click="killAllAgents()") 终止所有代理

//- Agents table
table.table.is-striped.is-hoverable.is-fullwidth(v-if="agents.length")
    thead
        tr
            th ID（爪印 paw）
            th 主机 
            th 分组 
            th 平台
            th 通讯方式
            th 进程号（PID）
            th 权限
            th 状态
            th 最近在线
            th 操作
    tbody
        tr(v-for="(agent, index) in agents" :key="agent.paw" @click="selectedAgent = agent; modals.agents.showDetails = true")
            td {{ agent.paw }}
            td {{ agent.host }}
            td {{ agent.group }}
            td {{ agent.platform }}
            td {{ agent.contact }}
            td {{ agent.pid }}
            td {{ agent.privilege }}
            td 
                span(:class="{ 'has-text-warning': getAgentStatus(agent) === 'dead', 'has-text-success': getAgentStatus(agent) === 'alive', 'has-text-info': getAgentStatus(agent) === 'pending kill' }") {{ getAgentStatus(agent) === 'alive' ? '存活' : getAgentStatus(agent) === 'dead' ? '死亡' : '待终止' }}
                span ， 
                span(:class="{ 'has-text-warning': !agent.trusted, 'has-text-success': agent.trusted }") {{ agent.trusted ? '已信任' : '未信任' }}
            td {{ new Date(agent.last_seen).toLocaleString() }}
            td.has-text-centered 
                button.delete.is-white(@click.stop="agentStore.deleteAgent($api, agent.paw, index)")
.has-text-centered.content(v-if="!agents.length")
    p 尚未部署任何代理

//- Modals
DeployModal
ConfigModal
DetailsModal
</template>


<style scoped>
tr {
    cursor: pointer;
}
</style>
