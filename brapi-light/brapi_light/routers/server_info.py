"""GET /brapi/v2/serverinfo — service discovery endpoint, and root welcome page."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from brapi_light.config import settings

router = APIRouter()


EXPECTED_CALLS = [
    {
        "service": "serverinfo",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "programs",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "trials",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "studies",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "observationunits",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "observationlevels",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "variables",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "observations",
        "versions": ["2.0", "2.1"],
        "methods": ["GET", "POST", "PUT"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "seasons",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "locations",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "people",
        "versions": ["2.0", "2.1"],
        "methods": ["GET"],
        "dataTypes": ["application/json"],
    },
    {
        "service": "images",
        "versions": ["2.0", "2.1"],
        "methods": ["GET", "POST", "PUT"],
        "dataTypes": ["application/json"],
    },
]


WELCOME_HTML = """\
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>brapi-light</title>
<style>
  body {{ font-family: system-ui, -apple-system, sans-serif; display: flex;
        justify-content: center; align-items: center; min-height: 100vh;
        margin: 0; background: #f5f5f5; color: #333; }}
  .card {{ background: #fff; border-radius: 12px; padding: 48px 40px;
          max-width: 460px; text-align: center; box-shadow: 0 2px 16px rgba(0,0,0,.08); }}
  h1 {{ margin: 0 0 8px; font-size: 28px; color: #2c3e50; }}
  .version {{ font-size: 14px; color: #888; margin-bottom: 24px; }}
  .status {{ display: inline-block; width: 12px; height: 12px; background: #27ae60;
            border-radius: 50%; margin-right: 6px; }}
  .badge {{ display: inline-block; background: #e8f5e9; color: #27ae60;
           padding: 6px 16px; border-radius: 16px; font-size: 14px; margin-bottom: 24px; }}
  .hint {{ font-size: 15px; line-height: 1.6; color: #555; margin-bottom: 28px; }}
  .arrow {{ font-size: 18px; color: #27ae60; }}
  .footer {{ font-size: 12px; color: #aaa; }}
</style>
</head>
<body>
<div class="card">
  <h1>brapi-light</h1>
  <p class="version">{server_name} v{server_version}</p>
  <p class="badge"><span class="status"></span>服务运行中</p>
  <p class="hint">
    BrAPI v2 后端已就绪。<br>
    <span class="arrow">&#x2190;</span> <strong>配置成功，请返回 Field Book App 继续操作</strong>
  </p>
  <p class="footer">brapi-light &mdash; Lightweight BrAPI v2 backend for Field Book</p>
</div>
</body>
</html>"""


@router.get("/")
async def root_welcome(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(content=WELCOME_HTML.format(
            server_name=settings.server_name,
            server_version="0.1.0",
        ))
    return JSONResponse(content={
        "status": "ok",
        "message": "brapi-light is running",
        "version": "0.1.0",
        "serverName": settings.server_name,
    })


@router.get("/brapi/v2/serverinfo")
async def get_server_info():
    return {
        "result": {
            "serverName": settings.server_name,
            "serverDescription": "brapi-light — Lightweight BrAPI v2 backend for Field Book",
            "serverVersion": "0.1.0",
            "organizationName": "Field Book",
            "organizationUrl": "https://github.com/PhenoApps/Field-Book",
            "contactEmail": settings.contact_email,
            "calls": EXPECTED_CALLS,
        }
    }
