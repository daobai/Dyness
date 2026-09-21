# Dyness 储能设备测试工程

储能设备（电池 / BMS / PCS / 通信模块）测试脚本、自动化测试用例与测试工具汇总仓库（PyCharm 项目）。

## 目录结构

```
Dyness/
├── docs/                       # 文档
│   ├── requirements/           # 需求文档（PRD / 口述 / 禅道导出）
│   ├── interfaces/             # 接口文档（Open API Protocol 等）
│   └── devices/                # 设备信息文档（寄存器点表等）
├── cases/                      # 测试用例产出（禅道 CSV，按类型分类）
│   ├── api/  ├── app/  ├── ota/  └── web/
├── common/                     # 公共测试基础设施（脚本与日志/报告产物分开）
│   ├── report.py               #   报告生成脚本（HTML + JSON，供 api/modbus 复用）
│   ├── logs/                   #   测试日志（按月分目录，按天滚动，git 忽略）
│   └── reports/                #   测试报告产物（按天分目录，HTML/JSON，git 忽略）
├── tests/                      # pytest 自动化测试
│   ├── modbus/                 # Modbus 主站读写验证
│   └── api/                    # OpenAPI 数据驱动测试
│       ├── config/config.yaml  #   配置（域名/凭据/设备SN/超时）
│       ├── core/               #   API 专属公共库（签名/机型/加载/断言）
│       ├── data/               #   接口测试数据（正常流 api_testdata.csv + 异常 api_testdata_negative.csv + models.yaml）
│       ├── README.md           #   ★ API 测试框架详细文档（命令/功能）
│       ├── gen_api_cases.py    #   生成正常流测试数据 CSV
│       ├── gen_api_negative_cases.py  # 生成异常/边界测试数据 CSV
│       ├── conftest.py         #   参数化入口 + fixtures
│       └── test_api.py         #   执行脚本
├── tools/                      # 测试辅助工具 / 桩
│   └── modbus/                 # 多设备模拟器（从站桩）
├── requirements.txt            # 依赖
├── pytest.ini                  # pytest 配置
└── .claude/skills/             # 测试用例生成 skill（api/app/ota/web）
```

## 环境准备

- Python 3.14
- 安装依赖：`py -3 -m pip install -r requirements.txt`
  - `pymodbus` —— Modbus 通信
  - `pytest` —— 测试框架
  - `requests` —— HTTP 请求
  - `jsonpath-ng` —— 响应字段断言
  - `pyyaml` —— 配置解析

## Modbus 测试

1. 启动模拟器（从站桩，模拟多台储能设备，监听 502）：
   ```bat
   py -3 tools/modbus/modbus_multi_device.py
   ```
2. 另开窗口跑测试：
   ```bat
   py -3 -m pytest tests/modbus -v
   ```

寄存器点表见 [docs/devices/register-map.md](docs/devices/register-map.md)。

## OpenAPI 接口测试

基于 pytest 的数据驱动测试，覆盖 Dyness OpenAPI 六大产品线（户用储能 AquaVolt/AquaVolt_LV/SolarCube/SolarCube2、Cygni、高压电池、低压电池、Junior Box、工商业）的查询类 + 控制类接口，支持多设备机型自适应、HMAC-SHA1 自签名鉴权、按机型/模块/冒烟三种执行方式、完整报文日志与 HTML/JSON 报告。

- **详细文档、命令、框架说明** → [tests/api/README.md](tests/api/README.md)
- **接口清单与测试覆盖** → [docs/接口清单.md](docs/接口清单.md)
- **用例数据字段 / 断言语法** → [tests/api/data/README.md](tests/api/data/README.md)
- 接口协议 → [docs/interfaces/](docs/interfaces/)（各产品线 Open API Protocol 文档）

快速上手：

```bat
# 配置 tests/api/config/config.yaml 后运行
py -3 -m pytest tests/api -v                 # 跑全部
py -3 -m pytest tests/api --smoke            # 冒烟（核心查询，不跑下发）
py -3 -m pytest tests/api --module=commerce  # 按模块
py -3 -m pytest tests/api -k "GetBaseSetting" # 只跑某个接口
```

## 测试产物

| 产物 | 位置 | 说明 |
|------|------|------|
| 日志 | `common/logs/YYYYMM/api_test_YYYYMMDD.log` | 按月分目录、按天滚动，含完整请求/响应报文 |
| 报告 | `common/reports/YYYYMMDD/report_<时间戳>.html/.json` | 每天一个子目录，每次运行生成，含通过/待确认/不通过汇总 + 完整报文 |

两者均已加入 `.gitignore`，不进入版本控制。

## 工作流

| 环节 | 目录 | 说明 |
|------|------|------|
| ① 文档管理 | `docs/` | 需求 `requirements/`、接口 `interfaces/`、设备 `devices/` |
| ② 测试用例 | `cases/` | 用 skill 生成禅道可导入 CSV，按 api/app/ota/web 分类 |
| ③ 自动化测试 | `tests/` | pytest 可执行用例（modbus / api） |
| ④ 测试工具 | `tools/` | 模拟器、用例生成脚本等 |

> 跑全部测试：`py -3 -m pytest -v`（需模拟器已启动 + 网络可达）。
