<script setup>
import { storeToRefs } from "pinia";
import { ref, inject, onMounted, computed, watch } from "vue";
import { useCoreStore } from "../stores/coreStore";

const coreStore = useCoreStore();
const { mainConfig } = storeToRefs(coreStore);

const $api = inject("$api");

const settings = ref({});

const tabNameMap = {
    ability_refresh: "能力刷新",
    "app.contact.dns.domain"	:"DNS 域名",
    "app.contact.dns.socket"	:"DNS 套接字",
    "app.contact.ftp.host"	:"FTP 主机",
    "app.contact.ftp.port"	:"FTP 端口",
    "app.contact.ftp.pword"	:"FTP 密码",
    "app.contact.ftp.server.dir"	:"FTP 服务器目录",
    "app.contact.ftp.user"	:"FTP 用户名",
    "app.contact.gist"	:"Gist（GitHub 代码片段）通讯",
    "app.contact.html"	:"HTML 通讯",
    "app.contact.http"	:"HTTP 通讯",
    "app.contact.slack.api_key"	:"Slack API 密钥",
    "app.contact.slack.bot_id"	:"Slack 机器人 ID",
    "app.contact.slack.channel_id"	:"Slack 频道 ID",
    "app.contact.tcp"	:"TCP 通讯",
    "app.contact.tunnel.ssh.host_key_file"	:"SSH 隧道主机密钥文件",
    "app.contact.tunnel.ssh.host_key_passphrase"	:"SSH 隧道主机密钥口令",
    "app.contact.tunnel.ssh.socket"	:"SSH 隧道套接字",
    "app.contact.tunnel.ssh.user_name"	:"SSH 隧道用户名",
    "app.contact.tunnel.ssh.user_password"	:"SSH 隧道用户密码",
    "app.contact.udp"	:"UDP 通讯",
    "app.contact.websocket"	:"WebSocket 通讯",
    "exfil_dir"	:"数据外传目录",
    "objects.planners.default"	:"默认计划器对象",
    "reachable_host_traits"	:"可达主机特征",
    "reports_dir"	:"报告目录",
};

watch(mainConfig, () => {
    let config = JSON.parse(JSON.stringify(mainConfig.value));
    delete config.plugins;
    settings.value = config;
});

onMounted(async () => {
    await coreStore.getMainConfig($api);
});

function isSettingChanged(setting) {
    return settings.value[setting] === mainConfig.value[setting];
}
</script>

<template lang="pug">
.content
    h2 设置
hr

.is-flex.is-justify-content-center
    table
        tbody
            tr(v-for="setting in Object.keys(settings)")
                td.has-text-right.pt-3
                    span {{ tabNameMap[setting] || setting }}
                td
                    .field.has-addons
                        .control
                            input.input(v-model="settings[setting]")
                        .control
                            button.button(@click="settings[setting] = mainConfig[setting]" v-tooltip="'重置'" :disabled="isSettingChanged(setting)")
                                span.icon 
                                    font-awesome-icon(icon="fas fa-undo")
                        .control
                            button.button.is-primary(@click="coreStore.updateMainConfigSetting($api, setting, settings[setting])" :disabled="isSettingChanged(setting)") 更新
</template>


<style scoped>
table {
    background-color: hsl(0deg, 0%, 14%);
    border-radius: 8px;
}

td {
    padding: 10px 25px;
}
</style>
