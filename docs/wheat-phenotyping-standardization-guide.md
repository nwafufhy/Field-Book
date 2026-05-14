# 小麦表型标准化采集实现指南

> 日期：2026-05-13 | 版本：v1.0

## 1. 场景定义

**作物**：小麦 (Wheat, Triticum aestivum)
**采集内容**：

| 类别 | 指标 | 采集方式 |
|------|------|----------|
| 农艺性状 | 株高 (Plant Height) | 手持设备 / 米尺 |
| 生理性状 | SPAD (叶绿素相对含量) | SPAD-502 手持叶绿素计 |
| 冠层性状 | LAI (叶面积指数) | LAI-2200 / 半球摄影 |
| 遥感影像 | RGB + 多光谱 (多波段反射率) | 无人机 (UAV) |
| 植被指数 | NDVI, NDRE, EVI 等 | 多光谱正射影像后处理 |

---

## 2. 性状标准化映射 (CO_321)

### 2.1 你的性状 → CO ID

| 你的测量项 | CO_321 变量名 | 变量 ID | 方法 ID | 单位/范围 |
|-----------|--------------|---------|---------|-----------|
| **株高** | Plant height (PTHT) | `CO_321:0000020` | — | cm, 0-250 |
| **SPAD** | Chlorophyll content | `CO_321:0000028` | `CO_321:0000249` (SPAD method) | SPAD 值, 0-50 |
| **LAI** | Leaf area index | `CO_321:0000184` | — | 无量纲 (m²/m²) |
| **NDVI** | Canopy NDVI | `CO_321:0000301` | drone/spectral estimation | 0-1 |
| **生物量** | Above-ground biomass | `CO_321:0001431` | — | g/m² 或 kg/ha |
| **旗叶面积** | Flag leaf area | `CO_321:0000141` | — | cm² |
| **叶绿素荧光** | Chlorophyll fluorescence | `CO_321:0000028` | Fv/Fm 方法 | 0-1 |

### 2.2 BrAPI ObservationVariable 建模

以株高为例，这是你在 brapi-light 的 `brapi.db` 中应该写入的 JSON 结构：

```json
{
  "observationVariableDbId": "CO_321:0000020",
  "observationVariableName": "Plant height",
  "trait": {
    "traitDbId": "CO_321:0000020",
    "traitName": "Plant height",
    "description": "Representative height of the plant measured from ground to spike, excluding awns",
    "synonyms": ["PTHT", "plant_height"],
    "mainAbbreviation": "PTHT",
    "entity": "plant",
    "attribute": "height",
    "status": "recommended"
  },
  "method": {
    "methodDbId": "CO_321:0001150",
    "methodName": "Ruler measurement from ground to spike tip",
    "description": "Manual measurement using a meter stick",
    "methodClass": "measurement",
    "bibliographicalReference": "CIMMYT Wheat Trait Dictionary"
  },
  "scale": {
    "scaleDbId": "CO_321:0001149",
    "scaleName": "centimeter",
    "dataType": "numeric",
    "validValues": {
      "minimumValue": 0,
      "maximumValue": 250,
      "categories": []
    },
    "decimalPlaces": 1
  },
  "defaultValue": null,
  "synonyms": ["PTHT", "plant_height_cm"],
  "documentationURL": "https://cropontology.org/term/CO_321:0000020",
  "language": "en",
  "commonCropName": "Wheat",
  "contextOfUse": ["breeding", "research"],
  "institution": "CIMMYT",
  "scientist": "Rosemary Shrestha"
}
```

以 SPAD 为例：

