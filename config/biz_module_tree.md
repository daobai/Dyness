# Dyness 业务功能模块树

> **统一模块树**：同时用于映射 **Web 自动化测试用例** 和 **API 接口测试用例**。
> 所有测试用例的"所属模块"字段均按此文档填写。

---

## 一、模块树总览

```
Dyness 云平台
│
├── 首页
│   ├── 电站概览
│   ├── 数据统计
│   └── 快捷入口
│
├── 电站中心
│   ├── 电站管理
│   │   ├── 电站列表
│   │   ├── 新建电站
│   │   ├── 编辑电站
│   │   └── 删除电站
│   ├── 电站详情
│   │   ├── 概览（3D图示/功率曲线/电量趋势）
│   │   ├── 设备管理（添加/删除/详情）
│   │   ├── 数据统计（收益/电量/效率）
│   │   ├── 告警管理
│   │   ├── 授权管理
│   │   ├── 智能场景
│   │   └── 基本信息
│   └── 设备管理（全局设备列表）
│
├── 设备库管理
│   ├── 设备档案
│   ├── 设备入库
│   └── 设备概览页
│
├── VPP管理
│   ├── VPP电站授权
│   ├── VPP设备快照
│   └── VPP接入/退出
│
├── 运维管理
│   ├── 监控管理
│   ├── 数据录播
│   ├── 固件管理
│   │   ├── 固件列表
│   │   ├── 新增固件
│   │   ├── 固件下发
│   │   └── 固件授权
│   └── 设备模块变更记录
│
├── 产品管理
│   ├── 产品物模型
│   ├── 在售产品类型管理
│   └── 设备类型配置
│
├── 数据采集
│   ├── 采集器参数设置
│   ├── 逆变器设置
│   ├── 电表管理（4G电表/IEMS/Shelly）
│   ├── 数据转发
│   └── 主从机管理
│
├── 设备参数配置
│   ├── 安规国家设置
│   ├── 工作模式设置
│   ├── 电池参数设置
│   ├── 负载控制设置
│   ├── 峰值控制设置
│   ├── 高级参数设置
│   └── 发电机控制
│
├── 工商业储能
│   ├── 接入点管理
│   ├── 工商业设备管理
│   ├── 工商业一体机设置
│   ├── 工商业系统设置
│   ├── 工商业电池参数
│   ├── 工商业运行模式
│   ├── 工商业峰谷时段
│   └── 工商业高级设置
│
├── OTA升级
│   ├── 固件列表
│   ├── 固件详情
│   ├── 固件升级（⚠️ 危险）
│   ├── 固件下发（⚠️ 危险）
│   ├── 升级任务管理
│   ├── 升级记录
│   ├── 设备升级检查
│   ├── 禁升名单管理（⚠️ 警告）
│   ├── ROM类型
│   ├── 电池类型
│   └── 最新版本
│
├── BI大屏
│   ├── 大屏数据展示
│   └── 工商业大屏
│
├── 数据分析
│   ├── 报表统计
│   ├── 累计报表
│   ├── 实时报表
│   └── 电站数据统计
│
├── 售后管理
│   ├── 售后工单
│   │   ├── 工单列表
│   │   ├── 创建工单
│   │   └── 工单详情（AI辅助诊断）
│   ├── 产品质保
│   ├── 延保记录
│   └── 告警设置
│
├── 市场运营
│   ├── 场景管理
│   └── 动态电价
│
├── 开发者中心
│   ├── API管理
│   │   ├── API应用创建
│   │   └── API密钥管理
│   └── 数据转发配置
│
├── 系统设置
│   ├── 国家/地区设置
│   ├── 系统语言设置
│   ├── 告警接收设置
│   ├── 页面标签管理
│   └── 暗亮模式
│
├── 账号与权限
│   ├── 账号注册
│   ├── 账号登录/退出
│   ├── 用户中心
│   └── OAuth2设备选择
│
└── 其他
    ├── 天气管理
    ├── CA证书下发
    ├── 充电桩设备
    ├── 积分商城
    └── 意见建议
```

---

## 二、API 接口 → 业务模块映射

