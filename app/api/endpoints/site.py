from typing import List, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.background import BackgroundTasks

from app import schemas
from app.chain.cookiecloud import CookieCloudChain
from app.chain.search import SearchChain
from app.chain.site import SiteChain
from app.core.security import verify_token
from app.db import get_db
from app.db.models.site import Site
from app.db.models.siteicon import SiteIcon
from app.db.systemconfig_oper import SystemConfigOper
from app.schemas.types import SystemConfigKey
from app.utils.string import StringUtils

router = APIRouter()


def start_cookiecloud_sync():
    """
    后台启动CookieCloud站点同步
    """
    CookieCloudChain().process(manual=True)


@router.get("/", summary="所有站点", response_model=List[schemas.Site])
def read_sites(db: Session = Depends(get_db),
               _: schemas.TokenPayload = Depends(verify_token)) -> List[dict]:
    """
    获取站点列表
    """
    return Site.list_order_by_pri(db)


@router.put("/", summary="更新站点", response_model=schemas.Response)
def update_site(
        *,
        db: Session = Depends(get_db),
        site_in: schemas.Site,
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    更新站点信息
    """
    site = Site.get(db, site_in.id)
    if not site:
        return schemas.Response(success=False, message="站点不存在")
    site.update(db, site_in.dict())
    return schemas.Response(success=True)


@router.delete("/", summary="删除站点", response_model=schemas.Response)
def delete_site(
        site_in: schemas.Site,
        db: Session = Depends(get_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    删除站点
    """
    Site.delete(db, site_in.id)
    return schemas.Response(success=True)


@router.get("/cookiecloud", summary="CookieCloud同步", response_model=schemas.Response)
def cookie_cloud_sync(background_tasks: BackgroundTasks,
                      _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    运行CookieCloud同步站点信息
    """
    background_tasks.add_task(start_cookiecloud_sync)
    return schemas.Response(success=True, message="CookieCloud同步任务已启动！")


@router.get("/reset", summary="重置站点", response_model=schemas.Response)
def cookie_cloud_sync(db: Session = Depends(get_db),
                      _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    清空所有站点数据并重新同步CookieCloud站点信息
    """
    Site.reset(db)
    SystemConfigOper(db).set(SystemConfigKey.IndexerSites, [])
    CookieCloudChain().process(manual=True)
    return schemas.Response(success=True, message="站点已重置！")


@router.get("/cookie/{site_id}", summary="更新站点Cookie&UA", response_model=schemas.Response)
def update_cookie(
        site_id: int,
        username: str,
        password: str,
        db: Session = Depends(get_db),
        _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    使用用户密码更新站点Cookie
    """
    # 查询站点
    site_info = Site.get(db, site_id)
    if not site_info:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在！",
        )
    # 更新Cookie
    state, message = SiteChain().update_cookie(site_info=site_info,
                                               username=username,
                                               password=password)
    return schemas.Response(success=state, message=message)


@router.get("/test/{site_id}", summary="连接测试", response_model=schemas.Response)
def test_site(site_id: int,
              db: Session = Depends(get_db),
              _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    测试站点是否可用
    """
    site = Site.get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    status, message = SiteChain().test(site.domain)
    return schemas.Response(success=status, message=message)


@router.get("/icon/{site_id}", summary="站点图标", response_model=schemas.Response)
def site_icon(site_id: int,
              db: Session = Depends(get_db),
              _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    获取站点图标：base64或者url
    """
    site = Site.get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    icon = SiteIcon.get_by_domain(db, site.domain)
    if not icon:
        return schemas.Response(success=False, message="站点图标不存在！")
    return schemas.Response(success=True, data={
        "icon": icon.base64 if icon.base64 else icon.url
    })


@router.get("/resource/{site_id}", summary="站点资源", response_model=List[schemas.TorrentInfo])
def site_resource(site_id: int, keyword: str = None,
                  db: Session = Depends(get_db),
                  _: schemas.TokenPayload = Depends(verify_token)) -> Any:
    """
    浏览站点资源
    """
    site = Site.get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    torrents = SearchChain().browse(site.domain, keyword)
    if not torrents:
        return []
    return [torrent.to_dict() for torrent in torrents]


@router.get("/domain/{site_url}", summary="站点详情", response_model=schemas.Site)
def read_site_by_domain(
        site_url: str,
        db: Session = Depends(get_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    通过域名获取站点信息
    """
    domain = StringUtils.get_url_domain(site_url)
    site = Site.get_by_domain(db, domain)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {domain} 不存在",
        )
    return site


@router.get("/{site_id}", summary="站点详情", response_model=schemas.Site)
def read_site(
        site_id: int,
        db: Session = Depends(get_db),
        _: schemas.TokenPayload = Depends(verify_token)
) -> Any:
    """
    通过ID获取站点信息
    """
    site = Site.get(db, site_id)
    if not site:
        raise HTTPException(
            status_code=404,
            detail=f"站点 {site_id} 不存在",
        )
    return site
