---
name: reset-db
description: 重置 brapi-light 数据库到初始 demo 状态
---

## 用途

删除 brapi-light SQLite 数据库中所有数据，重新建表并插入初始 demo 数据。

## 执行

```bash
cd brapi-light && uv run python scripts/reset_db.py
```

## 注意事项

- 不需要先杀服务端 — 脚本直接操作 SQLite 文件
- 如果服务端正运行，重启后会读取新数据库
- 初始数据包含：1 Program, 1 Trial, 1 Study, 1 Location, 1 Season, 1 Person, 3 Variables, 3 ObservationUnits
