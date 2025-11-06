<script setup>
import { reactive, ref, inject, computed } from "vue";
import { storeToRefs } from "pinia";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import { useProfileStore } from "@/stores/profileStore";
import { useAbilityStore } from "../../stores/abilityStore";

const $api = inject("$api");
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const profileStore = useProfileStore();
const abilityStore = useAbilityStore();

const fileUploadPlaceholder = "未选择文件";
const fileName = ref(fileUploadPlaceholder);
const isFileSelected = ref(false);
const input = ref(null);

const platformOptions = [
  { label: "Windows", value: "Windows" },
  { label: "Linux", value: "Linux" },
  { label: "macOS", value: "macOS" },
  { label: "其他", value: "Other" },
];

const tacticOptions = [
  { label: "发现", value: "Discovery" },
  { label: "执行", value: "Execution" },
  { label: "持久化", value: "Persistence" },
  { label: "权限提升", value: "Privilege Escalation" },
  { label: "防御规避", value: "Defense Evasion" },
  { label: "凭据访问", value: "Credential Access" },
  { label: "数据收集", value: "Collection" },
  { label: "命令与控制", value: "Command and Control" },
  { label: "数据渗出", value: "Exfiltration" },
  { label: "影响", value: "Impact" },
  { label: "横向移动", value: "Lateral Movement" },
];

const riskOptions = [
  { label: "低", value: "Low" },
  { label: "中", value: "Medium" },
  { label: "高", value: "High" },
];

const validation = reactive({
  name: "",
  file_name: "",
  description: "",
  file_type: "",
  platforms: [],
  tactics: [],
  risk: "Medium",
});

// 自动计算文件类型
const fileExtension = computed(() => {
  if (!fileName.value || fileName.value === fileUploadPlaceholder) {
    return "未选择文件";
  }
  const parts = fileName.value.split(".");
  return parts.length > 1 ? parts.pop() : "未知";
});

function updateFileName($event) {
  const files = $event.target.files;
  if (files && files.length > 0) {
    const file = files[0];
    fileName.value = file.name;
    validation.file_name = file.name;
    validation.file_type = fileExtension.value;
    isFileSelected.value = true;
  } else {
    fileName.value = fileUploadPlaceholder;
    validation.file_name = "";
    validation.file_type = "";
    isFileSelected.value = false;
  }
}

function closeModal() {
  modals.value.profile.showUpload = false;
}

async function submitFile() {
  const file = input.value?.files?.[0];
  if (!file) return;
  await abilityStore.savePayload($api, file, true, true);
}

async function submitProfile($event) {
  $event.preventDefault();
  if (!isFileSelected.value) return;

  const file = input.value?.files?.[0];
  if (!file) return;

  const payload = {
    name: validation.name,
    file_name: validation.file_name,
    platform: validation.platforms,
    tactic: validation.tactics,
    risk: validation.risk,
    description: validation.description,
    file_type: validation.file_type,
  };

  try {
    await profileStore.saveProfiles($api, payload);
    Object.assign(validation, {
      name: "",
      file_name: "",
      description: "",
      file_type: "",
      platforms: [],
      tactics: [],
      risk: "Medium",
    });
    fileName.value = fileUploadPlaceholder;
    isFileSelected.value = false;
    if (input.value) input.value.value = "";
    closeModal();
  } catch (err) {
    console.error("保存失败:", err?.response?.data || err);
    console.log("完整响应:", err?.response?.data);
    console.log("json 部分:", err?.response?.data?.json);
  }
}

function onSubmitClick($event) {
  submitFile();
  submitProfile($event);
}
</script>

