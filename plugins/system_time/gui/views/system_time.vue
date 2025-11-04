<script setup>
import { ref, onMounted } from 'vue';
import { inject } from 'vue';

// 注入API服务
const $api = inject('$api');

// 系统时间状态
const currentTime = ref('');
const timestamp = ref(0);

// 获取当前时间
const getCurrentTime = async () => {
  try {
    const response = await $api.get('/plugin/system_time/current_time');
    currentTime.value = response.data.current_time;
    timestamp.value = response.data.timestamp;
  } catch (error) {
    console.error('获取系统时间失败:', error);
  }
};

// 组件挂载时获取时间
onMounted(() => {
  getCurrentTime();
  // 每秒更新一次时间
  setInterval(getCurrentTime, 1000);
});
</script>

<template>
  <div class="system-time-container">
    <div class="card">
      <header class="card-header">
        <p class="card-header-title">
          <span class="icon mr-2"><i class="fas fa-clock"></i></span>
          系统时间
        </p>
      </header>
      <div class="card-content">
        <div class="content">
          <div class="is-size-2 has-text-centered my-6 font-mono">
            {{ currentTime }}
          </div>
          <div class="has-text-centered my-4">
            <span class="tag is-info">
              时间戳: {{ timestamp }}
            </span>
          </div>
          <div class="has-text-centered">
            <button 
              @click="getCurrentTime"
              class="button is-primary"
              :class="{ 'is-loading': loading }"
              :disabled="loading"
            >
              <span class="icon"><i class="fas fa-sync-alt"></i></span>
              <span>立即刷新</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.system-time-container {
  padding: 20px;
}

.font-mono {
  font-family: 'Courier New', Courier, monospace;
}
</style>