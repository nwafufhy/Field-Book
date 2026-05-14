# Field Book — 田间表型多人协作采集系统

基于 [PhenoApps/Field-Book](https://github.com/PhenoApps/Field-Book) (v7.2.1) 的二次开发分支，新增 BrAPI v2 后端、中文汉化、多人实时协作采集。

[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

## 仓库结构

```
Field-Book/                    # 伞形仓库
├── fieldbook-android/         # Android 采集 App (Kotlin/Java)
├── brapi-light/               # BrAPI v2 后端 (Python/FastAPI/SQLite)
├── docker/                    # Docker Compose 部署
├── doc/                       # PRD、部署计划、测试清单
└── .claude/                   # AI 开发辅助 (skills/agents)
```

| 子项目 | 技术栈 | 说明 |
|--------|--------|------|
| **fieldbook-android** | Kotlin/Java, Gradle | 田间表型数据采集 Android App，含 WorkManager 自动同步 |
| **brapi-light** | Python 3.11+, FastAPI, SQLite | 轻量 BrAPI v2 后端，替换 BreedBase，支持多人协作 |

## 相比上游的新增功能

- **BrAPI v2 后端 (brapi-light)**: 16 个端点，乐观锁增量同步，Docker 部署
- **中文汉化**: 覆盖率 99%，默认语言中文
- **WorkManager 自动同步**: 后台定期同步，间隔 1 分钟
- **字段级冲突检测**: 支持多人并发编辑
- **BrAPI v2 图片同步**: 照片/视频性状上传下载全流程

## 快速开始

### Android App

用 Android Studio 打开 `fieldbook-android/` 目录构建。

```bash
cd fieldbook-android
./gradlew app:assembleDebug
```

### brapi-light 后端

```bash
cd brapi-light
uv sync --extra dev
uv run uvicorn brapi_light.main:app --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
cd docker
docker compose up -d    # brapi-light 服务 → 端口 38000
```

## 开发流程

```
PRD 特性 ID → GitHub Issue → Worktree 隔离 → TDD (红-绿-重构) → Commit → PR
```

详见 `doc/prd.md` 和 [GitHub Issues](https://github.com/nwafufhy/Field-Book/issues)。

## 当前状态

- **Milestone**: v1.0.0 — 17 个 open Issue
- **brapi-light**: 53 测试通过，0 lint 错误
- **汉化**: 99% 覆盖率 (Issue #1)
- **进行中**: WebSocket 实时协同 (#21)、SSE 推送 (#20)、麦穗识别 ONNX (#3-#7)

## 上游项目

Field Book 是一款田间表型数据采集 App，由 PhenoApps 团队开发。支持自定义布局、BrAPI 数据交换、多语言。

- [用户手册](https://fieldbook.phenoapps.org/#/)
- [Google Play](https://play.google.com/store/apps/details?id=com.fieldbook.tracker)
- [上游仓库](https://github.com/PhenoApps/Field-Book)

## 贡献者

感谢上游 PhenoApps/Field-Book 的所有[贡献者](https://github.com/PhenoApps/Field-Book#%E2%9C%A8-contributors)。

## 许可证

GPL v2 — 与上游保持一致。