```json
{
  "observationVariableDbId": "CO_321:0000028__CO_321:0000249",
  "observationVariableName": "Leaf greenness (SPAD)",
  "trait": {
    "traitDbId": "CO_321:0000028",
    "traitName": "Chlorophyll content",
    "description": "Relative chlorophyll content estimated by SPAD-502 meter",
    "synonyms": ["CLPHYL", "SPAD", "leaf_greenness"],
    "mainAbbreviation": "CLPHYL",
    "entity": "leaf",
    "attribute": "chlorophyll content",
    "status": "recommended"
  },
  "method": {
    "methodDbId": "CO_321:0000249",
    "methodName": "SPAD-502 chlorophyll meter reading",
    "description": "Handheld SPAD-502 (Konica Minolta) non-destructive measurement on flag leaf",
    "methodClass": "measurement",
    "bibliographicalReference": "https://cropontology.org/term/CO_321:0000249"
  },
  "scale": {
    "scaleDbId": "SPAD_scale",
    "scaleName": "SPAD unit",
    "dataType": "numeric",
    "validValues": {
      "minimumValue": 0.0,
      "maximumValue": 60.0,
      "categories": []
    },
    "decimalPlaces": 1
  },
  "commonCropName": "Wheat",
  "contextOfUse": ["breeding", "physiology", "high-throughput phenotyping"]
}
```

### 2.3 BrAPI trait + method + scale 设计原则

```
ObservationVariable
  ├── trait    → "测什么"     (property, entity + attribute)
  ├── method   → "怎么测"     (instrument, protocol)
  └── scale    → "值是什么"   (numeric/categorical/ordinal + units + range)
```

**关键规则**：
- 同一 trait 配合不同 method 产生不同的 ObservationVariable（例如 CO_321:0000028 配 SPAD vs 配乙醇提取法）
- `observationVariableDbId` 可用 `{traitId}__{methodId}` 组合编码，确保唯一性
- 不要改变客户端发来的 DbId 值（BrAPI 协议陷阱之一）

---

## 3. 无人机多光谱影像标准化

### 3.1 数据流全景

```
无人机飞行（DJI / Parrot / 自组）
  │
  ├── 原始影像 (RAW / TIFF)
  │    └── 按波段分文件: RED.tif, NIR.tif, REDEDGE.tif, GREEN.tif, BLUE.tif
  │
  ├── 摄影测量处理 (Agisoft Metashape / ODM / Pix4D)
  │    └── 输出: 正射影像 (GeoTIFF), DSM/DTM, 点云
  │         ├── RGB 正射影像 (orthomosaic_rgb.tif)
  │         └── 多光谱反射率地图 (orthomosaic_multispectral.tif)
  │
  ├── GIS 处理 (QGIS / Python rasterio)
  │    ├── 小区边界矢量化 (polygon shapefile → GeoJSON)
  │    ├── 植被指数计算 (NDVI, NDRE, EVI, OSAVI...)
  │    └── 分区统计 (zonal statistics → 每个 plot 的 mean/max/min NDVI)
  │
  └── BrAPI 入库
       ├── POST /images          → 正射影像元数据 + GeoJSON 边界
       ├── POST /observations    → 每个 plot 的 NDVI 均值 (关联 observationVariable "CO_321:0000301")
       └── MIAPPE 元数据         → 关联传感器、飞行参数、处理流程
```

### 3.2 BrAPI Images 端点 — 无人机影像建模

**正射影像**（覆盖整个试验田）：

```json
POST /brapi/v2/images
{
  "imageFileName": "orthomosaic_multispectral_fieldA_2026-05-10.tif",
  "mimeType": "image/tiff",
  "imageFileSize": 524288000,
  "imageWidth": 12000,
  "imageHeight": 8000,
  "imageTimeStamp": "2026-05-10T10:30:00Z",
  "description": "Multispectral orthomosaic of Field A wheat trial. 5 bands: R,G,B,RE,NIR. Altitude 50m.",
  "imageLocation": {
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [116.301, 39.952, 50],
        [116.304, 39.952, 50],
        [116.304, 39.949, 50],
        [116.301, 39.949, 50],
        [116.301, 39.952, 50]
      ]]
    }
  },
  "descriptiveOntologyTerms": [
    "UAV", "drone", "multispectral",
    "orthomosaic", "geotiff",
    "MicaSense RedEdge", "DJI P4 Multispectral"
  ],
  "copyright": "CC-BY 4.0 - Wheat Phenomics Lab 2026",
  "additionalInfo": {
    "flightAltitude_m": 50,
    "groundSamplingDistance_cm": 2.5,
    "bands": ["blue_475", "green_560", "red_668", "rededge_717", "nir_840"],
    "radiometricCalibration": "Reflectance panel (MicaSense CRP)",
    "processingSoftware": "Agisoft Metashape 2.1",
    "crs": "EPSG:4326"
  }
}
```