<template lang="pug">
.modal(:class="{ 'is-active': modals.profile.showUpload }")
  .modal-background(@click="closeModal()")
  .modal-card
    header.modal-card-head.header-bar
      .header-left
        p.modal-card-title 上传载荷画像
        p.header-subtitle 上传脚本或二进制文件，创建载荷画像
      button.delete(aria-label="close" @click="closeModal()")

    .modal-card-body
      form(@submit.prevent)
        .form-grid
          // 左侧：基本信息
          .form-section
            h3.section-title 基本信息
            p.section-tip 为载荷画像设置名称和说明，便于检索与复用

            .field
              label.label 字段
              .id-row
                span.id-label 载荷ID
                span.id-value 自动生成

            .field
              label.label 载荷画像名称
              .control
                input.input(
                  v-model="validation.name"
                  placeholder="如：内网探测脚本（端口+服务识别）"
                )

            .field
              label.label 描述
              .control
                textarea.textarea(
                  v-model="validation.description"
                  rows="3"
                  placeholder="简要描述载荷用途、执行环境、注意事项等"
                )

            .field.field-inline
              .field-half
                label.label 文件名
                .display-box {{ fileName }}
              .field-half
                label.label 文件类型
                .display-box {{ fileExtension }}

            .field
              label.label 上传文件
              .upload-row
                span.upload-text 请选择要上传的文件
                label.file-label
                  input.file-input(type="file" ref="input" @change="updateFileName")
                  span.file-cta
                    span.file-icon
                      font-awesome-icon(icon="fas fa-upload")
                    span.file-label 选择文件…

          // 右侧：分类信息
          .form-section
            h3.section-title 分类信息
            p.section-tip 选择对应平台、战术阶段与威胁等级，辅助画像管理

            .field
              label.label 平台
              .control
                .checkbox-group.checkbox-group--scroll
                  label.checkbox-item(v-for="p in platformOptions" :key="p.value")
                    input(type="checkbox" :value="p.value" v-model="validation.platforms")
                    span.checkbox-label {{ p.label }}

            .field.mt-4
              label.label 战术
              .control
                .checkbox-group.checkbox-grid.checkbox-group--scroll
                  label.checkbox-item(v-for="t in tacticOptions" :key="t.value")
                    input(type="checkbox" :value="t.value" v-model="validation.tactics")
                    span.checkbox-label {{ t.label }}

            .field.mt-4
              label.label 威胁等级
              .control
                select.select-box(v-model="validation.risk")
                  option(
                    v-for="r in riskOptions"
                    :key="r.value"
                    :value="r.value"
                  ) {{ r.label }}

        .summary-bar
          .summary-left
            span.summary-title 画像概览：
            span.summary-item(v-if="validation.name") 名称：{{ validation.name }}
            span.summary-item(v-if="validation.platforms.length") 平台数：{{ validation.platforms.length }}
            span.summary-item(v-if="validation.tactics.length") 战术数：{{ validation.tactics.length }}
          .summary-right
            span.dot(:class="{ 'dot-active': isFileSelected }")
            span.summary-hint {{ isFileSelected ? '已选择文件，可以提交' : '请选择文件后再提交' }}

    footer.modal-card-foot.footer-bar
      button.button(type="button" @click="closeModal()") 关闭
      button.button.is-primary(
        type="submit"
        :disabled="!isFileSelected || !validation.name"
        @click="onSubmitClick($event)"
      )
        span.icon
          font-awesome-icon(icon="fas fa-save")
        span 上传画像
</template>

<style scoped>
/* 隐藏原生 input */
.file-input {
  display: none;
}
.file-icon {
  font-size: 14px;
}

/* 横向布局容器 */
.upload-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background:rgba(8, 12, 26, 0.9);
  border: 1px solid rgba(74, 141, 255, 0.5);
  border-radius: 6px;
  padding: 10px 16px;
  gap: 16px;
}

/* 左侧文字 */
.upload-text {
  font-size: 13px;
  color: #cfd5ff;
  flex: 1;
}

.modal-card {
  width: 72%;
  max-width: 920px;
  background: #050811;
  border-radius: 14px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.65);
  border: 1px solid rgba(70, 120, 255, 0.3);
}

