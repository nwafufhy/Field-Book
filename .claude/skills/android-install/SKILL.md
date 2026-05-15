---
name: android-install
description: 编译 fieldbook-android debug APK 并安装到设备。当用户说要"安装到手机"、"装到真机"、"编译安装"、"build and install"、"deploy APK"、"adb install"时使用。也用于构建完成后需要部署到设备验证的场景。
---

# Android 编译安装

编译 fieldbook-android debug APK，安装到目标设备，启动应用。

## 设备选择优先级

1. **真机优先** — 通过 `mcp__android-dev__device_list` 获取已连接设备，选非 emulator 的设备
2. 模拟器兜底 — 没有真机时用 emulator
3. 如果目标设备 TCP 断开，用 `mcp__android-dev__device_connect(host="<ip>")` 重连

## 执行步骤

### 1. 编译

```bash
cd D:/proj/Field-Book/fieldbook-android && ./gradlew app:assembleDebug
```

如果编译失败且报 XML 解析错误，先检查 `AndroidManifest.xml` 标签闭合再重试。

### 2. 安装

**必须使用 `outputs` 目录的 APK，不要用 `intermediates` 目录的**（intermediates 目录的 APK 可能缺少部分 ABI 原生库，导致 `INSTALL_FAILED_NO_MATCHING_ABIS`）。

```
mcp__android-dev__app_install(
  apk_path="D:/proj/Field-Book/fieldbook-android/app/build/outputs/apk/debug/app-debug.apk",
  device_id="<serial>",
  reinstall=true
)
```

### 3. 启动

Debug 包名带 `.debug` 后缀：

```
mcp__android-dev__app_launch(
  package_name="com.fieldbook.tracker.debug",
  device_id="<serial>"
)
```

## 常见问题

| 症状 | 原因 | 解决 |
|------|------|------|
| `INSTALL_FAILED_NO_MATCHING_ABIS` | APK 缺少设备架构的原生库 | 确认用的是 `outputs/apk/debug/` 而非 `intermediates/apk/debug/` |
| `device not found` | TCP 连接断开 | `mcp__android-dev__device_connect` 重连 |
| `No launchable activity` / 包名错误 | 错用了正式版包名 | Debug 版用 `com.fieldbook.tracker.debug` |
| `more than one device/emulator` | 多设备在线 | 所有操作带 `device_id` 参数 |

## 相关技能

- `android-harness` — MCP 工具详细用法（logcat、UI 操作、崩溃排查）
- `reset-db` — 重置后端数据库