**单小区多光谱影像**（每个 plot 一个 polygon）：

```json
POST /brapi/v2/images
{
  "imageFileName": "plot_0042_multispectral_2026-05-10.tif",
  "mimeType": "image/tiff",
  "observationUnitDbId": "plot_0042",
  "imageTimeStamp": "2026-05-10T10:32:15Z",
  "imageLocation": {
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[
        [116.3021, 39.9512],
        [116.3023, 39.9512],
        [116.3023, 39.9510],
        [116.3021, 39.9510],
        [116.3021, 39.9512]
      ]]
    }
  },
  "observationDbIds": ["obs_ndvi_plot42"],
  "descriptiveOntologyTerms": ["plot", "multispectral", "UAV", "GeoTIFF"]
}
```

### 3.3 植被指数作为 Observation 入库

NDVI 不是直接测量值，而是从多光谱影像**计算**出的指数。BrAPI 中应对应为一个 Observation：

```json
POST /brapi/v2/observations
[
  {
    "observationDbId": "obs_ndvi_plot42_20260510",
    "observationUnitDbId": "plot_0042",
    "observationVariableDbId": "CO_321:0000301",
    "observationVariableName": "Canopy NDVI",
    "observationTimeStamp": "2026-05-10T10:30:00Z",
    "value": "0.72",
    "season": "2026-Spring",
    "collector": "Drone Team",
    "externalReferences": [
      {
        "referenceID": "orthomosaic_multispectral_fieldA_2026-05-10.tif",
        "referenceSource": "BrAPI Images"
      }
    ]
  }
]
```

### 3.4 多光谱变量的 CO 映射建议

目前 CO_321 已有 NDVI 术语，但部分植被指数尚在候选阶段。对于 CO 尚未覆盖的指数，策略是：

| 植被指数 | CO 状态 | 策略 |
|---------|---------|------|
| NDVI | ✅ `CO_321:0000301` | 直接引用 |
| NDRE | ⚠️ 候选 | 使用 `CO_321:0000301` + method="RedEdge NDVI" |
| EVI | ⚠️ 候选 | 使用 `CO_321:0000301` + method="Enhanced Vegetation Index" |
| OSAVI | ⚠️ 候选 | 同上，在 method 中区分 |
| 冠层覆盖度 | ✅ `CO_321:0000014` | 直接引用 |
| 叶绿素荧光 | ✅ `CO_321:0000028` | 使用 method 区分 SPAD vs 多光谱 |

**通用策略**：当 CO 尚无专用 ID，先用最接近的 CO trait + 自建 method ID 组合，并在 `externalReferences` 中保留原始波段数据。后续可向 Crop Ontology 提交新变量。

---

## 4. MIAPPE 实验级元数据

### 4.1 必填项映射到 brapi-light 模型

| MIAPPE 章节 | brapi-light 对应 | 示例值 |
|-------------|-----------------|--------|
| 通用元数据 | `Trial` / `Study.trialName` | "2026 Wheat Drought Tolerance Trial" |
| 生物源 | `Germplasm` | "TAM 112", "CS" (Chinese Spring) |
| 实验设计 | `Study` 扩展字段 | RCBD, 3 reps, 6 rows × 10 columns |
| 环境 | `Location` / `Season` | CIMMYT Obregon, 2026-Spring |
| 环境变量 | `Observation` + Environment Variable | 土壤水分、降雨、温度时序 |
| 传感器 | 存储在 `images.additionalInfo` | DJI Phantom 4 Multispectral |
| 处理 | 待扩充（当前 Study 无此字段） | 充分灌溉 / 限水灌溉 |

### 4.2 brapi-light 扩展建议

当前 Study 模型缺少 MIAPPE 核心字段。推荐在 Study 表增加：

```sql
ALTER TABLE study ADD COLUMN experimental_design TEXT;
ALTER TABLE study ADD COLUMN treatment_description TEXT;
ALTER TABLE study ADD COLUMN miappe_version TEXT DEFAULT '1.1';
```