/* 头部条 */
.header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: radial-gradient(circle at top left, #1b2340 0, #050811 55%);
  border-bottom: 1px solid rgba(74, 141, 255, 0.3);
  padding: 10px 18px;
}
.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.modal-card-title {
  color: #f5f7ff;
  font-size: 18px;
  font-weight: 600;
}
.header-subtitle {
  font-size: 12px;
  color: #a8b3ff;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 标签 */
.tag {
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 11px;
  line-height: 1;
}
.tag-info {
  background: rgba(74, 141, 255, 0.15);
  border: 1px solid rgba(74, 141, 255, 0.6);
  color: #d6e2ff;
}
.tag-mini {
  background: rgba(84, 194, 255, 0.1);
  border: 1px solid rgba(84, 194, 255, 0.5);
  color: #c8f0ff;
  margin-right: 4px;
  margin-top: 4px;
}

/* 主体布局 */
.modal-card-body {
  padding: 18px 18px 12px;
  background: radial-gradient(circle at top, #101524 0, #050811 55%);
}

.form-grid {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 18px;
}

.form-section {
  background: rgba(8, 12, 26, 0.9);
  border-radius: 10px;
  padding: 14px 14px 12px;
  border: 1px solid rgba(60, 80, 140, 0.65);
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #e1e5ff;
  margin-bottom: 4px;
}
.section-tip {
  font-size: 11px;
  color: #8b93c8;
  margin-bottom: 10px;
}

/* 字段行 */
.field {
  margin-bottom: 10px;
}
.label {
  font-size: 12px;
  color: #c3c8f7;
  margin-bottom: 4px;
}

.id-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #10131d;
  border-radius: 6px;
  border: 1px dashed #353b5c;
  padding: 6px 10px;
}
.id-label {
  font-size: 12px;
  color: #9fa6d8;
}
.id-value {
  font-size: 12px;
  color: #e8edff;
}

/* 输入控件 */
.input,
.select-box,
.textarea {
  background: #10131d;
  border: 1px solid #353b5c;
  border-radius: 6px;
  color: #f5f5ff;
  font-size: 13px;
  padding: 6px 9px;
}
.textarea {
  resize: vertical;
}
.input:focus,
.select-box:focus,
.textarea:focus {
  outline: none;
  border-color: #4a8dff;
  box-shadow: 0 0 0 1px rgba(74, 141, 255, 0.4);
}

/* 文件名 + 类型并排 */
.field-inline {
  display: flex;
  gap: 10px;
}
.field-half {
  flex: 1;
}

.display-box {
  background: #171924;
  border: 1px solid #353b5c;
  border-radius: 6px;
  padding: 6px 8px;
  color: #f5f5f5;
  font-size: 13px;
  height: 34px;
  display: flex;
  align-items: center;
}

/* checkbox 区域 */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  background: #10131d;
  border-radius: 6px;
  border: 1px solid #353b5c;
  max-height: 160px;
}
.checkbox-group--scroll {
  overflow-y: auto;
  scrollbar-width: thin;
}
.checkbox-group--scroll::-webkit-scrollbar {
  width: 6px;
}
.checkbox-group--scroll::-webkit-scrollbar-thumb {
  border-radius: 999px;
  background: rgba(120, 140, 200, 0.8);
}

.checkbox-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 6px 10px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #dde1ff;
}
.checkbox-item input[type="checkbox"] {
  width: 14px;
  height: 14px;
  accent-color: #4a8dff;
}
.checkbox-label {
  white-space: nowrap;
}

/* 已选标签提示 */
.selected-tags {
  margin-top: 4px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}
.selected-label {
  font-size: 11px;
  color: #9fa6d8;
}

/* 按钮外层 */
.file-label {
  display: inline-flex;
  align-items: center;
  border-radius: 6px;
  background:  rgba(8, 12, 26, 0.9);
  color: #ffffff;
  padding: 6px 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  border: none;
}

.file-cta .file-label{
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  border: none;
  background: transparent;
}
.file-cta .file-label:hover{
  background: transparent;
}

/* 内层文件按钮样式 */
.file-cta {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #ffffff;
  border: none;
  background: #313749;
}
/* 底部摘要条 */
.summary-bar {
  margin-top: 14px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid rgba(70, 120, 255, 0.4);
  background: linear-gradient(90deg, rgba(20, 40, 110, 0.8), rgba(6, 10, 26, 0.95));
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}
.summary-left {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.summary-title {
  font-size: 12px;
  color: #e7ecff;
  font-weight: 500;
}
.summary-item {
  font-size: 11px;
  color: #cfd7ff;
}

.summary-right {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #c4d0ff;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #555b7c;
}
.dot-active {
  background: #4ad38a;
}

/* 底部按钮区 */
.footer-bar {
  background: #050811;
  border-top: 1px solid rgba(40, 52, 100, 0.8);
  padding: 10px 18px;
}
.button {
  font-size: 13px;
  border-radius: 999px;
}
.button.is-primary {
  background: linear-gradient(135deg, #4a8dff, #7ea6ff);
  border: none;
  color: #fff;
  box-shadow: 0 0 18px rgba(74, 141, 255, 0.45);
}
.button.is-primary:disabled {
  opacity: 0.45;
  box-shadow: none;
  cursor: not-allowed;
}

/* 自适应 */
@media (max-width: 960px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
