<script setup>
import { inject, reactive, ref } from "vue";
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
  watchdogTimer: "",
});
let showDetails = ref(false);
let showActions = ref(false);

function getAgentStatus(agent) {
  if (!agent.last_seen) return "";
  let lastSeen = new Date(agent.last_seen).getTime();
  let msSinceSeen = Date.now() - lastSeen;
  // Give a buffer of 1 minute to mark an agent dead
  let isAlive = msSinceSeen < agent.sleep_max * 1000;

  if (
    msSinceSeen <= 60000 &&
    agent.sleep_min === 3 &&
    agent.sleep_max === 3 &&
    agent.watchdog === 1
  ) {
    return "pending kill";
  } else {
    return msSinceSeen <= 60000 || isAlive ? "alive" : "dead";
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
    validation.beaconTimer =
      "Sleep min must be less than or equal to Sleep max";
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
  if (
    (selectedAgent.value.watchdog !== 0 && !selectedAgent.value.watchdog) ||
    selectedAgent.value.watchdog < 0
  ) {
    validation.watchdogTimer =
      "Watchdog timer must be greater than or equal to 0";
  } else {
    validation.watchdogTimer = "";
  }

  // If all inputs pass validation, save
  if (
    !validation.group &&
    !validation.beaconTimer &&
    !validation.watchdogTimer
  ) {
    agentStore.saveSelectedAgent($api);
  }
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.operations.showAgentDetails }")
    .modal-background(@click="modals.operations.showAgentDetails = false")
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
                        th.has-text-right 通信通道
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
                                label.mr-3 最小值
                                input.input.mr-4(v-model="selectedAgent.sleep_min" type="number" placeholder="30" min="0" :max="selectedAgent.sleep_max" :class="{ 'is-danger': validation.beaconTimer }")
                                label.mr-3 最大值
                                input.input(v-model="selectedAgent.sleep_max" type="number" placeholder="60" :min="selectedAgent.sleep_min" :class="{ 'is-danger': validation.beaconTimer }")
                            p.help.has-text-danger(v-if="validation.beaconTimer") {{ validation.beaconTimer }}
                    tr
                        th.has-text-right 看门狗定时器（秒）
                        td
                            input.input(type="number" v-model="selectedAgent.watchdog" min="0" :class="{ 'is-danger': validation.watchdogTimer }")
                            p.help.has-text-danger(v-if="validation.watchdogTimer") {{ validation.watchdogTimer }}
            button.button.is-primary.is-fullwidth.mt-4(@click="saveAgent()") 保存设置
            hr
            button.accordion(@click="showDetails = !showDetails") 代理详细信息
            .panel(:style="{ maxHeight: showDetails ? '700px' : '0px' }")
              table
                  col(width="30%")
                  col(width="70%")
                  tbody
                      tr
                          th.has-text-right 状态
                          td 
                              span(:class="{ 'has-text-warning': getAgentStatus(selectedAgent) === 'dead', 'has-text-success': getAgentStatus(selectedAgent) === 'alive', 'has-text-info': getAgentStatus(selectedAgent) === 'pending kill' }") {{ getAgentStatus(selectedAgent) }}
                              span ，
                              span(:class="{ 'has-text-warning': !selectedAgent.trusted, 'has-text-success': selectedAgent.trusted }") {{ selectedAgent.trusted ? '可信' : '不可信' }}
                      tr
                          th.has-text-right Paw
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
                          th.has-text-right 权限
                          td {{ selectedAgent.privilege }}
                      tr
                          th.has-text-right 最后通信时间
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
                          th.has-text-right 进程 ID (PID)
                          td {{ selectedAgent.pid }}
                      tr
                          th.has-text-right 父进程 ID (PPID)
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
                          th.has-text-right P2P 代理接收端
                          td {{ (selectedAgent.proxy_receivers && Object.keys(selectedAgent.proxy_receivers).length) ? Object.keys(selectedAgent.proxy_receivers) : '未激活本地 P2P 代理接收端。' }}
                      tr
                          th.has-text-right P2P 代理链
                          td {{ (selectedAgent.proxy_chain && selectedAgent.proxy_chain.length) ? selectedAgent.proxy_chain.join(', ') : '未通过 P2P 代理连接至 C2。' }}
        footer.modal-card-foot.is-flex.is-justify-content-flex-end 
            button.button(@click="modals.operations.showAgentDetails = false") 关闭
            button.button.is-danger.is-outlined(@click="agentStore.killAgent($api, selectedAgent.paw); modals.operations.showAgentDetails = false;")
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
.accordion {
  background-color: hsl(0deg, 0%, 14%);
  color: #eee;
  cursor: pointer;
  padding: 18px;
  width: 100%;
  text-align: left;
  border: none;
  outline: none;
  transition: 0.4s;
}
.panel {
  padding: 0 18px;
  background-color: hsl(0deg, 0%, 22%);
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.2s ease-out;
}
</style>
