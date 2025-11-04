# 恶意载荷库插件

恶意载荷库管理插件，提供恶意载荷的分类、管理和与Ability集成的功能。

## 功能特性

- 🎯 **分类管理**: 按系统类型和ATT&CK战术分类管理恶意载荷
- 📁 **文件管理**: 支持载荷文件的存储、上传和下载
- 🔍 **智能筛选**: 基于系统类型、战术、威胁等级等多维度筛选
- 📊 **威胁评估**: 支持Low/Medium/High/Critical威胁等级评估
- 🔗 **Ability集成**: 与Caldera Ability库无缝集成
- 📤 **导入导出**: 支持ZIP包和元数据的导入导出
- 🎨 **现代UI**: 基于Magma的Vue 3 + Pinia架构

## 技术架构

### 后端架构
- **数据模型**: `Payload`类和`PayloadSchema`
- **业务服务**: `PayloadManagerService`
- **API接口**: `PayloadApi`处理器
- **数据存储**: YAML文件 + 文件系统

### 前端架构 (Magma集成)
- **框架**: Vue 3 + Composition API
- **状态管理**: Pinia Store
- **组件**: 
  - `PayloadsView.vue` - 主界面
  - `CreateEditPayloadModal.vue` - 创建/编辑模态框
  - `ImportModal.vue` - 导入模态框
- **路由**: 通过Magma自动注册

## Magma集成

本插件完全集成到Caldera的Magma前端框架中：

### 1. 路由注册
```javascript
// gui/routes.js
export const routes = [
  {
    path: '/payloads',
    name: 'Payloads',
    component: PayloadsView,
    meta: {
      title: 'Malware Payloads',
      icon: 'fas fa-bomb',
      requiresAuth: true
    }
  }
]
```

### 2. 导航菜单
```javascript
export const navigation = {
  label: 'Payloads',
  icon: 'fas fa-bomb',
  path: '/payloads',
  order: 50
}
```

### 3. 状态管理
```javascript
// gui/stores/payloadStore.js
export const usePayloadStore = defineStore('payload', () => {
  // Vue 3 Composition API + Pinia
})
```

### 4. 插件注册
```javascript
// gui/index.js
export default {
  name: 'payloadmanager',
  routes,
  navigation,
  async initialize(app, store) {
    // 初始化逻辑
  }
}
```

## 数据结构

恶意载荷包含以下信息：
- `payload_id`: 唯一标识符
- `name`: 载荷名称
- `description`: 载荷描述
- `md5`: MD5哈希值
- `file_type`: 文件类型
- `file_size`: 文件大小
- `payload_file`: 文件路径
- `tactics`: 战术分类（支持多战术）
- `threat_level`: 威胁等级
- `platforms`: 支持平台
- `cve_references`: CVE引用
- `apt_groups`: APT组织
- `tags`: 标签

## 使用方法

### 1. 插件安装
**重要**: 插件注册需要手动配置，不是完全自动的：

1. **启用插件**: 在`conf/default.yml`的`plugins:`列表中添加`payloadmanager`
2. **构建前端**: 运行`python3 server.py --build`以复制GUI文件到Magma
3. **重启服务**: 重启Caldera服务

### 2. 访问界面
通过Magma导航菜单中的"Plugins" → "payloadmanager"访问。

### 3. 管理载荷
- 创建、编辑、删除恶意载荷
- 按平台、战术、威胁等级筛选
- 上传载荷文件
- 导入导出载荷数据

### 4. API使用
```bash
# 获取所有载荷
GET /api/v2/payloads

# 创建载荷
POST /api/v2/payloads

# 更新载荷
PATCH /api/v2/payloads/{id}

# 删除载荷
DELETE /api/v2/payloads/{id}

# 导入载荷
POST /api/v2/payloads/import

# 导出载荷
GET /api/v2/payloads/export
```

## 文件组织

```
plugins/payloadmanager/
├── hook.py                    # 插件入口
├── package.json               # Magma插件配置
├── app/                       # 后端代码
│   ├── c_payload.py          # 数据模型
│   ├── payloadmanager_svc.py # 业务服务
│   ├── payload_api.py       # API处理器
│   └── payload_data_svc.py  # 数据服务
├── gui/                       # 前端代码 (Magma)
│   ├── index.js              # 插件入口
│   ├── routes.js             # 路由配置
│   ├── PayloadsView.vue      # 主界面
│   ├── CreateEditPayloadModal.vue # 编辑模态框
│   ├── ImportModal.vue       # 导入模态框
│   └── stores/
│       └── payloadStore.js   # Pinia状态管理
└── data/                      # 数据存储
    └── payloads/
        ├── windows/          # Windows载荷
        ├── linux/            # Linux载荷
        └── darwin/           # macOS载荷
```

## 开发说明

### 前端开发
- 使用Vue 3 Composition API
- 状态管理使用Pinia
- 组件采用单文件组件(SFC)格式
- 遵循Magma插件开发规范

### 后端开发
- 遵循Caldera插件架构
- API使用aiohttp框架
- 数据存储使用YAML文件
- 支持文件上传下载

## Caldera插件注册机制详解

### 🔍 为什么不是完全自动注册？

Caldera的插件注册机制包含以下步骤：

#### 1. **插件发现** (自动)
```python
# app/service/app_svc.py:117-137
async def load_plugins(self, plugins):
    for plug in filter(trim, plugins):
        # 检查插件目录和hook.py文件
        if not os.path.isdir('plugins/%s' % plug) or not os.path.isfile('plugins/%s/hook.py' % plug):
            self.log.error('Problem locating the "%s" plugin...')
            exit(0)
```

#### 2. **插件启用** (手动配置)
```python
# 只有在配置文件中明确启用的插件才会被激活
if plugin.name in self.get_config('plugins') or plugin.name == 'magma':
    await plugin.enable(self.get_services())
```

#### 3. **前端集成** (构建时复制)
```javascript
// plugins/magma/prebundle.js:7-15
const plugins = fs.readdirSync('../')
plugins.forEach((plugin) => {
    // 检查gui目录是否存在
    if (!fs.existsSync(`../${plugin}/gui`)) return;
    // 复制gui目录到magma/src/plugins/
    fs.copySync(`../${plugin}/gui/`, `./src/plugins/${plugin}`)
});
```

### 📋 完整注册步骤

1. **配置文件修改**:
   ```yaml
   # conf/default.yml
   plugins:
     - payloadmanager
   ```

2. **构建前端**:
   ```bash
   python3 server.py --build
   ```

3. **重启服务**:
   ```bash
   python3 server.py
   ```

4. **访问界面**: `/plugins/payloadmanager`

### ⚠️ 常见问题

- **插件不显示**: 检查`conf/default.yml`中是否添加了插件名
- **前端404**: 运行`python3 server.py --build`重新构建
- **API不可用**: 确保插件在配置文件中启用

## 兼容性

- **Caldera**: >= 4.0.0
- **Magma**: >= 1.0.0
- **Vue**: >= 3.0.0
- **Python**: >= 3.8

## 许可证

Apache License 2.0
