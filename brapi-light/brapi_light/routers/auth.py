"""Minimal OIDC endpoints so Field Book can bypass auth."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

AUTH_PAGE = """\
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
  .return {{ display: inline-block; background: #27ae60; color: #fff;
            padding: 10px 28px; border-radius: 8px; text-decoration: none;
            font-size: 15px; }}
</style>
</head>
<body>
<div class="card">
  <h1>brapi-light</h1>
  <p class="version">v0.1.0</p>
  <p class="badge"><span class="status"></span>服务运行中</p>
  <p class="hint">
    BrAPI v2 后端已就绪。<br>
    <span class="arrow">&#x2190;</span> <strong>配置成功，请返回 Field Book App 继续操作</strong>
  </p>
  <a class="return" href="{redirect_uri}#{fragment}">返回 Field Book</a>
  <p class="footer">点击按钮返回 App，或等待自动跳转…</p>
</div>
<script>
  setTimeout(function(){{
    window.location = "{redirect_uri}#{fragment}";
  }}, 1500);
</script>
</body>
</html>"""

NO_REDIRECT_HTML = """\
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
  h1 {{ margin: 0 0 16px; font-size: 28px; color: #2c3e50; }}
  p {{ font-size: 15px; color: #555; }}
</style>
</head>
<body>
<div class="card">
  <h1>brapi-light</h1>
  <p>请通过 POST /token 获取访问令牌。</p>
</div>
</body>
</html>"""


@router.get("/.well-known/openid-configuration")
async def openid_configuration(request: Request):
    base = str(request.base_url).rstrip("/")
    return {
        "issuer": base,
        "authorization_endpoint": f"{base}/auth",
        "token_endpoint": f"{base}/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "jwks_uri": f"{base}/jwks",
        "response_types_supported": ["token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["none"],
    }


@router.post("/token")
async def token():
    return {
        "access_token": "fieldbook-test-token",
        "token_type": "Bearer",
        "expires_in": 360000,
    }


@router.get("/userinfo")
async def userinfo():
    return {"sub": "janedoe", "name": "Jane Doe", "email": "jane@fieldbook.local"}


@router.get("/auth")
async def auth(request: Request):
    redirect_uri = request.query_params.get("redirect_uri", "")
    state = request.query_params.get("state", "")

    if not redirect_uri:
        return HTMLResponse(content=NO_REDIRECT_HTML)

    fragment = f"access_token=fieldbook-test-token&token_type=Bearer&expires_in=360000"
    if state:
        fragment += f"&state={state}"
    return HTMLResponse(content=AUTH_PAGE.format(
        redirect_uri=redirect_uri, fragment=fragment,
    ))


@router.get("/jwks")
async def jwks():
    return {"keys": []}
