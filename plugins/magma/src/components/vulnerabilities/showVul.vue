<script setup>
import { reactive, inject, defineProps, watch } from "vue";
import { storeToRefs } from "pinia";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";

const props = defineProps({
  selVulnerability: {
    type: Object,
    default: null,
  },
});

// 只读展示用的缓存对象
const detail = reactive({
  vulnerability_id: "",
  name: "",
  product: "",
  description: "",
  risk: "Medium",
  cve: "",
  cvss_v3: 0.0,
  access: "",
});

// 收到父组件传入的 vulnerability 后，填充 detail
watch(
  () => props.selVulnerability,
  (val) => {
    if (!val) return;
    detail.vulnerability_id = val.vulnerability_id || "";
    detail.name = val.name || "";
    detail.product = val.product || "";
    detail.description = val.description || "";
    detail.risk = val.risk || "Medium";
    detail.cve = val.cve || "";
    detail.cvss_v3 =
      val.cvss_v3 !== undefined && val.cvss_v3 !== null ? val.cvss_v3 : 0.0;
    detail.access = val.access || "";
    console.log("已载入漏洞详情:", val);
  },
  { immediate: true }
);

const $api = inject("$api"); // 目前不需要，但保留注入不影响

const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);

function closeModal() {
  // 这里使用 coreDisplayStore 里定义的开关字段
  if (modals.value.vulnerability) {
    modals.value.vulnerability.showVul = false;
  }
}
</script>
<template lang="pug">
.modal(:class="{ 'is-active': modals.vulnerability && modals.vulnerability.showVul }")
  .modal-background(@click="closeModal()")
  .modal-card
    header.modal-card-head.header-bar
      .header-left
        p.modal-card-title 漏洞详情
        p.header-subtitle 仅展示漏洞信息，不支持在此页面编辑
      button.delete(aria-label="close" @click="closeModal()")

    .modal-card-body
      .form-grid
        // 左侧：基础信息
        .form-section
          h3.section-title 基本信息
          p.section-tip 漏洞的基础属性信息，便于识别与检索

          .field
            label.label 漏洞 ID
            .display-box {{ detail.vulnerability_id || '未分配' }}

          .field
            label.label 漏洞名称
            .display-box {{ detail.name || '未命名漏洞' }}

          .field
            label.label 关联产品
            .display-box {{ detail.product || '未设置' }}

          .field
            label.label CVE 编号
            .display-box {{ detail.cve || '未分配' }}

          .field
            label.label CVSS v3 分数
            .display-box {{ detail.cvss_v3 !== null && detail.cvss_v3 !== undefined ? detail.cvss_v3 : 'N/A' }}

        // 右侧：风险与描述
        .form-section
          h3.section-title 风险信息与说明
          p.section-tip 了解漏洞风险等级与详细描述

          .field
            label.label 风险等级
            .display-box
                span(v-if="detail.risk === 'Low'") 低风险
                span(v-else-if="detail.risk === 'Medium'") 中风险
                span(v-else-if="detail.risk === 'High'") 高风险
                span(v-else) 未知风险

          .field
            label.label 访问级别 / 标记
            .display-box {{ detail.access || '未设置' }}

          .field
            label.label 漏洞描述
            .display-box.display-box--multiline {{ detail.description || '暂无描述' }}

    footer.modal-card-foot.footer-bar
      button.button(type="button" @click="closeModal()") 关闭
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
  background: #10131d;
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

/* 只读展示框 */
.display-box {
  background: #171924;
  border: 1px dashed #353b5c;
  border-radius: 6px;
  padding: 8px 10px;
  color: #f5f5f5;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;     /* ✅ 自动换行 */
  word-break: break-word;    /* ✅ 长词也会断行 */
  display: block;            /* ✅ 不再用 flex，改成块级元素 */
  width: 100%;
}

.display-box--multiline {
  max-height: none;          /* ✅ 去掉高度限制 */
  overflow: visible;         /* ✅ 内容完全显示 */
}

.desc-text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: inherit;
  font-size: 13px;
  color: #e5e7ff;
}

/* 风险标签 */
.tag-mini {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 11px;
  line-height: 1;
}

/* 低 / 中 / 高 / 未知风险配色 */
.risk-low {
  background: rgba(16, 185, 129, 0.15);
  border: 1px solid rgba(16, 185, 129, 0.7);
  color: #6ee7b7;
}
.risk-mid {
  background: rgba(234, 179, 8, 0.15);
  border: 1px solid rgba(234, 179, 8, 0.75);
  color: #facc15;
}
.risk-high {
  background: rgba(248, 113, 113, 0.15);
  border: 1px solid rgba(248, 113, 113, 0.85);
  color: #fecaca;
}
.risk-unknown {
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.8);
  color: #bfdbfe;
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

/* 自适应 */
@media (max-width: 960px) {
  .form-grid {
    grid-template-columns: 1fr;
  }
}

</style>

