# 恶意载荷库目录结构说明

## 概述
恶意载荷库插件现在支持Windows、Linux和macOS三个平台的恶意载荷管理，每个平台都有完整的ATT&CK战术分类目录结构。

## 目录结构

```
plugins/payloadmanager/data/payloads/
├── windows/                    # Windows平台载荷
│   ├── collection/            # 数据收集
│   ├── command-and-control/   # 命令控制
│   ├── credential-access/     # 凭据访问
│   ├── defense-evasion/       # 防御规避
│   ├── discovery/            # 发现
│   ├── execution/            # 执行
│   ├── exfiltration/         # 数据渗出
│   ├── impact/               # 影响
│   ├── lateral-movement/      # 横向移动
│   ├── persistence/          # 持久化
│   └── privilege-escalation/ # 权限提升
├── linux/                      # Linux平台载荷
│   ├── collection/
│   ├── command-and-control/
│   ├── credential-access/
│   ├── defense-evasion/
│   ├── discovery/
│   ├── execution/
│   ├── exfiltration/
│   ├── impact/
│   ├── lateral-movement/
│   ├── persistence/
│   └── privilege-escalation/
└── darwin/                     # macOS平台载荷
    ├── collection/
    ├── command-and-control/
    ├── credential-access/
    ├── defense-evasion/
    ├── discovery/
    ├── execution/
    ├── exfiltration/
    ├── impact/
    ├── lateral-movement/
    ├── persistence/
    └── privilege-escalation/
```

## 文件格式

每个payload文件都是YAML格式，包含以下信息：

- **id**: 唯一标识符
- **name**: 载荷名称
- **description**: 载荷描述
- **md5**: 文件MD5哈希值
- **file_type**: 文件类型（exe, dll, ps1, sh, py等）
- **file_size**: 文件大小（字节）
- **payload_file**: 实际文件路径
- **tactics**: ATT&CK战术列表
- **threat_level**: 威胁等级（Low, Medium, High, Critical）
- **platforms**: 支持的操作系统平台
- **cve_references**: CVE引用列表
- **apt_groups**: 相关APT组织
- **tags**: 标签列表
- **plugin**: 插件名称

## 前端功能增强

### Payload卡片显示
- 文件大小和MD5值（前8位）
- 文件位置信息
- 威胁等级颜色标识

### Payload详情页面
- 完整的文件位置路径
- 文件大小格式化显示
- 完整MD5值
- CVE引用标签
- APT组织标签
- 自定义标签

## 使用方法

1. 将payload文件放置在对应平台的战术目录下
2. 创建对应的YAML元数据文件
3. 系统会自动加载并显示在恶意载荷库界面中
4. 可以通过Web界面查看、编辑、导入和导出payload

## 注意事项

- 确保payload文件路径正确
- MD5值会自动计算（如果文件存在）
- 文件大小会自动获取（如果文件存在）
- 支持导入/导出ZIP格式的payload包

## 真实Payload示例

当前包含的真实payload文件：

### Windows平台
- **Mimikatz**: `plugins/stockpile/payloads/Invoke-MemeKatz.ps1` - PowerShell版本的Mimikatz凭据转储工具
- **PowerShell Scanner**: `plugins/stockpile/payloads/basic_scanner.ps1` - PowerShell网络扫描工具
- **Legitimate Executable**: `plugins/stockpile/payloads/totallylegit.exe` - 看起来合法的Windows可执行文件

### Linux平台
- **Network Scanner**: `plugins/access/data/payloads/scanner.sh` - 基于NMAP的Linux网络扫描工具

### macOS平台
- **WiFi Scanner**: `plugins/stockpile/payloads/wifi.sh` - WiFi网络扫描和管理工具

这些payload文件都是Caldera自带的真实工具，可以直接在渗透测试中使用。