<script setup>
import { inject, ref, reactive, watch, onMounted } from "vue";
import { storeToRefs } from "pinia";

import { useAbilityStore } from "@/stores/abilityStore";
import CodeEditor from "@/components/core/CodeEditor.vue";
import AutoSuggest from "@/components/core/AutoSuggest.vue";

const props = defineProps({
  ability: Object,
  active: Boolean,
  creating: Boolean,
});
const emit = defineEmits(["close"]);

const $api = inject("$api");

const abilityStore = useAbilityStore();
const { tactics, techniqueIds, techniqueNames, platforms, payloads } =
  storeToRefs(abilityStore);

let abilityToEdit = ref({});
let validation = reactive({
  name: "",
  tactic: "",
  techniqueId: "",
  techniqueName: "",
  executors: "",
});

onMounted(async () => {
  await abilityStore.getAbilities($api);
  await abilityStore.getPayloads($api);
});

watch(
  () => props.ability,
  () => {
    setAbilityToEdit();
  }
);

function setAbilityToEdit() {
  abilityToEdit.value = JSON.parse(JSON.stringify(props.ability));
  if (!abilityToEdit.value.requirements) {
    abilityToEdit.value.requirements = [];
  }
}

function addExecutor() {
  const baseExecutor = {
    cleanup: [],
    timeout: 60,
    platform: "darwin",
    name: platforms.value.darwin[0],
    payloads: [],
    parsers: [],
  };
  if (!abilityToEdit.value.executors) {
    abilityToEdit.value.executors = [baseExecutor];
  } else {
    abilityToEdit.value.executors.push(baseExecutor);
  }
}

function validateAndSave() {
  validation.name = abilityToEdit.value.name ? "" : "Name cannot be empty";
  validation.tactic = abilityToEdit.value.tactic
    ? ""
    : "Tactic cannot be empty";
  validation.techniqueId = abilityToEdit.value.technique_id
    ? ""
    : "Technique ID cannot be empty";
  validation.techniqueName = abilityToEdit.value.technique_name
    ? ""
    : "Technique Name cannot be empty";
  validation.executors =
    abilityToEdit.value.executors &&
    abilityToEdit.value.executors.every(
      (executor) =>
        executor.platform &&
        executor.name &&
        executor.command &&
        executor.timeout !== null &&
        executor.timeout >= 0
    )
      ? ""
      : "There must be at least 1 executor. Each executor must have a command, platform, timeout, and executor.";

  if (Object.keys(validation).every((k) => !validation[k])) {
    abilityStore.saveAbility($api, abilityToEdit.value, props.creating);
    emit("close");
  }
}

