<script setup>
import { inject, onMounted } from "vue";
import { useCoreStore } from "../stores/coreStore";
import { storeToRefs } from "pinia";

const $api = inject("$api");

const coreStore = useCoreStore();
const { contacts } = storeToRefs(coreStore);
const { availableContacts } = storeToRefs(coreStore);

onMounted(async () => {
  await coreStore.getContacts($api);
  await coreStore.getAvailableContacts($api);
});

async function downloadReport(contact) {
  await coreStore.downloadContactReport($api, contact);
}
</script>

<template lang="pug">
.content
    h2 通讯方式
    p #[strong 通讯方式是代理的接触点。] 通讯方式是服务器上代理进行通信的连接端点。 
      | 代理可以针对一个或多个通讯方式自定义编写。每个通讯方式都会记录所有代理连接以及它下发的所有命令。可在下方为任意通讯方式下载报告。

hr

table.table.is-striped.is-fullwidth
    tbody
        template(v-for="(contact) of contacts" :key="contact.name")
            tr
                th {{ contact.name }}
                td {{ contact.description }}
                td
                    template(v-if="!availableContacts.includes(contact.name.toUpperCase())")
                        button.button.is-small(disabled) 无可用报告
                    template(v-else)
                        button.button.is-small.is-primary(@click="downloadReport(contact.name)")
                            span.icon
                              font-awesome-icon(icon="fas fa-download")
                            span 下载报告
</template>

