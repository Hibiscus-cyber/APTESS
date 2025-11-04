<script setup>
import { inject, reactive } from "vue";
import { useAgentStore } from "../../stores/agentStore";
import { useCoreDisplayStore } from "../../stores/coreDisplayStore";
import { storeToRefs } from "pinia";

const $api = inject("$api");

const agentStore = useAgentStore();
const { selectedAgent } = storeToRefs(agentStore);
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);

let validation = reactive({
    group: "",
    beaconTimer: "",
    watchdogTimer: ""
});

function getAgentStatus(agent) {
    if (!agent.last_seen) return '';
    let lastSeen = new Date(agent.last_seen).getTime();
    let msSinceSeen = Date.now() - lastSeen;
    // Give a buffer of 1 minute to mark an agent dead
    let isAlive = (msSinceSeen < (agent.sleep_max * 1000));

    if (msSinceSeen <= 60000 && agent.sleep_min === 3 && agent.sleep_max === 3 && agent.watchdog === 1) {
        return 'pending kill'
    } else {
        return msSinceSeen <= 60000 || isAlive ? 'alive' : 'dead';
    }
}

function saveAgent() {
    // Validate group
    if (!selectedAgent.value.group) {
        validation.group = "Group cannot be empty";
    } else {
        validation.group = "";
    }
    // Validate beacon timer
    if (selectedAgent.value.sleep_min > selectedAgent.value.sleep_max) {
        validation.beaconTimer = "Sleep min must be less than or equal to Sleep max";
    } else if (selectedAgent.value.sleep_min < 0) {
        validation.beaconTimer = "Sleep min must be greater than or equal to 0";
    } else if (selectedAgent.value.sleep_max < 0) {
        validation.beaconTimer = "Sleep max must be greater than or equal to 0";
    } else if (!selectedAgent.value.sleep_min || !selectedAgent.value.sleep_max) {
        validation.beaconTimer = "Sleep min and max cannot be empty";
    } else {
        validation.beaconTimer = "";
    }
    // Validate watchdog
    if ((selectedAgent.value.watchdog !== 0 && !selectedAgent.value.watchdog) || selectedAgent.value.watchdog < 0) {
        validation.watchdogTimer = "Watchdog timer must be greater than or equal to 0";
    } else {
        validation.watchdogTimer = "";
    }

    // If all inputs pass validation, save
    if (!validation.group && !validation.beaconTimer && !validation.watchdogTimer) {
        agentStore.saveSelectedAgent($api);
    }
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.agents.showDetails }")
    .modal-background(@click="modals.agents.showDetails = false")
    .modal-card 
        header.modal-card-head 
            p.modal-card-title 代理详情
        .modal-card-body 
            p.has-text-weight-bold.has-text-centered.mb-3 设置 
            table
                col(width="30%")
                col(width="70%")
                tbody
                    tr
                        th.has-text-right 通信方式
                        td
                            .select.control
                                select(v-model="selectedAgent.pending_contact")
                                    option(v-for="contact in selectedAgent.available_contacts" :key="contact" :value="contact") {{ contact }}
                    tr
                        th.has-text-right 分组
                        td
                            input.input(type="text" v-model="selectedAgent.group" :class="{ 'is-danger': validation.group }")
                            p.help.has-text-danger(v-if="validation.group") {{ validation.group }}
                    tr 
                        th.has-text-right 心跳间隔（秒）
                        td
                            .is-flex.is-align-items-center 
                                label.mr-3 最小
                                input.input.mr-4(v-model="selectedAgent.sleep_min" type="number" placeholder="30" min="0" :max="selectedAgent.sleep_max" :class="{ 'is-danger': validation.beaconTimer }")
                                label.mr-3 最大
                                input.input(v-model="selectedAgent.sleep_max" type="number" placeholder="60" :min="selectedAgent.sleep_min" :class="{ 'is-danger': validation.beaconTimer }")
                            p.help.has-text-danger(v-if="validation.beaconTimer") {{ validation.beaconTimer }}
                    tr
                        th.has-text-right 看门狗计时（秒）
                        td
                            input.input(type="number" v-model="selectedAgent.watchdog" min="0" :class="{ 'is-danger': validation.watchdogTimer }")
                            p.help.has-text-danger(v-if="validation.watchdogTimer") {{ validation.watchdogTimer }}
            button.button.is-primary.is-fullwidth.mt-4(@click="saveAgent()") 保存设置
            hr
            p.has-text-weight-bold.has-text-centered.mb-3 代理信息
            table
                col(width="30%")
                col(width="70%")
                tbody
                    tr
                        th.has-text-right 状态
                        td 
                            span(:class="{ 'has-text-warning': getAgentStatus(selectedAgent) === 'dead', 'has-text-success': getAgentStatus(selectedAgent) === 'alive', 'has-text-info': getAgentStatus(selectedAgent) === 'pending kill' }") {{ getAgentStatus(selectedAgent) }}
                            span ，
                            span(:class="{ 'has-text-warning': !selectedAgent.trusted, 'has-text-success': selectedAgent.trusted }") {{ selectedAgent.trusted ? '已信任' : '未信任' }}
                    tr
                        th.has-text-right Paw（代理ID）
                        td {{ selectedAgent.paw }}
                    tr
                        th.has-text-right 主机
                        td {{ `${selectedAgent.host} (${selectedAgent.host_ip_addrs ? selectedAgent.host_ip_addrs.join(', ') : ''})` }}
                    tr(v-if="selectedAgent.display_name")
                        th.has-text-right 显示名称
                        td {{ selectedAgent.display_name }}
                    tr
                        th.has-text-right 用户名
                        td {{ selectedAgent.username }}
                    tr
                        th.has-text-right 权限级别
                        td {{ selectedAgent.privilege }}
                    tr
                        th.has-text-right 最后在线时间
                        td {{ new Date(selectedAgent.last_seen).toLocaleString() }}
                    tr
                        th.has-text-right 创建时间
                        td {{ new Date(selectedAgent.created).toLocaleString() }}
                    tr
                        th.has-text-right 架构
                        td {{ selectedAgent.architecture }}
                    tr
                        th.has-text-right 平台
                        td {{ selectedAgent.platform }}
                    tr
                        th.has-text-right 进程 ID（PID）
                        td {{ selectedAgent.pid }}
                    tr
                        th.has-text-right 父进程 ID（PPID）
                        td {{ selectedAgent.ppid }}
                    tr
                        th.has-text-right 可执行文件名
                        td {{ selectedAgent.exe_name }}
                    tr
                        th.has-text-right 位置
                        td {{ selectedAgent.location }}
                    tr
                        th.has-text-right 执行器
                        td {{ selectedAgent.executors ? selectedAgent.executors.join(", ") : '' }}
                    tr(v-if="selectedAgent.host_ip_addrs")
                        th.has-text-right 主机 IP 地址
                        td {{ selectedAgent.host_ip_addrs ? selectedAgent.host_ip_addrs.join(", ") : '' }}
                    tr
                        th.has-text-right 点对点代理接收器
                        td {{ (selectedAgent.proxy_receivers && Object.keys(selectedAgent.proxy_receivers).length) ? Object.keys(selectedAgent.proxy_receivers) : '无活动的本地 P2P 代理接收器。' }}
                    tr
                        th.has-text-right 点对点代理链路
                        td {{ (selectedAgent.proxy_chain && selectedAgent.proxy_chain.length) ? selectedAgent.proxy_chain.join(', ') : '未通过 P2P 代理连接至 C2。' }}
        footer.modal-card-foot.is-flex.is-justify-content-flex-end 
            button.button(@click="modals.agents.showDetails = false") 关闭
            button.button.is-danger.is-outlined(@click="agentStore.killAgent($api, selectedAgent.paw); modals.agents.showDetails = false;")
                span.icon 
                    font-awesome-icon(icon="fas fa-skull-crossbones") 
                span 终止代理
</template>


<style scoped>
th {
    padding-right: 15px;
}
table {
    border-collapse: separate;
    border-spacing: 10px;
}
</style>
