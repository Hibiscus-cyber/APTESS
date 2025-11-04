<script setup>
import { useProfileStore } from "@/stores/profileStore";
import { storeToRefs } from "pinia";
import { ref, onMounted, onBeforeUnmount,watch,inject,reactive} from 'vue'
import {
  initSvg,
  drawFromSnapshot,
  destroy,
  resetView,     
  setDataFromSnapshot,
  onFileChange,
  setFlag,
  refreshHotSet,  
  startPolling,
  stopPolling,
  get_fileName,
} from '@/stores/topologyStore.js'
const $api = inject("$api");
const profileStore = useProfileStore();
const { profiles } = storeToRefs(profileStore);

const fileName=ref('')
const containerEl = ref(null)
const flag = ref(0)

async function FileChange(e) {
  const name = await onFileChange(e)  // onFileChange 返回字符串
  fileName.value = name || e.target.files?.[0]?.name || ''
}

// 这个 ref 绑定到 checkbox
const lockedMode = ref(false)

// 当 lockedMode 改变时，同步到拓扑模块
watch(lockedMode, (val) => {
  // 勾上 -> 1，取消 -> 0
  setFlag(val ? 1 : 0)
})

onMounted(async () => {
  initSvg(containerEl.value)
    // 先拿一次初始数据
  refreshHotSet()
  // 启动轮询
  startPolling()
  fileName.value = get_fileName()
  await profileStore.getProfiles($api);
  const savedState = localStorage.getItem('graphState')
  if (savedState) {
    try {
      const snapshot = JSON.parse(savedState)

      // 告诉模块：把这个 snapshot 作为内部的 data
      setDataFromSnapshot(snapshot)

      // 让模块自己画
      drawFromSnapshot(snapshot)
    } catch (err) {
      console.warn('恢复 graphState 失败:', err)
    }
  }
})

onBeforeUnmount(() => {
  stopPolling()
  destroy()
})
</script>

<template lang="pug">
.section
  .content
    h2.title.is-4 网络拓扑图
    p.subtitle.is-6
      | 网络拓扑图用于描述网络结构、设备位置、连接关系以及攻击路径等信息的可视化表示
    hr

  // 外层左右布局容器
  .is-flex.is-align-items-stretch
    // 左侧竖直按钮栏
    .box.toolbar.is-flex.is-flex-direction-column.is-align-items-flex-start.p-3.mr-4
      button.button.is-primary.is-small.mb-3(@click="resetView")
        span.icon.is-small
          font-awesome-icon(icon='fas fa-sync-alt')
        span 重置视图

      label.checkbox.mb-3
        input(type="checkbox" v-model="lockedMode")
        | 锁定拖拽模式

      .file.is-small.is-link
        label.file-label
          input#file.file-input(type="file" accept=".yml,.yaml" @change="FileChange")
          span.file-cta
            span.file-icon
              font-awesome-icon(icon='fas fa-upload')
            span.file-label 载入YAML文件
        span.file-name.ml-2 {{ fileName || '未选择文件' }}

    // 右侧拓扑图容器
    .box#container(ref="containerEl")

</template>




<style scoped>
.section {
  display: flex;
  flex-direction: column;
  height: 100vh; /* 占满整个视口高度 */
}

.is-flex {
  flex: 1;
  overflow: hidden;
}

/* 左侧工具栏 */
.toolbar {
  flex: 0 0 220px;
  height: 100%;
  background: #1c1c1c;
  border-radius: 10px;
  padding: 20px;              /* 内边距增大，整体更松散 */
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;                  /* 工具间距 */
}

/* 按钮更大、更易点击 */
.toolbar .button {
  font-size: 1rem;            /* 增大文字 */
  padding: 10px 16px;         /* 增大内边距 */
  border-radius: 8px;
  width: 100%;                /* 按钮宽度充满侧栏 */
}


/* 右侧拓扑画布 */
#container {
  flex: 1;
  height: 100%;
  background-color: #111;
  border: 1px solid #333;
  border-radius: 10px;
  overflow: hidden;
  position: relative;
}


</style>
