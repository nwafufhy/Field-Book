# Field Book 作物表型数据采集标准工作流（BrAPI v2）

> 状态：草案 | 日期：2026-05-13

## 1. BrAPI v2 是什么

**BrAPI** (Breeding API) 是国际植物育种社区共同维护的 REST API 标准规范（[brapi.org](https://brapi.org)）。v2 是当前主流版本。

核心目标：让不同育种软件（Field Book、BreedBase、Germinate 等）通过统一接口互操作。Field Book 作为采集客户端，通过 BrAPI v2 协议与任意兼容后端通信。

本项目自建的 **brapi-light** 严格遵循 BrAPI v2 数据模型，实现了 Field Book 实际使用的 16 个端点（完整规范有 100+）。

## 2. BrAPI v2 核心规则

### 2.1 请求/响应约定

| 规则 | 说明 |
|------|------|
| 根路径 | 所有端点位于 `/brapi/v2/` 下 |
| 响应结构 | `{metadata: {pagination, status, datafiles}, result: {data: [...]}}` |
| 分页 | `metadata.pagination` 含 `pageSize`, `totalCount`, `totalPages` |
| 命名风格 | JSON 字段使用 camelCase（`studyDbId`、`observationUnitDbId`） |

### 2.2 数据实体层级

```
Program（育种项目）
  └── Trial（试验）
       └── Study（研究/田间试验）
            ├── ObservationUnit（观测单元 = 小区/植株）
            │    ├── ObservationUnitPosition（位置：重复/区块/行列）
            │    └── Observation（观测值）
            ├── ObservationVariable（观测变量 = trait + method + scale）
            └── Germplasm（种质/品种，种在每个 ObservationUnit 里）
```

### 2.3 本项目对 BrAPI 规范的取舍

- **已实现**：16 个端点（serverinfo, programs, trials, studies, observationunits, observationlevels, variables, observations CRUD, sync/changes, germplasm, images, OIDC）
- **不实现**：images 扩展 (PUT imagecontent 已完成)、samples、callsets、vendor、crosses 等 Field Book 不用的端点
- **简化**：SQLite 替代 PostgreSQL，单容器部署，OIDC 绕过（局域网场景）

### 2.4 图像支持

BrAPI v2 的 `/images` 端点设计为两步上传：
1. `POST /images` — 上传元数据（文件名、MIME 类型、关联的 observationUnitDbId）
2. `PUT /images/{imageDbId}/imagecontent` — 上传二进制内容

SQLite 通过 BLOB 列可存储图像二进制（单字段上限 2 GB），brapi-light 已实现此方案。

## 3. 标准采集流程（理论路径）

```
Step 1 — 部署后端
  Docker Compose 或 uvicorn 启动 brapi-light

Step 2 — Field Book 连接 BrAPI
  Settings → BrAPI → 填入 http://<服务器IP>:8000/brapi/v2 → Login (OIDC)

Step 3 — 导入 Study
  主界面 → Import → BrAPI → Studies → 选择 Program → Trial → Study → 导入

Step 4 — 导入 Traits（观测变量）
  主界面 → Traits → Import from BrAPI → 选择性状 → 导入

Step 5 — 配置观测单元
  进入 Study → 设置行列数/小区数 → 自动生成 Observation Units（Plot 1, Plot 2, ...）

Step 6 — 采集
  点击 Observation Unit → 选择 Trait → 录入值 → 保存

Step 7 — 同步
  自动：WorkManager 后台 1 分钟间隔（已集成）
  手动：Sync → Upload / Download
```

## 4. 当前项目状态

详见 `doc/prd.md`（需求基线）和 `doc/handoff-status.md`（进度追踪），本文档不做重复叙述。

## 5. 参考资料

| 资源 | 地址 |
|------|------|
| BrAPI v2 官方规范 | https://brapi.org/specification |
| BrAPI-FastAPI 参考实现 | https://github.com/agostof/BrAPI-FastAPI |
| Field Book 项目 | https://github.com/PhenoApps/Field-Book |
| 本项目 PRD | `doc/prd.md` |
| 本项目部署方案 | `doc/brapi-deploy-plan.md` |
| 前端调试日志 | `adb logcat -d \| grep -iE "BrAPI\|sync\|Error"` |