在 Study 的 `additionalInfo` JSON 字段中存储 MIAPPE 元数据：

```json
{
  "miappe": {
    "version": "1.1",
    "experimentalDesign": "randomized_complete_block",
    "numberOfReplicates": 3,
    "plotDimensions_m": { "length": 4.0, "width": 1.2 },
    "sowingDate": "2025-11-15",
    "sowingDensity_plantsPerM2": 300,
    "irrigationRegime": "full_irrigation",
    "soilType": "clay_loam"
  }
}
```

---

## 5. 实施路线图（按本仓库当前状态）

### 5.1 近期（基于现有 brapi-light）

```
Step 1: 在 brapi.db 种子数据中写入标准化 Variable
  ├── 使用 CO_321 ID 作为 observationVariableDbId
  ├── 确保 trait/method/scale 三层结构完整（非 null）
  └── 验证: GET /brapi/v2/variables 返回标准格式

Step 2: 在 Field Book App 中导入标准化 Traits
  ├── 验证 Trait 导入不再报 Unknown error
  └── 验证: 在 App 的 Trait 列表中看到 "Plant height (PTHT)"

Step 3: 端到端采集一条记录
  ├── 在 Field Book 中为某个 Plot 录入 Plant height
  ├── Sync → Upload
  └── 验证: curl GET /brapi/v2/observations 返回标准数据

Step 4: 图像支持
  ├── POST /images 写入无人机正射影像元数据
  ├── PUT /images/{id}/imagecontent 上传缩略图
  └── 验证: Curl 确认 image 记录可查询
```

### 5.2 中期（扩展 brapi-light）

```
Step 5: MIAPPE 元数据支持
  ├── Study 模型增加 experimental_design, treatment_description
  └── 支持 MIAPPE 元数据导出

Step 6: 多光谱数据管道
  ├── Python 脚本: GeoTIFF → COG → 分块上传
  ├── Python 脚本: zonal statistics → NDVI per plot → POST observations
  └── 验证: 端到端从无人机影像到 Observation 入库
```

### 5.3 长期（FAIR 合规）

```
Step 7: 数据集发布
  ├── 生成 MIAPPE 兼容的元数据文件
  ├── 关联 CO 术语
  └── 发布到 FAIDARE / Zenodo

Step 8: 跨站互操作
  └── 不同试验站用同一 CO 变量编码，数据可直接合并分析
```

---

## 6. 实操脚本

### 6.1 生成标准化种子数据

