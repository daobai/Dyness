# API 测试数据 CSV 字段说明

数据驱动测试从 `api_testdata.csv`（正常流）和 `api_testdata_negative.csv`（异常/边界/特殊参数）读取用例，逐条签名并发请求、断言。**用 Excel / WPS 编辑最方便**——在单元格里直接写 JSON 即可，保存为 CSV 时 Excel 会自动处理引号转义。

## 字段

| 字段 | 必填 | 说明 |
|------|------|------|
| case_id | 是 | 用例编号，唯一即可 |
| name | 是 | 用例标题 |
| method | 是 | GET / POST / PUT / DELETE / PATCH（本套接口全 POST） |
| path | 是 | 接口路径（如 `/v2/GetRealTimeDataBySN`），也支持完整 URL |
| headers | 否 | 额外请求头，JSON 对象，如 `{"X-Token":"abc"}` |
| params | 否 | query 参数，JSON 对象，如 `{"page":1,"size":10}` |
| body | 否 | 请求体，JSON 对象 |
| expected_status | 是 | 预期 HTTP 状态码，如 `200` |
| expected_code | 否 | 预期业务码（响应体 `code`），默认 `200`；异常用例填 `500` |
| assertions | 否 | 断言表达式，多条用 `;` 分隔（见下） |
| description | 否 | 备注 |
| enabled | 否 | `0` 表示跳过该条，默认 `1` 执行 |
| models | 否 | 机型限制：空=全机型；`AquaVolt,SolarCube`=仅这些机型跑该用例 |

## 断言表达式

每条格式：`<jsonpath> <操作符> [期望值]`，多条用 `;` 分隔。

| 操作符 | 示例 | 含义 |
|--------|------|------|
| == | `$.code == 200` | 相等（数字/布尔/null 自动识别） |
| != | `$.code != 0` | 不等 |
| > >= < <= | `$.data.total > 0` | 数值比较 |
| contains | `$.info contains Success` | 字符串包含 / 列表包含 |
| in | `$.workStatus in 0,1,2` | 值在某集合（逗号分隔） |
| exists | `$.data.soc exists` | 字段存在 |
| not_exists | `$.error not_exists` | 字段不存在 |

JSONPath 示例：

- `$.code` —— 根对象下的 code
- `$.data[0].id` —— data 数组第一个元素的 id
- `$[0].title` —— 响应本身是数组时，第一个元素的 title
- `$.data.batteryInfo.soc` —— 嵌套对象取值

### 机型前缀

某字段只在部分机型上返回时（接口文档里标「某某系列：无」），给断言加机型前缀；当前设备机型不在列表里则自动跳过该条断言：

```
$.code == 200;[AquaVolt,SolarCube] $.data.onGridDischargeDod exists
```

不带前缀 = 全机型通用。

### 断言结果三分类

- 断言全部通过（HTTP 200 + code=200）→ **通过 PASS**
- HTTP 200 且 code=200，但字段与文档不符 → **待确认 PENDING**（人工与开发确认）
- HTTP 非 200 / code 非 200 / 响应体非法 / 请求异常 → **不通过 FAIL**

断言字段严格以接口文档为准，实际返回与文档不符时保持文档断言、让用例进入「待确认」，不迁就实际。

## 鉴权（Dyness OpenAPI 自签名）

接口采用 HMAC-SHA1 自签名鉴权，框架在每次请求时自动生成 `Content-MD5`、`Date`、`Authorization` 头，**无需在 CSV 里手写鉴权信息**。

## 配置（域名 / 应用凭据 / 设备 SN / 超时）

配置放在 `tests/api/config/config.yaml`，也可在运行时覆盖，优先级：

**命令行参数 > 环境变量 > config.yaml**

| 配置项 | 命令行 | 环境变量 | config.yaml |
|--------|--------|----------|-------------|
| 接入域名 | `--base-url` | `API_BASE_URL` | `api.base_url` |
| 应用 ID | `--app-id` | `API_APP_ID` | `api.app_id` |
| 应用密钥 | `--app-secret` | `API_APP_SECRET` | `api.app_secret` |
| 设备序列号 | `--device-sn` | `API_DEVICE_SN` | `api.device_sn` |
| 超时(秒) | `--timeout` | `API_TIMEOUT` | `api.timeout` |
| 请求间隔(秒) | `--request-interval` | `API_REQUEST_INTERVAL` | `api.request_interval` |
| 机型 | `--model` | `API_MODEL` | `api.model`（留空=自动探测，可手动指定兜底） |

示例：

```bat
py -3 -m pytest tests/api -v --app-id=xxx --app-secret=xxx --device-sn=SN1,SN2,SN3
```

## 多设备 + 机型自动识别

- `device_sn` 支持**多台**：逗号分隔字符串或 YAML 列表；留空=测账号下全部设备。
- 跑前框架调 `GetDeviceList` 自动探测每台设备的机型（`deviceModel` → AquaVolt / AquaVolt_LV / SolarCube），用例 × 设备矩阵执行。
- 机型归一化映射在 `tests/api/data/models.yaml`，**新增机型时在此追加别名/硬件型号即可**，无需改代码。
- 探测失败（网络不通/鉴权错/SN 无效）→ 该台降级为「只跑通用用例」；全部失败 → 整体 skip。
- 已知机型会自动跳过 `models` 列不匹配的用例、跳过机型前缀不匹配的断言。

## 模板变量 {{deviceSn}}

CSV 里 body 的 `{{deviceSn}}` 会在运行时替换成**当前被测设备**的 SN（多设备时逐台替换），无需在 CSV 里写死。

## 控制类下发用例

下发类接口会**真实修改设备参数**。当前已全部启用（`enabled=1`）；如只想跑查询类，把对应下发行的 `enabled` 改成 `0` 再跑。

## 编辑提示

- 文件编码 UTF-8。
- JSON 字段（headers / params / body）在 Excel 里直接写 `{"a":1}` 即可，不用管转义。
- 若用文本编辑器手写，JSON 里的双引号要写成 `""`（CSV 标准转义）。
- 用例也可用 `py -3 tools/gen_api_cases.py` 重新生成（基于接口文档的完整清单）。
