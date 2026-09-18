# OpenAPI 接口测试框架（tests/api）

基于 pytest 的**数据驱动** API 自动化测试，覆盖 Dyness OpenAPI（AquaVolt / AquaVolt_LV / SolarCube 三系列）的查询类 + 控制类接口。

## 核心特性

- **数据驱动**：用例全部在 CSV 里，改数据不改代码。
- **HMAC-SHA1 自签名鉴权**：每次请求自动生成 `Content-MD5` / `Date` / `Authorization` 头。
- **多设备 + 机型自适应**：一次跑多台设备，自动探测每台机型，用例与断言按机型裁剪。
- **完整报文留痕**：日志与报告都记录完整的请求报文（请求头+请求体）和响应报文（状态+响应头+响应体），便于事后查阅。

## 目录结构

```
tests/api/
├── config/config.yaml       # 配置：域名 / appId / appSecret / 设备SN / 超时
├── core/                    # API 专属公共库
│   ├── sign.py              #   HMAC-SHA1 自签名
│   ├── device.py            #   机型探测与归一化
│   ├── loader.py            #   用例加载 / 模板变量替换
│   └── assertions.py        #   断言引擎（JSONPath）
├── data/
│   ├── api_testdata.csv            #   接口测试数据-正常流（Excel/WPS 可直接编辑）
│   ├── api_testdata_negative.csv   #   接口测试数据-异常/边界/特殊参数
│   ├── models.yaml                 #   机型别名 + 硬件型号映射表
│   └── README.md            #   CSV 字段 / 断言语法详解
├── conftest.py              # 参数化入口 + fixtures + 日志/报告 hook
├── test_api.py              # 用例执行主体（签名→请求→断言→记录）
└── test_device_unit.py      # 机型归一化的离线单元测试（不联网）
```

> 通用报告模块在项目根的 [`common/report.py`](../../common/report.py)，供 api / modbus 等所有测试复用。

## 快速开始

1. 配置 `config/config.yaml`（域名、appId、appSecret、设备 SN）。
2. 安装依赖（项目根执行一次）：`py -3 -m pip install -r requirements.txt`
3. 运行全部：

   ```bat
   py -3 -m pytest tests/api -v
   ```

4. 看结果：控制台实时输出，日志在 `common/logs/`，报告在 `common/reports/`（跑完控制台末尾会打印具体路径）。

> Windows Git Bash 下中文乱码时，命令前加 `PYTHONIOENCODING=utf-8`。

## 运行命令

### 跑全部

```bat
py -3 -m pytest tests/api -v          # 详细
py -3 -m pytest tests/api -q          # 简洁
```

### 单独跑一个接口（-k 过滤）

用例 id 形如 `{用例ID} {接口名} {中文名}`（如 `TC007 GetBaseSetting 安规国家查询`），所以**按接口名或用例 ID 都能过滤**：

```bat
py -3 -m pytest tests/api -k "GetBaseSetting" -v   # 按接口名
py -3 -m pytest tests/api -k "TC007" -v            # 按用例ID
py -3 -m pytest tests/api -k "GetDeviceList or GetStatusInfBySN" -v   # 多个
py -3 -m pytest tests/api -k "not TC007" -v        # 排除某个，跑其余全部
```

### 指定设备 / 多设备

```bat
# 单台
py -3 -m pytest tests/api -v --device-sn 6LHC0110800W261040009
# 多台（逗号分隔）
py -3 -m pytest tests/api -v --device-sn SN1,SN2,SN3
# 测账号下全部设备（config.yaml 里 device_sn 留空）
```

### 参数覆盖（优先级高于 config.yaml）

```bat
py -3 -m pytest tests/api -v --base-url=xxx --app-id=xxx --app-secret=xxx --device-sn=SN1
```

### 只列用例，不执行（不联网）

```bat
py -3 -m pytest tests/api --collect-only -q
```

### 离线单元测试（机型归一化等，不联网）

```bat
py -3 -m pytest tests/api/test_device_unit.py -v
```

## 配置

配置在 `config/config.yaml`，优先级：**命令行参数 > 环境变量 > config.yaml**。

| 配置项 | 命令行 | 环境变量 | config.yaml |
|--------|--------|----------|-------------|
| 接入域名 | `--base-url` | `API_BASE_URL` | `api.base_url` |
| 应用 ID | `--app-id` | `API_APP_ID` | `api.app_id` |
| 应用密钥 | `--app-secret` | `API_APP_SECRET` | `api.app_secret` |
| 设备序列号 | `--device-sn` | `API_DEVICE_SN` | `api.device_sn` |
| 超时(秒) | `--timeout` | `API_TIMEOUT` | `api.timeout` |
| 请求间隔(秒) | `--request-interval` | `API_REQUEST_INTERVAL` | `api.request_interval` |
| 机型 | `--model` | `API_MODEL` | `api.model`（留空=自动探测，可手动指定兜底） |

`base_url` 需含 `/openapi/ems-device` 前缀；`device_sn` 支持多台（逗号分隔或 YAML 列表），留空=测账号下全部。

## 鉴权（HMAC-SHA1 自签名）

每个请求由 `core/sign.py` 动态生成请求头：

```
Content-MD5    = Base64(MD5(body))
Date           = GMT 时间（"Mon, 17 Sep 2026 08:00:00 GMT"）
string_to_sign = "POST\n{Content-MD5}\napplication/json\n{Date}\n{接口路径}"
sign           = Base64(HMAC-SHA1(appSecret, string_to_sign))
Authorization  = "API {appId}:{sign}"
```

签名强依赖 `Date` + 请求体 + 接口路径，任何一项变化签名即失效，因此**每次请求都实时签名**，无需手动管理。

## 多设备 + 机型自适应

