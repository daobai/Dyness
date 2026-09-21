---
name: api-testdata
description: 从接口文档生成 API 自动化测试数据（正常流 api_testdata.csv + 异常/边界/特殊参数 api_testdata_negative.csv），供 pytest 数据驱动执行。当用户要求为新接口生成/更新自动化测试数据、补充异常/边界用例时使用。
---

# API 自动化测试数据生成

## 目标

从接口文档生成 pytest 数据驱动测试所需的两个 CSV，由 `tests/api/test_api.py` 执行。覆盖正常流 + 异常/边界/特殊参数，断言严格以接口文档为准。

## 输出文件

| 文件 | 内容 | case_id 段 |
|------|------|-----------|
| `tests/api/data/api_testdata.csv` | 正常流（合法参数 → 预期 `code=200`） | TC001 起 |
| `tests/api/data/api_testdata_negative.csv` | 异常/边界/特殊参数（预期 `code=500`/`200`） | TC101 起 |

## 生成方式

更新生成脚本后重新生成 CSV：

```bat
py -3 tests/api/gen_api_cases.py           # 正常流
py -3 tests/api/gen_api_negative_cases.py  # 异常/边界
```

脚本：`tests/api/gen_api_cases.py`（正常流）、`tests/api/gen_api_negative_cases.py`（异常/边界）。

## 新增接口流程（分工）

新增一个接口时，**框架代码（test_api.py / assertions.py / device.py / backup.py / report.py）完全不用改**，只改两个 gen 脚本。

- **用户提供**：新接口文档（接口路径 + 参数定义：必填/选填、类型、取值范围、枚举、机型差异、嵌套字段），并说明是查询类还是下发类。
- **AI 改动**：
  1. 分析参数约束与机型适用性。
  2. 按本 skill 的测试设计规范设计用例（正常流 + 异常/边界/特殊参数）。
  3. `tests/api/gen_api_cases.py`：正常流加一条 `c(...)`。
  4. `tests/api/gen_api_negative_cases.py`：查询类接口在 `_DEVICE_SN_PATHS` 列表加一行（自动生成 deviceSn 异常）；下发类接口按参数补 `neg(...)` 边界/越界/枚举/必填缺失用例。
  5. 跑两个 gen 脚本重新生成 CSV，再跑 pytest 验证。

示例（新增查询接口 `/v2/GetNewThing`，仅 deviceSn 参数）：

- `gen_api_cases.py` 加：`c("TC019", "xxx查询", "/v2/GetNewThing", {"deviceSn": SN}, "$.code == 200", "查询类:xxx")`
- `gen_api_negative_cases.py` 的 `_DEVICE_SN_PATHS` 加：`("GetNewThing", "xxx查询")`（自动生成 deviceSn 不存在/空两条异常）

## CSV 字段

| 字段 | 说明 |
|------|------|
| case_id | 用例编号（正常 TC001~，异常 TC101~） |
| name | 用例标题 |
| method | 请求方法（本套接口全 POST） |
| path | 接口路径（如 `/v2/GetDeviceList`） |
| body | 请求体 JSON（模板变量 `{{deviceSn}}` 运行时替换） |
| expected_status | 预期 HTTP 状态码（默认 200） |
| expected_code | 预期业务码 `code`（正常 200，参数错误 500） |
| assertions | 断言表达式（JSONPath，`;` 分隔；异常用例可留空，靠 expected_code 判定） |
| description | 备注（正常/异常类型，如「边界外:xxx=999」） |
| enabled | 1 执行 / 0 跳过 |
| models | 机型限制（空=全机型；`AquaVolt,SolarCube`=仅这些机型） |

## 测试设计规范（实战要点）

### 参数取值：边界值 + 等价类，不照搬文档示例

- **禁止照搬文档示例值**——示例值可能超范围或笔误（如 `powerLevelSetting` 示例 `103` 超出声明范围 700~2000、`gridPowerLimitValue` 示例 `3000` 超出 0~800）。一律按字段「取值范围 / 枚举 / 步长」重新设计取值。
- **等价类代表值**：有效类内取中间值（范围 700~2000 → `1000`）。
- **边界值**（合法，预期 `200`）：最小值、最大值（`700`、`2000`）。
- **边界外**（非法，预期 `500`）：最小-1、最大+1（`699`、`2001`）。
- **步长约束**：文档声明「每 N 一档」时，补非挡位值（每 10W 一档 → `705`）。
- **枚举参数**：每个合法取值都要覆盖（`safetyCountry` 0/2/37/43/46/106 逐值验证）。
- **嵌套字段**：注意字段层级（如 `gridPowerLimitGroup.gridPowerLimitValue`），入参结构须与文档一致。

### 异常 / 特殊参数（预期 `500`）

- 资源不存在（`deviceSn` 不存在）
- 必填缺失（缺必填参数）
- 空字符串 / null / 类型错误（数字传字符串、字符串传数字）
- 格式错误（时间 `HH:mm`、`HH:mm-HH:mm` 等）
- 特殊字符 / 超长

### 预期业务码 code

| code | 含义 |
|------|------|
| 200 | success（请求成功） |
| 401 | Unauthorized（未授权） |
| 500 | Invalid Parameter（参数错误） |
| 429 | 限流（≤2 次/秒，批量执行需加请求间隔） |

### 断言与结果判定

- **断言严格以接口文档为准**：实际返回与文档不一致时，**不改断言迁就实际**，保持用例失败/待确认，由人工与开发确认是文档问题还是实现问题。
- 结果三分类：通过（响应与文档一致）/ 待确认（code 正常但字段与文档不一致）/ 不通过（HTTP 非 200、code 非预期、请求异常）。

### 机型差异

- 机型：AquaVolt / AquaVolt_LV / SolarCube。
- **查询接口（读方向）**：文档标注「某某系列：无」的字段，断言加机型前缀（如 `[AquaVolt,SolarCube] $.data.xxx exists`），执行时按当前机型自动裁剪。
- **下发接口（写方向）**：body 字段同样用 `[机型]` 前缀标记（如 `"[SolarCube] batteryOffGridChargeLimit": "70"`），执行时按当前机型自动剔除不适用的字段；整个接口只对某机型有意义时（参数基本全标「某某系列：无」），用 `models` 列限制该机型。不要写死单一机型、也不要一条 body 覆盖所有机型。

## 执行

```bat
py -3 -m pytest tests/api -v              # 全部（正常+异常）
py -3 -m pytest tests/api -k "TC1" -v     # 只跑异常/边界用例（case_id TC1xx）
```