```python
# seed_wheat_variables.py — 在你的 brapi-light 中使用
wheat_variables = [
    {
        "variable_db_id": "CO_321:0000020",
        "name": "Plant height",
        "trait_db_id": "CO_321:0000020",
        "trait_name": "Plant height",
        "trait_description": "Height from ground to spike tip, excluding awns",
        "trait_synonyms": '["PTHT", "plant_height"]',
        "method_db_id": "CO_321:0001150",
        "method_name": "Ruler measurement ground to spike",
        "method_description": "Manual meter stick",
        "scale_db_id": "CO_321:0001149",
        "scale_name": "cm",
        "scale_data_type": "numeric",
        "scale_valid_values": '{"min": 0, "max": 250}',
        "scale_decimal_places": 1,
        "crop": "Wheat",
        "language": "en"
    },
    {
        "variable_db_id": "CO_321:0000028__CO_321:0000249",
        "name": "Leaf greenness (SPAD)",
        "trait_db_id": "CO_321:0000028",
        "trait_name": "Chlorophyll content",
        "trait_description": "Relative chlorophyll (SPAD-502)",
        "trait_synonyms": '["CLPHYL", "SPAD"]',
        "method_db_id": "CO_321:0000249",
        "method_name": "SPAD-502 chlorophyll meter",
        "method_description": "Konica Minolta SPAD-502, non-destructive",
        "scale_db_id": "SPAD_scale",
        "scale_name": "SPAD unit",
        "scale_data_type": "numeric",
        "scale_valid_values": '{"min": 0, "max": 60}',
        "scale_decimal_places": 1,
        "crop": "Wheat",
        "language": "en"
    },
    {
        "variable_db_id": "CO_321:0000184",
        "name": "Leaf area index",
        "trait_db_id": "CO_321:0000184",
        "trait_name": "Leaf area index",
        "trait_description": "One-sided green leaf area per unit ground area",
        "trait_synonyms": '["LAI", "leaf_area_index"]',
        "method_db_id": "LAI_2200",
        "method_name": "LAI-2200 plant canopy analyzer",
        "method_description": "LI-COR LAI-2200, above/below canopy readings",
        "scale_db_id": "LAI_scale",
        "scale_name": "m2/m2",
        "scale_data_type": "numeric",
        "scale_valid_values": '{"min": 0, "max": 12}',
        "scale_decimal_places": 2,
        "crop": "Wheat",
        "language": "en"
    },
    {
        "variable_db_id": "CO_321:0000301",
        "name": "Canopy NDVI",
        "trait_db_id": "CO_321:0000301",
        "trait_name": "Canopy NDVI",
        "trait_description": "Normalized Difference Vegetation Index from multispectral imagery",
        "trait_synonyms": '["NDVI", "normalized_difference_vegetation_index"]',
        "method_db_id": "UAV_multispectral",
        "method_name": "UAV multispectral image processing",
        "method_description": "Drone mounted multispectral camera → orthomosaic → NDVI calculation",
        "scale_db_id": "NDVI_scale",
        "scale_name": "NDVI",
        "scale_data_type": "numeric",
        "scale_valid_values": '{"min": -1, "max": 1}',
        "scale_decimal_places": 4,
        "crop": "Wheat",
        "language": "en"
    }
]
```

### 6.2 分区统计：从正射影像到 Observation

```python
# extract_plot_ndvi.py — 伪代码，展示数据管道逻辑
import rasterio
import geopandas as gpd
from rasterstats import zonal_stats

# 1. 加载 plot 边界 (GeoJSON)
plots = gpd.read_file("plots_fieldA.geojson")

# 2. 加载 NDVI raster
with rasterio.open("ndvi_orthomosaic.tif") as src:
    # 3. 对每个 plot 提取统计值
    for _, plot in plots.iterrows():
        stats = zonal_stats(
            plot.geometry, src.read(1),
            affine=src.transform, stats="mean std min max"
        )[0]
        # 4. POST 到 BrAPI
        post_observation(
            plot_id=plot["plot_id"],
            variable_id="CO_321:0000301",
            value=round(stats["mean"], 4),
            timestamp="2026-05-10T10:30:00Z",
            additional_info={
                "ndvi_std": stats["std"],
                "ndvi_min": stats["min"],
                "ndvi_max": stats["max"],
                "source_raster": "ndvi_orthomosaic.tif"
            }
        )
```

---

## 7. 参考资源

| 资源 | 链接 |
|------|------|
| CO_321 小麦性状本体 (AgroPortal) | https://agroportal.eu/ontologies/CO_321 |
| CO_321 GitHub 仓库 | https://github.com/Planteome/CO_321-wheat-traits |
| CO_321 Zenodo 发布 | https://zenodo.org/records/8253720 |
| 小麦性状在 CropOntology 浏览 | https://cropontology.org — 搜索 "CO_321" |
| MIAPPE 官网 | https://www.miappe.org |
| MIAPPE GitHub | https://github.com/MIAPPE/MIAPPE |
| TTADDA-UAV 数据集 (MIAPPE+无人机参考) | https://github.com/NPEC-NL/MIAPPE_TTADDA_dataset |
| BrAPI Phenotyping Concept Dictionary | https://plant-breeding-api.readthedocs.io/en/brapi-v2.1/docs/concept_dictionary/brapi_phenotyping_concept_dictionary.html |
| BrAPI Images 规范 | https://wiki.brapi.org/index.php/Image_Upload |
| BrAPI-FastAPI (Python 参考实现) | https://github.com/agostof/BrAPI-FastAPI |
| FAIDARE 数据门户 | https://urgi.versailles.inrae.fr/faidare |