| 接口路径 | 业务模块路径 | func_module |
|---------|-------------|-------------|
| GetDeviceList | 电站中心/电站管理/电站列表 | station_mgmt |
| GetDeviceInfBySN | 电站中心/设备管理 | device_info |
| GetStatusInfBySN | 电站中心/设备管理/设备详情 | device_status |
| GetRealTimeDataBySN | 电站中心/电站详情/概览 | realtime_data |
| GetTotalEnergyDataBySN | 电站中心/电站详情/数据统计 | energy_data |
| GetAlarmInfBySN | 电站中心/告警管理 | alarm_info |
| GetParallelInfBySN | 电站中心/设备管理/并机信息 | parallel_info |
| GetBaseSetting / SetBaseSetting | 设备参数配置/安规国家设置 | safety_setting |
| GetWorkModeSetting / SetWorkModeSetting | 设备参数配置/工作模式设置 | work_mode |
| GetBatterySetting / SetBatterySetting | 设备参数配置/电池参数设置 | battery_setting |
| GetLoadControlSetting / SetLoadControlSetting | 设备参数配置/负载控制设置 | load_control |
| GetPeakControlSetting / SetPeakControlSetting | 设备参数配置/峰值控制设置 | peak_control |
| GetAdvancedSetting / SetAdvancedSetting | 设备参数配置/高级参数设置 | advanced_setting |
| GetGeneratorControlSetting / SetGeneratorControlSetting | 设备参数配置/发电机控制 | generator_control |
| SetCommerceSystemSetting | 工商业储能/工商业系统设置 | commerce_system |
| SetCommerceBatterySetting | 工商业储能/工商业电池参数 | commerce_battery |
| SetCommerceRunModeSetting | 工商业储能/工商业运行模式 | commerce_run_mode |
| SetCommercePeakValleyPeriodSetting | 工商业储能/工商业峰谷时段 | commerce_peak_valley |
| SetCommerceAdvancedSetting | 工商业储能/工商业高级设置 | commerce_advanced |

---

## 三、Web 功能 → 业务模块映射

> Web 自动化测试用例按页面/功能路径映射到同一棵模块树。

| Web 页面/功能 | 业务模块路径 |
|--------------|-------------|
| 首页仪表盘 | 首页/电站概览 |
| 电站列表页 | 电站中心/电站管理/电站列表 |
| 新建电站弹窗 | 电站中心/电站管理/新建电站 |
| 电站详情页-概览 | 电站中心/电站详情/概览 |
| 电站详情页-设备 | 电站中心/电站详情/设备管理 |
| 电站详情页-数据统计 | 电站中心/电站详情/数据统计 |
| 电站详情页-告警 | 电站中心/电站详情/告警管理 |
| 电站详情页-授权 | 电站中心/电站详情/授权管理 |
| 设备列表页 | 电站中心/设备管理 |
| 设备详情页 | 电站中心/设备管理/设备详情 |
| 固件管理页 | 运维管理/固件管理 |
| 固件下发页 | 运维管理/固件管理/固件下发 |
| 售后工单列表 | 售后管理/售后工单/工单列表 |
| 创建售后工单 | 售后管理/售后工单/创建工单 |
| API管理页 | 开发者中心/API管理 |
| 系统设置页 | 系统设置 |

---

## 四、模块命名规范

### 模块路径格式
- **禅道 CSV**：`Dyness Open API/电站中心/设备管理`
- **Web 用例**：`Dyness Web/电站中心/电站管理/电站列表`
- **统一标识**：使用 `func_module` 字段作为唯一标识符

### 新增模块流程
1. 在本文档"一、模块树总览"中添加新模块节点
2. 在对应映射表（二或三）中添加映射关系
3. 如果是 API 接口，同步更新 `tests/api/gen_*_cases.py` 中的 `_FUNC_MODULE_MAP`

---

## 五、风险等级（risk 字段）

自动化用例 CSV 中的 `risk` 字段标记用例的危险程度：

| 值 | 含义 | 执行策略 |
|----|------|---------|
| （空） | safe - 安全 | 默认执行（查询类、普通参数下发） |
| `warning` | 警告 | 默认执行（改变设备运行状态但可恢复） |
| `danger` | 危险 | **默认跳过**，需 `--include-danger` 显式开启 |

### 危险操作示例
- `SetCommerceAdvancedSetting` 含 `reset`/`faultReset` 参数（系统重启/故障重置）
- `SetAdvancedSetting` 含 `systemReset` 参数（系统重置）
- 其他可能导致设备关机、恢复出厂设置的操作

### 执行命令
```bash
# 默认执行（跳过 danger 用例）
pytest tests/api -v

# 包含危险用例
pytest tests/api -v --include-danger
```

---

## 六、版本记录

| 日期 | 变更内容 |
|------|---------|
| 2026-09-21 | 初始版本，基于用户手册和接口文档整理 |
