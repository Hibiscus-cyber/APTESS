<script setup>
import { storeToRefs } from "pinia";
import { reactive, inject, onMounted, computed, ref } from "vue";
import { useRoute } from "vue-router";
import { useProfileStore } from "@/stores/profileStore";
import { useCoreDisplayStore } from "@/stores/coreDisplayStore";
import UploadModal from "@/components/profiles/UploadProfile.vue";
import EditModal from "@/components/profiles/EditProfile.vue";

const $api = inject("$api");
const route = useRoute();
const profileStore = useProfileStore();
const { profiles } = storeToRefs(profileStore);
const coreDisplayStore = useCoreDisplayStore();
const { modals } = storeToRefs(coreDisplayStore);
const selProfile = ref(null);

// 平台、战术映射关系
const platformMap = {
  Windows: 'Windows',
  Linux: 'Linux',
  macOS: 'macOS',
  Other: '其他',
};
const tacticMap = {
  Discovery: '发现',
  Execution: '执行',
  Persistence: '持久化',
  'Privilege Escalation': '权限提升',
  'Defense Evasion': '防御规避',
  'Credential Access': '凭据访问',
  Collection: '数据收集',
  'Command and Control': '命令与控制',
  Exfiltration: '数据渗出',
  Impact: '影响',
  'Lateral Movement': '横向移动',
};
const tacticFilterOptions = [
  { label: "全部战术", value: "" },
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
const platformFilterOptions = [
  { label: "Windows", value: "Windows" },
  { label: "Linux", value: "Linux" },
  { label: "macOS", value: "macOS" },
  { label: "其他", value: "Other" },
];

let filters = reactive({
  searchQuery: "",
  name: "",
  tactic: "",    
  platforms: [],     
});

// 实现过滤器功能
const filteredProfiles = computed(() => {
  return profiles.value.filter((p) => {
    const matchSearch =
      p.name?.toLowerCase().includes(filters.searchQuery.toLowerCase());

    const matchName = !filters.name || p.name === filters.name;

    // 处理 profile.tactic 字段：可能是 string 或 array
    const profileTactics = Array.isArray(p.tactic)
      ? p.tactic
      : p.tactic
      ? [p.tactic]
      : [];
    const matchTactic =
      !filters.tactic || profileTactics.includes(filters.tactic);

    // 处理 profile.platform 字段：可能是 string 或 array
    const profilePlatforms = Array.isArray(p.platform)
      ? p.platform
      : p.platform
      ? [p.platform]
      : [];
    const matchPlatform =
      filters.platforms.length === 0 ||
      filters.platforms.some((pl) => profilePlatforms.includes(pl));

    return matchSearch && matchName && matchTactic && matchPlatform;
  });
});

onMounted(async () => {
  await profileStore.getProfiles($api);
  filters.name = route.query.name || "";
});

function clearFilters() {
  Object.keys(filters).forEach((k) => (filters[k] = ""));
  filters.platforms = []; // 手动清空数组
}

function selectProfile(profile) {
  console.log("selected profile:", profile?.profile_id);
  selProfile.value = profile;
}

</script>


<template lang="pug">
.content
  h2 载荷画像
  p “载荷画像”是指对攻击载荷的结构、行为和功能等特征的全面刻画。
hr

.box.mb-4
  .is-flex.is-align-items-center.is-flex-wrap-wrap
    // 新建载荷按钮
    button.button.is-primary.mr-3.mb-2(@click="modals.profile.showUpload = true")
      span.icon
        font-awesome-icon(icon="fas fa-plus")
      span 新建载荷

    // 搜索框
    .field.has-addons.mr-3.mb-2
      .control.has-icons-left
        input.input.is-small(
          v-model="filters.searchQuery"
          type="text"
          placeholder="搜索载荷…"
        )
        span.icon.is-left
          font-awesome-icon(icon="fas fa-search")

    // ✅ 战术筛选下拉框
    .field.mr-3.mb-2
      .control
        .select.is-small
          select(v-model="filters.tactic")
            option(
              v-for="t in tacticFilterOptions"
              :key="t.value"
              :value="t.value"
            ) {{ t.label }}

    // ✅ 系统平台多选
    .field.mr-3.mb-2
      .control.is-flex.is-align-items-center
        span.mr-2 系统:
        label.checkbox.mr-2(
          v-for="p in platformFilterOptions"
          :key="p.value"
        )
          input(
            type="checkbox"
            :value="p.value"
            v-model="filters.platforms"
          )
          span.ml-1 {{ p.label }}

    // 清除按钮与计数
    button.button.is-light.is-small.mr-3.mb-2(@click="clearFilters()") 清除筛选
    p.help.mb-0.mt-0 {{ filteredProfiles.length }} / {{ profiles.length }} 个载荷


.columns.is-multiline
  .column.is-12-mobile.is-6-tablet.is-4-desktop.is-3-widescreen(
    v-for="profile in filteredProfiles"
    :key="profile.profile_id"
  )
    .box.p-3.ability(@click="selectProfile(profile); modals.profile.showEdit = true")
      // 顶部：名称 + 风险等级
      .ability-header
        .ability-title
          strong.ability-name {{ profile.name || '未命名画像' }}
          span.ability-id(v-if="profile.profile_id") {{ '#' + profile.profile_id.slice(0, 8) }}
          span.ability-risk(:class="profile.risk === 'Low' ? 'risk-low' : profile.risk === 'Medium' ? 'risk-mid' : profile.risk === 'High' ? 'risk-high' : ''")
          span.ability-risk-label 风险
          span.ability-risk-value(
            v-if="profile.risk === 'Low'"
          ) 低
          span.ability-risk-value(
            v-else-if="profile.risk === 'Medium'"
          ) 中
          span.ability-risk-value(
            v-else-if="profile.risk === 'High'"
          ) 高
          span.ability-risk-value(
            v-else
          ) 未知

      // 中部：平台 + 战术 标签
      .ability-tags
        // 平台
        .tag-group(v-if="profile.platform && (Array.isArray(profile.platform) ? profile.platform.length : true)")
          span.tag-label 平台：
          span.tag-item(
            v-for="pl in (Array.isArray(profile.platform) ? profile.platform : [profile.platform])"
            :key="pl.label"
          ) {{ platformMap[pl] || pl }}
        // 战术
        .tag-group(
          v-if="profile.tactic && (Array.isArray(profile.tactic) ? profile.tactic.length : true)"
        )
          span.tag-label 战术：
          span.tag-item(
            v-for="t in (Array.isArray(profile.tactic) ? profile.tactic : [profile.tactic])"
            :key="t"
          ) {{ tacticMap[t] || t }}

      // 描述
      p.ability-desc {{ profile.description || '暂无描述' }}

      // 底部：文件名 + hover 提示
      .ability-meta
        span.file-name(
          v-if="profile.file_name"
          :title="profile.file_name"
        )
          font-awesome-icon(icon="fas fa-file-code" class="mr-1")
          | {{ profile.file_name }}
        span.meta-hint  点击卡片可查看 / 编辑

UploadModal
EditModal(:selProfile='selProfile')
</template>

<style scoped>
/* 顶部：标题+风险 */
.ability-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.ability-title {
  display: flex;
  flex-direction: column;
}

.ability-name {
  font-size: 15px;
  font-weight: 700;
  color: #f9fafb;
  max-width: 180px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ability-id {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 风险标记 */
.ability-risk {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid rgba(156, 163, 175, 0.5);
  background: rgba(17, 24, 39, 0.9);
}

.ability-risk-label {
  color: #9ca3af;
}

.ability-risk-value {
  font-weight: 600;
}

/* 低 / 中 / 高 不同颜色 */
.risk-low {
  border-color: rgba(16, 185, 129, 0.7);
  background: rgba(6, 95, 70, 0.6);
  color: #6ee7b7;
}

.risk-mid {
  border-color: rgba(234, 179, 8, 0.7);
  background: rgba(113, 63, 18, 0.6);
  color: #facc15;
}

.risk-high {
  border-color: rgba(248, 113, 113, 0.7);
  background: rgba(127, 29, 29, 0.6);
  color: #fecaca;
}

/* 平台 / 战术 标签区 */
.ability-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  margin-bottom: 8px;
}

.tag-group {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
}

.tag-label {
  font-size: 11px;
  color: #9ca3af;
}

.tag-item {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 999px;
  background: #111827;
  border: 1px solid #4b5563;
  color: #e5e7eb;
}

/* 描述 */
.ability-desc {
  font-size: 13px;
  color: #d1d5db;
  line-height: 1.4;
  margin: 4px 0 6px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;     /* 描述最多两行 */
  -webkit-box-orient: vertical;
}

/* 底部 meta 行 */
.ability-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #9ca3af;
  margin-top: auto;          /* 推到底部，让卡片高度统一 */
  padding-top: 4px;
  border-top: 1px dashed rgba(55, 65, 81, 0.8);
}

.file-name {
  display: inline-flex;
  align-items: center;
  max-width: 60%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta-hint {
  opacity: 0.8;
}

/* === 容器：统一行高 + 拉伸卡片 === */
.abilities{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(520px, 1fr)); /* 每卡至少 520px 宽 */
  gap: 12px;
  overflow-x: hidden; /* 保留你的设定 */
  align-items: stretch;                 /* 让格子里的元素拉满行高 */
  grid-auto-rows: 170px;                /* ✅ 统一每一行的高度（可按需调 150~200） */
}

/* 旧的 width 媒体查询会干扰自适应，覆盖为 100% */
@media (max-width: 2400px){ .box.ability{ width: 100% !important; } }
@media (min-width: 1200px){ .box.ability{ width: 100% !important; } }

/* === 卡片：占满格子高度，变成扁长形，内容竖直排布 === */
.box.ability{
  position: relative;
  cursor: pointer;
  border: 1px solid transparent;
  background-color: #272727;
  display: flex;               /* 竖向布局 */
  flex-direction: column;
  height: 100%;                /* ✅ 撑满格子的统一行高 */
  padding: 12px 16px;
  border-radius: 16px;
  transition: box-shadow .12s ease, border-color .12s ease, transform .08s ease;
}
.box.ability:hover{
  border: 1px solid #474747;
  box-shadow: 0 4px 12px rgba(0,0,0,.18);
  transform: translateY(-1px);
}

/* 顶部 meta 行（战术标签 / 技术ID） */
.box.ability > .is-flex{
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

/* 标题占一行或两行，底部留出空间给描述 */
.box.ability strong{
  font-weight: 800;
  line-height: 1.2;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;          /* 标题最多 2 行，可调为 1 */
  -webkit-box-orient: vertical;
}

/* 描述固定两行，超出省略，保证所有卡片同高 */
.box.ability p.help.mb-0{
  opacity: .9;
  line-height: 1.35;
  margin: 0;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;          /* ✅ 描述两行 */
  -webkit-box-orient: vertical;
}

/* 小优化 */
.box.ability .tag.is-small{ margin-right: 8px; }
.box.ability p.help.mt-0{ white-space: nowrap; opacity: .8; margin-left: 8px; }

/* 不同屏宽下的列宽与统一行高可微调 */
@media (max-width: 1440px){
  .abilities{ grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); grid-auto-rows: 180px; }
}
@media (max-width: 1024px){
  .abilities{ grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); grid-auto-rows: 190px; }
}
@media (max-width: 640px){
  .abilities{ grid-template-columns: 1fr; grid-auto-rows: 200px; } /* 手机上一列更高一点 */
}

</style>
