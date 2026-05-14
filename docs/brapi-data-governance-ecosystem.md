# BrAPI 数据治理生态：标准体系全景

> 日期：2026-05-13 | 版本：v1.0

## 摘要

BrAPI 并非孤立协议。它下面有一套完整的 三层标准栈：

```
应用层    BrAPI v2/v2.1  ← REST 交换协议（怎么传数据）
语义层    Crop Ontology   ← 性状词典（数据叫什么、怎么测）
元数据层  MIAPPE          ← 实验描述规范（实验怎么做的、上下文是什么）
```

全部标准的内核是 **FAIR 数据原则**（Findable, Accessible, Interoperable, Reusable）。

---

## 1. 标准层级全景

```
                        ┌──────────────────┐
                        │    FAIR 原则      │
                        └────────┬─────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
       │   MIAPPE      │  │ Crop Ontology│  │  配套本体     │
       │  实验元数据    │  │ 性状标准词典  │  │ PO/TO/PATO   │
       └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 ▼
                        ┌──────────────────┐
                        │  BrAPI v2/v2.1   │
                        │  数据交换协议      │
                        └──────────────────┘
```

---

## 2. Crop Ontology (CO) — 作物本体论

### 2.1 概述

**CGIAR** 主导的社区标准，由 Generation Challenge Programme (GCP) 和 Integrated Breeding Platform (IBP) 孵化。托管在 [cropontology.org](https://cropontology.org)。

**解决的问题**：同名异义、异名同义。"株高"在不同作物、不同国家、不同试验站叫法完全不同。CO 给每个性状一个全球唯一的 `CO_` 前缀 ID。

### 2.2 变量结构

与 BrAPI 的 `ObservationVariable` 模型直接对应：

```
ObservationVariable（标准变量）
  ├── trait / property（性状/属性：如 "株高" → 映射到 TO、PO）
  ├── method（测量方法：如 "米尺测量"）
  └── scale（尺度类型：数值/分类/序数 + 单位）
```

每个标准变量获得一个 **CO ID**，格式为 `CO_XXX:NNNNNNNNNN`，如 `CO_321:0000700`（小麦株高）。

### 2.3 覆盖范围

**20+ 种作物**：小麦、水稻、玉米、大麦、大豆、马铃薯、甘薯、木薯、香蕉、鹰嘴豆、菜豆、豇豆、花生、小扁豆、珍珠粟、木豆、高粱、燕麦、山药、葡萄。

### 2.4 外部本体映射

CO 术语交叉引用以下参考本体：

| 本体 | 全称 | 用途 |
|------|------|------|
| PO | Plant Ontology | 植物解剖结构、发育阶段 |
| TO | Trait Ontology (Gramene) | 植物性状通用分类 |
| PATO | Phenotypic Quality Ontology | 性状表现型质量 |
| CHEBI | Chemical Entities of Biological Interest | 化学成分 |
| EO | Environment Ontology | 环境条件 |
| GO | Gene Ontology | 基因功能 |
| PECO | Plant Experimental Conditions Ontology | 实验条件/处理 |

### 2.5 治理机制

正式治理框架（Arnaud et al., 2022）包含 8 条原则：**完整性、透明性、问责制、所有权、管理权、标准化、变更管理、数据审计**。

提交流程：育种者用 Trait Dictionary Template（Excel）提交 → 社区 curator 审核 → 分配 CO ID → 映射到外部本体 → 发布。

### 2.6 与 BrAPI 的关系

BrAPI 的 `/brapi/v2/variables` 端点返回的 `ObservationVariable`，其 `trait.traitDbId`、`trait.traitName` 字段期望引用 CO 的 trait 定义。CO 是 BrAPI 的"语义数据库"。

---

## 3. MIAPPE — 植物表型实验最小信息标准

### 3.1 概述

由 **ELIXIR、INRAE、IPK Gatersleben** 等欧洲机构维护的开源社区标准。

- **官网**：[miappe.org](https://www.miappe.org)
- **GitHub**：[github.com/MIAPPE/MIAPPE](https://github.com/MIAPPE/MIAPPE)

**解决的问题**：仅有性状数据不足以支撑复用——必须知道实验在什么条件下做的。MIAPPE 定义了描述一个植物表型实验所需的 **最少元数据集**。

### 3.2 版本演进

| 版本 | 年份 | 关键变化 |
|------|------|----------|
| v1.0 | 2015 | transPLANT 项目产出，Krajewski et al. (J Exp Bot) |
| v1.1 | 2019 | ELIXIR 主导，扩展至木本植物/大田/温室，增加显式数据模型、本体推荐、ISA-Tab 兼容、BrAPI 互操作 (Papoutsoglou et al., New Phytol) |
| v1.2 | 审核中 | 文档澄清、字段补充 |
| v2.0 | 筹备中 | NFDI4Biodiversity 项目，2026-2027 推进 |

### 3.3 11 个标准章节

| # | 章节 | 内容 |
|---|------|------|
| 1 | 通用元数据 | 项目名称、负责人、机构、发表信息 |
| 2 | 生物源 | 植物材料来源、品种/品系、种质 ID |
| 3 | 实验设计 | 时间、地点、目的、田间布局（重复/区块）、种植密度 |
| 4 | 处理 | 灌溉、施肥、化学处理等 |
| 5 | 样品管理 | 取样策略、运输、储存 |
| 6 | 环境 | 大田/温室/生长箱的总体环境描述 |
| 7 | 环境变量 | 温度、湿度、光照、CO₂（定量 + 时序） |
| 8 | 表型 | 测量的性状（引用 CO 变量）、方法、时间点 |
| 9 | 实验设置 | 仪器、设施 |
| 10 | 自变量 | 研究者控制的操作变量 |
| 11 | 数据文件 | 原始文件、格式、校验和 |

### 3.4 技术实现

| 格式 | 用途 |
|------|------|
| PDF 清单 | 人类阅读 |
| Excel 模板 | 手动填写 |
| ISA-Tab / ISA JSON | 数据集提交、机器验证 |
| PPEO (OWL/RDF) | 语义推理、知识图谱查询 |
| JSON Schema | 开发中 |
| BrAPI v2 端点 | 数据交换层 |

### 3.5 PPEO — 机器可读版本

**Plant Phenotype Experiment Ontology** 是 MIAPPE 的 OWL 编码，支持自动验证和语义查询。PPEO 将 MIAPPE 的 11 个章节映射为可推理的 RDF 类/属性，使得 MIAPPE 可以嵌入语义知识图谱。

### 3.6 与 BrAPI 的关系

MIAPPE 描述"实验是什么/怎么做的"，BrAPI 负责"数据怎么传输"。两者互补，已实现完全互操作：

- BrAPI 的 `Study` 对象可以携带 MIAPPE 推荐的环境和处理元数据
- BrAPI 的 `ObservationVariable` 引用 CO 定义的变量，满足 MIAPPE 第 8 章要求
- FAIDARE 门户已索引约 30 个数据库，使用 BrAPI 或 MIAPPE 最小格式

---

## 4. 配套标准

### 4.1 AgrO — 农艺本体

正在开发中的农艺管理实践标准，基于 **ICASA** 标准编译约 350 个变量，覆盖整地、播种、灌溉、施肥、除草、收获等田间操作。与 CO 互补——CO 描述植物性状，AgrO 描述人对田块做了什么。

### 4.2 参考本体全表

| 缩写 | 全称 | 域 |
|------|------|-----|
| PO | Plant Ontology | 植物解剖、发育 |
| TO | Trait Ontology | 性状通用分类 |
| PATO | Phenotypic Quality Ontology | 表型质量 |
| PECO | Plant Experimental Conditions | 实验条件 |
| EO | Environment Ontology | 环境描述 |
| CHEBI | Chemical Entities | 化学物质 |
| GO | Gene Ontology | 基因功能 |
| CRO | Crop Research Ontology | 实验设计 |
| IAO | Information Artifact Ontology | 信息实体 |
| UO | Units Ontology | 计量单位 |

---

## 5. FAIR 数据原则

所有上述标准的共同内核。

| 字母 | 含义 | MIAPPE 如何满足 | BrAPI 如何满足 |
|------|------|----------------|---------------|
| **F**indable | 可发现 | DOI、唯一标识符、元数据索引 | `/serverinfo` 端点、OIDC |
| **A**ccessible | 可访问 | 开放协议、持久存储 | REST API、标准 HTTP 认证 |
| **I**nteroperable | 可互操作 | CO 变量引用、ISA-Tab 格式 | JSON 标准格式、camelCase 约定 |
| **R**eusable | 可复用 | 完整的实验上下文元数据 | `externalReferences`、详细的 provenance |

---

## 6. 最新动态（2025-2026）

| 事件 | 时间 | 意义 |
|------|------|------|
| **BrAPI v2 论文发表** | 2025-09 | 60+ 作者，首次在学术期刊系统论证 BrAPI 在真实育种场景的应用价值 |
| **DeltaBreed 发布** | 2025-12 | 首个完全 BrAPI 驱动的育种数据管理系统（USDA-ARS），使用 BrAPI v2.1 Java Test Server 作为主数据库 |
| **ISO/TC 347 成立** | 2023 | ISO 正式介入数据驱动农食系统标准，范围覆盖 agrisemantics |
| **NFDI4Biodiversity 启动** | 2026-01 | MIAPPE v2.0 推进，目标融合 Semantic Web / Bioschemas |
| **Voral et al. 综述** | 2026-03 | 系统性回顾 MIAPPE + BrAPI + HPC 融合路径，指出数据治理和语义对齐是当前最大缺口 |

---

## 7. 对本项目的启示

### 7.1 当前对齐程度

brapi-light 已经在数据模型层面暗合了 CO 的变量结构：

```python
# brapi-light 的 ObservationVariable 模型
Variable:
  trait_db_id    # ← 对应 CO_xxx:xxxxxxxx 标准性状 ID
  trait_name     # ← 对应 CO trait/property 名称
  method_name    # ← 对应 CO method
  scale_name     # ← 对应 CO scale 类型
```

### 7.2 可推进的治理增强（按优先级）

1. **引入 CO ID** — 在 `trait` 中填入标准 CO 编号（`CO_321:0000700`），使性状数据可跨系统互操作
2. **MIAPPE 元数据支持** — 在 `Study`/`Trial` 层级增加 MIAPPE 必填字段（实验设计类型、环境描述、处理信息），使数据集可发表
3. **作物本体映射** — `commonCropName` 映射到 CO 物种代码，`observationLevel` 映射到 PO 植物结构术语
4. **PPEO 导出** — 生成 MIAPPE 兼容的 RDF/JSON-LD，使 brapi-light 数据集可被 FAIDARE 等门户索引

### 7.3 生产级参考工具

| 工具 | 链接 | 说明 |
|------|------|------|
| BrAPI Test Server (Java) | [brapi.org](https://brapi.org) | BrAPI 参考实现，v2.1 |
| BrAPI-FastAPI (Python) | [GitHub](https://github.com/agostof/BrAPI-FastAPI) | brapi-light 的参考桩 |
| MIAPPE Validator | [miappe.org](https://www.miappe.org) | 数据集 MIAPPE 合规检查 |
| Crop Ontology Trait Dictionary | [cropontology.org](https://cropontology.org) | 按作物浏览 CO 标准变量 |
| ELIXIR Plant Phenotyping | [elixir-europe.org](https://elixir-europe.org) | 培训教材、社区活动 |
| DeltaBreed | USDA-ARS (Breeding Insight) | 生产级 BrAPI 数据管理系统 |

---

## 8. 参考资料

- Selby P., et al. (2025). "BrAPI v2: real-world applications for data integration and collaboration in the breeding and genetics community." *Database*, baaf048. [DOI](https://doi.org/10.1093/database/baaf048)
- Yarnes S., et al. (2025). "DeltaBreed: A BrAPI-centric breeding data information system." *PLoS ONE*, e0324104. [DOI](https://doi.org/10.1371/journal.pone.0324104)
- Papoutsoglou E., et al. (2020). "Enabling reusability of plant phenomic datasets with MIAPPE 1.1." *New Phytologist*, 227(1):260-273. [DOI](https://doi.org/10.1111/nph.16544)
- Krajewski P., et al. (2015). "Towards recommendations for metadata and data handling in plant phenotyping." *Journal of Experimental Botany*, 66(18):5417-5427. [DOI](https://doi.org/10.1093/jxb/erv271)
- Arnaud E., et al. (2022). "Crop Ontology Governance and Stewardship Framework." *FAO AGRIS*.
- Voral et al. (2026). "Standardized Data Infrastructures for Plant Phenomics: A Review of MIAPPE and BrAPI Integration within High-Performance Computing Frameworks." *AGRIS on-line*, 18(1). [DOI](https://doi.org/10.7160/aol.2026.180109)
- [MIAPPE 官网](https://www.miappe.org)
- [Crop Ontology 官网](https://cropontology.org)
- [BrAPI 官网](https://brapi.org)
