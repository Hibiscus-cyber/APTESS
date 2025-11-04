// PayloadManager Plugin Registration for Magma
// 恶意载荷库管理插件注册

export default {
  name: 'payloadmanager',
  version: '1.0.0',
  description: '恶意载荷库管理插件',
  
  // 路由配置
  routes: [
    {
      path: '/payloads',
      name: '恶意载荷库',
      component: () => import('./gui/PayloadsView.vue'),
      meta: {
        title: '恶意载荷库',
        icon: 'fas fa-bomb',
        requiresAuth: true
      }
    }
  ],
  
  // 导航菜单配置
  navigation: {
    label: '恶意载荷库',
    icon: 'fas fa-bomb',
    path: '/payloads',
    order: 50
  },
  
  // 权限配置
  permissions: [
    'payloads:read',
    'payloads:write',
    'payloads:delete',
    'payloads:import',
    'payloads:export'
  ],
  
  // 初始化函数
  async initialize(app, store) {
    console.log('恶意载荷库插件已初始化')
    
    // 注册store
    if (store) {
      const { usePayloadStore } = await import('./gui/stores/payloadStore.js')
      store.use(usePayloadStore)
    }
  },
  
  // 清理函数
  async cleanup() {
    console.log('恶意载荷库插件清理完成')
  }
}