async function deleteAbility() {
  await abilityStore.deleteAbility($api, abilityToEdit.value.ability_id);
  emit("close");
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': props.active }")
    .modal-background(@click="emit('close')")
    .modal-card 
        header.modal-card-head 
            p.modal-card-title {{ props.creating ? '创建' : '编辑' }}能力
        .modal-card-body.content.m-0
            form
                label.label 能力 ID
                .field(v-if="!props.creating")
                    .control
                        input.input(v-model="abilityToEdit.ability_id" disabled)
                .field(v-else)
                    p.is-italic ID 将自动生成
                .field
                    label.label 名称
                    .control
                        input.input(v-model="abilityToEdit.name" :class="{ 'is-danger': validation.name }")
                        p.has-text-danger {{ validation.name }}
                .field
                    label.label 描述
                    .control
                        textarea.textarea(v-model="abilityToEdit.description")
                .field
                    label.label 战术 (Tactic)
                    .control(v-if="tactics.length > 0")
                        AutoSuggest(v-model="abilityToEdit.tactic" :items="tactics" :isDanger="!!validation.tactic" placeholder="输入或选择战术")
                        p.has-text-danger {{ validation.tactic }}
                .field
                    label.label 技术 ID (Technique ID)
                    .control(v-if="techniqueIds.length > 0")
                        AutoSuggest(v-model="abilityToEdit.technique_id" :items="techniqueIds" :isDanger="!!validation.techniqueId" placeholder="输入或选择技术 ID")
                        p.has-text-danger {{ validation.techniqueId }}
                .field
                    label.label 技术名称 (Technique Name)
                    .control(v-if="techniqueNames.length > 0")
                        AutoSuggest(v-model="abilityToEdit.technique_name" :items="techniqueNames" :isDanger="!!validation.techniqueName" placeholder="输入或选择技术名称")
                        p.has-text-danger {{ validation.techniqueName }}
                .field
                    label.label 选项
                    .control
                        input(type="checkbox" v-model="abilityToEdit.singleton")
                        span.ml-3 单实例 (Singleton)
                .field
                    .control
                        input(type="checkbox" v-model="abilityToEdit.repeatable")
                        span.ml-3 可重复执行 (Repeatable)
                .field
                    .control
                        input(type="checkbox" v-model="abilityToEdit.delete_payload")
                        span.ml-3 删除载荷 (Delete payload)
            p.has-text-centered 执行器 (Executors)
            p.has-text-danger {{ validation.executors }}
            .has-text-centered
                button.button.is-primary.mb-4(@click="addExecutor()")
                    span.icon
                        font-awesome-icon(icon="fas fa-plus")
                    span 添加执行器
            .box(v-for="(executor, index) in abilityToEdit.executors" :key="index + (abilityToEdit.ability_id ? abilityToEdit.ability_id : 0)")
                button.button.delete-btn(@click="abilityToEdit.executors.splice(index, 1)")
                    span.icon
                        font-awesome-icon(icon="fas fa-times")
                form
                    .field
                        label.label 平台 (Platform)
                        .control
                            .select
                                select(v-model="executor.platform")
                                    option(v-for="platform in Object.keys(platforms)" :value="platform") {{ platform }}
                    .field
                        label.label 执行器 (Executor)
                        .control
                            .select
                                select(v-model="executor.name")
                                    option(v-for="exec in platforms[executor.platform]" :value="exec") {{ exec }}
                    .field.is-grouped.is-grouped-multiline
                        label.label 载荷 (Payloads)
                        br
                        .control(v-if="executor.payloads.length === 0" class="ml-4")
                            span.tag.is-light 无载荷
                        .control(v-for="(payload, idx) in executor.payloads" class="ml-4")
                          .tags.has-addons
                            span.tag.is-primary {{ payload }}
                            a.tag.is-delete(@click="executor.payloads.splice(idx, 1)")
                    .field
                        .control.mt-3
                            div.select.is-small.is-multiple.is-fullwidth
                              select.select.is-multiple(multiple size="6")
                                template(v-for="payload in payloads")
                                  option(v-if="executor.payloads.indexOf(payload) === -1" @click="executor.payloads.push(payload)") {{ payload }}
                    .field
                        label.label 命令 (Command)
                        .control
                            CodeEditor(v-model="executor.command" :key="index" language="bash" line-numbers)
                    .field
                        label.label 超时时间 (Timeout)
                        .control
                            input.input(type="number" v-model="executor.timeout")
                    .field
                      label.label 清理命令 (Cleanup)
                      .field.has-addons(v-for="(cleanup, index) of executor.cleanup")
                          .control.is-expanded
                              CodeEditor(v-model="executor.cleanup[index]" :key="index" language="bash" line-numbers)
                          .control
                              a.button(@click="executor.cleanup.splice(index, 1)")
                                  span.icon
                                      font-awesome-icon(icon="fas fa-times")
                      button.button(type="button" @click="executor.cleanup.push('')")
                          span.icon
                              font-awesome-icon(icon="fas fa-plus")
                          span 添加清理命令
                    .field
                      label.label 需求条件 (Requirements)
                      .field.has-addons(v-for="(requirement, index) of abilityToEdit.requirements")
                          .control.is-expanded
                            .field
                              span 需求模块
                              .control
                                input.input(type="text" v-model="abilityToEdit.requirements[index].module" placeholder="输入需求模块名")
                            .field
                              span 来源关系
                              .field.has-addons(v-for="(relationship, r_index) of abilityToEdit.requirements[index].relationship_match")
                                .field
                                  .control
                                    input.input(type="text" v-model="abilityToEdit.requirements[index].relationship_match[r_index].source" placeholder="源 (Source)")
                                .field
                                  .control
                                    input.input(type="text" v-model="abilityToEdit.requirements[index].relationship_match[r_index].edge" placeholder="边 (Edge) [可选]")
                                .field 
                                  .control
                                    input.input(type="text" v-model="abilityToEdit.requirements[index].relationship_match[r_index].target" placeholder="目标 (Target) [可选]")
                          .control
                              a.button(@click="abilityToEdit.requirements.splice(index, 1)")
                                  span.icon
                                      font-awesome-icon(icon="fas fa-times")
                      button.button(type="button" @click="abilityToEdit.requirements.push({module: '',relationship_match:[{source:'', edge:'',target:''}]})")
                          span.icon
                              font-awesome-icon(icon="fas fa-plus")
                          span 添加需求
                    .field
                      label.label 解析器 (Parsers)
                      .field.has-addons(v-for="(parser, index) of executor.parsers")
                          .control.is-expanded
                            .field
                              span 解析器模块
                              .control
                                input.input(type="text" v-model="executor.parsers[index].module" placeholder="输入解析器模块名")
                            .field
                              span 输出源配置
                                .field.has-addons(v-for="(parserconfig, pc_index) of executor.parsers[index].parserconfigs")
                                    .field
                                      .control
                                        input.input(type="text" v-model="executor.parsers[index].parserconfigs[pc_index].source" placeholder="输出源 (Source)")
                                    .field
                                      .control
                                        input.input(type="text" v-model="executor.parsers[index].parserconfigs[pc_index].edge" placeholder="输出边 (Edge) [可选]")
                                    .field
                                      .control
                                        input.input(type="text" v-model="executor.parsers[index].parserconfigs[pc_index].target" placeholder="输出目标 (Target) [可选]")
                          .control
                              a.button(@click="executor.parsers.splice(index, 1)")
                                  span.icon
                                      font-awesome-icon(icon="fas fa-times")
                      button.button(type="button" @click="executor.parsers.push({module: '', parserconfigs: [{source:'', edge:'', target:''}]})")
                          span.icon
                              font-awesome-icon(icon="fas fa-plus")
                          span 添加解析器
            p.has-text-danger(v-if="abilityToEdit.executors && abilityToEdit.executors.length") {{ validation.executors }}
            .has-text-centered
                button.button.is-primary.mb-4(v-if="abilityToEdit.executors && abilityToEdit.executors.length" @click="addExecutor()")
                    span.icon
                        font-awesome-icon(icon="fas fa-plus")
                    span 添加执行器
        footer.modal-card-foot.is-flex.is-justify-content-space-between
            .is-flex
                button.button(@click="setAbilityToEdit()") 
                    span.icon
                        font-awesome-icon(icon="fas fa-undo")
                    span 重置
                button.button.is-danger.is-outlined(v-if="!props.creating" @click="deleteAbility()") 
                    span.icon
                        font-awesome-icon(icon="fas fa-trash")
                    span 删除
            .is-flex
                button.button(@click="emit('close')") 取消 
                button.button.is-primary(@click="validateAndSave()")
                    span.icon
                        font-awesome-icon(icon="fas fa-save") 
                    span {{ props.creating ? "创建" : "保存" }} 
</template>


<style scoped>
.box {
  position: relative;
}

.delete-btn {
  position: absolute;
  top: 18px;
  right: 20px;
}

.modal-card {
  width: 1000px;
}

@media screen and (max-width: 1050px) {
  .modal-card {
    width: 600px;
  }
}
</style>