- `device_sn` 支持多台；跑前框架调 `GetDeviceList` 自动探测每台设备的机型（归一化到 AquaVolt / AquaVolt_LV / SolarCube）。
- 机型映射在 `data/models.yaml`（两级：系列别名 + 硬件型号前缀），**新增机型时改这里即可，无需改代码**。
- 用例 `models` 列限制机型；断言 `[机型]` 前缀限制断言；机型不匹配自动跳过。
- 探测失败（网络不通/鉴权错/SN 无效）→ 该台降级为「只跑通用用例」；全部失败 → 整体 skip。

## 结果判定（三分类）

每条用例的结果分三类（报告与日志的「结果」列/字段 `outcome`）：

| 结果 | outcome | 判定条件 |
|------|---------|----------|
| **通过** | `PASS` | HTTP 200，且业务码 `code=200`，且响应体与接口文档一致（全部断言通过） |
| **待确认** | `PENDING` | HTTP 200，且 `code=200`，但响应体参数与文档不一致（字段断言失败），需人工与开发确认是文档问题还是实现问题 |
| **不通过** | `FAIL` | 其他情况：HTTP 状态码非 200、`code` 非 200、响应体非合法 JSON、请求超时/连接失败等 |

> **关键原则**：断言以接口文档为准。实际返回与文档不一致时保持文档断言、让用例进入「待确认」，**不改断言迁就实际**，由人工跟开发沟通确认。

## 日志与报告

### 日志（按月分目录，按天滚动）

- 位置：`common/logs/YYYYMM/api_test_YYYYMMDD.log`（如 `common/logs/202609/api_test_20260917.log`，每月一个子目录）。
- **同一天多次运行追加到同一文件**，每次运行写入 `# 运行开始 <时间>` 分隔标记；跨天自动换新文件。
- 每条用例记录**完整报文**：请求方法+URL、请求头、请求体、响应状态、响应头、响应体（不截断），以及断言结果。

### 报告（HTML + JSON）

- 位置：`common/reports/YYYYMMDD/report_<时间戳>.html` / `.json`（每天一个子目录），每次运行生成新文件。
- HTML：汇总卡片（总数/通过/待确认/不通过/跳过/通过率）+ 明细表，每行「报文」列可展开查看完整请求/响应。
- JSON：结构化结果（含 `request.headers/body`、`response.status/headers/body`），可脚本化提取。

## 测试数据与断言

- **正常流**：`data/api_testdata.csv`（18 个接口，合法参数 → 预期 `code=200`）。
- **异常/边界/特殊参数**：`data/api_testdata_negative.csv`（85 条：deviceSn 异常、枚举多值、越界、枚举非法、必填缺失、边界值等，预期业务码 `500`/`200`）。

字段、断言语法、机型前缀、模板变量 `{{deviceSn}}`、`expected_code` 等详解见 [`data/README.md`](data/README.md)。

## 接口清单

| 用例ID | 接口 | 类型 | 默认 |
|--------|------|------|------|
| TC001 | GetDeviceList | 查询 | 启用 |
| TC002 | GetDeviceInfBySN | 查询 | 启用 |
| TC003 | GetStatusInfBySN | 查询 | 启用 |
| TC004 | GetRealTimeDataBySN | 查询 | 启用 |
| TC005 | GetTotalEnergyDataBySN | 查询 | 启用 |
| TC006 | GetAlarmInfBySN | 查询 | 启用 |
| TC007 | GetBaseSetting | 控制-查询 | 启用 |
| TC009 | GetWorkModeSetting | 控制-查询 | 启用 |
| TC011 | GetBatterySetting | 控制-查询 | 启用 |
| TC013 | GetLoadControlSetting | 控制-查询 | 启用 |
| TC015 | GetPeakControlSetting | 控制-查询 | 启用 |
| TC017 | GetAdvancedSetting | 控制-查询 | 启用 |
| TC008 | SetBaseSetting | 控制-下发 | 启用 |
| TC010 | SetWorkModeSetting | 控制-下发 | 启用 |
| TC012 | SetBatterySetting | 控制-下发 | 启用 |
| TC014 | SetLoadControlSetting | 控制-下发 | 启用 |
| TC016 | SetPeakControlSetting | 控制-下发 | 启用 |
| TC018 | SetAdvancedSetting | 控制-下发 | 启用 |

## 控制类下发接口

下发接口会**真实修改设备参数**。当前已全部启用（`enabled=1`，随 18 个接口一起执行）；如只想跑查询类，把 `api_testdata.csv` 里对应下发行的 `enabled` 改成 `0`（或改 `tools/gen_api_cases.py` 里的 `"1"` 后重新生成）。

## 测试环境备份与恢复

下发测试会真实改设备参数，为防止参数被改导致设备损坏，框架**测试前自动备份、测试后自动恢复**：

- **备份**：collect 阶段探测设备后，自动调 6 个 Get\* 查询，把设备当前参数备份到 `common/backup/{device_sn}.json`。
- **恢复**：session 结束，自动读备份，调 6 个 Set\* 下发恢复参数（`SetAdvancedSetting` 的只读字段如 `coldStart`/`boxDisable` 会自动剔除）。
- 恢复结果打印在控制台末尾；备份文件跨会话保留，测试中途崩溃后也可手动恢复。
- 跳过恢复：`py -3 -m pytest tests/api -v --no-restore`。

恢复范围（6 类可下发参数）：BaseSetting / WorkModeSetting / BatterySetting / LoadControlSetting / PeakControlSetting / AdvancedSetting。

## 生成用例

用例清单可由接口文档批量生成/更新：

```bat
py -3 tools/gen_api_cases.py
```

生成脚本：`tools/gen_api_cases.py`，输出到 `data/api_testdata.csv`。
