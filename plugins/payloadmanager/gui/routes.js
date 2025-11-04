// PayloadManager Routes Configuration
// 恶意载荷库管理插件路由配置

import PayloadsView from './PayloadsView.vue'

export const routes = [
  {
    path: '/payloads',
    name: 'Payloads',
    component: PayloadsView,
    meta: {
      title: 'Malware Payloads',
      icon: 'fas fa-bomb',
      requiresAuth: true,
      description: 'Manage malware payloads organized by platform and ATT&CK tactics'
    }
  }
]

export const navigation = {
  label: 'Payloads',
  icon: 'fas fa-bomb',
  path: '/payloads',
  order: 50,
  badge: null
}

export default {
  routes,
  navigation
}
