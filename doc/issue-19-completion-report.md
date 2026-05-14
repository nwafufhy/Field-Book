## 完成报告 — Issue #19

### 根因

BrAPI images 端点在 Field Book → brapi-light 链路上存在 **4 个独立问题**，分别影响兼容性检查、功能完整性、同步逻辑和数据上传：

| # | 问题 | 根因 | 影响 |
|---|------|------|------|
| 1 | 兼容性检查显示 false | `server_info.py` 只声明了顶层 `"images"` 资源，Android 用精确字符串匹配查找 `"images/{imageDbId}"` 和 `"images/{imageDbId}/imagecontent"` | 3 个子端点显示为不支持 |
| 2 | PUT images/{imageDbId} 缺失 | 服务端未实现图片元数据更新端点 | 编辑图片元数据时 404 |
| 3 | 自建 camera trait 不同步 | `SyncWorker` 和 `BrapiSyncViewModel` 只处理普通 observation，忽略所有 image 分类（`newImageObservations`、`userCreatedImageObservations`）；且 image 观察被分类到独立桶后完全绕过了 POST /observations 通道 | camera 数据从不同步，服务端无 observation 和 variable 记录 |
| 4 | POST /images 返回 500 | Android 发送 `descriptiveOntologyTerms` 等字段，Image 模型无对应列，`**dict` 直接传入 SQLAlchemy 构造器报错 | 图片元数据上传失败 |

### 修复内容

**brapi-light (3 个 commits)**

| 文件 | 改动 |
|------|------|
| `routers/server_info.py:83-94` | 新增 `images/{imageDbId}` (GET/PUT) 和 `images/{imageDbId}/imagecontent` (GET/PUT) 端点声明 |
| `routers/phenotyping.py:302-316` | 新增 `PUT /brapi/v2/images/{image_db_id}` 路由，接收 JSON body 更新图片元数据 |
| `routers/phenotyping.py:225-234` | POST /images 增加 `allowed` 白名单过滤 (`Image.__table__.columns`)，过滤未知字段 |
| `services/phenotyping.py:196-209` | 新增 `update_image_metadata()`，白名单方式更新 `image_file_name`、`description`、`mime_type` 等字段 |
| `tests/test_images.py:153-182` | 新增 `test_images_put_metadata` 和 `test_images_put_metadata_404` |

**fieldbook-android (2 个 commits)**

| 文件 | 改动 |
|------|------|
| `SyncWorker.kt:61-117` | 新增图片上传逻辑（POST metadata + PUT content / PUT metadata + PUT content）；image 观察类别（`newImageObservations`、`userCreatedImageObservations`、`editedImageObservations`、`incompleteImageObservations`）全部合并到 observation 上传通道 |
| `BrapiSyncViewModel.kt:145-152` | `newObservations` 合并 `newImageObservations` + `userCreatedImageObservations`；`newImageObservations` 合并 `userCreatedImageObservations`；`editedObservations` 合并 `editedImageObservations` |

**核心架构修正**: Camera 观察现在走**双通道**：元数据（变量名、值、时间戳）→ POST /observations，图片二进制 → POST /images + PUT content。与普通 trait 共享 observation 上传通道，仅在图片二进制传输时走 image 特殊通道。

### 验证方式

1. 创建 camera 类型 trait → 拍照录入 → 手动同步 → 显示 "N 条待上传观测值" + "N 张待上传图片"
2. 同步完成后检查服务端数据库：`observation` 表有记录、`observation_variable` 表有 camera trait、`image` 表有图片
3. 另一设备 import → 图片随数据一起下载
4. brapi-light 测试: 68/68 passed
5. GET /brapi/v2/serverinfo 确认三个 images 端点声明就绪

### 留下的坑

- 上传的 observation value 为本地 content:// URI，服务端存储后 import 回来时 value 为失效的路径（图片二进制通过 image 通道单独处理，不影响使用）
- **Issue #24**: 自建 trait 类型信息丢失（数值型 → 文本型），待 Server 端新增 POST /variables 或 import 端保留本地 format 设置后修复
