from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import Session

from app.db.models import Base


class DownloadHistory(Base):
    """
    下载历史记录
    """
    id = Column(Integer, Sequence('id'), primary_key=True, index=True)
    # 保存路径
    path = Column(String, nullable=False, index=True)
    # 类型 电影/电视剧
    type = Column(String, nullable=False)
    # 标题
    title = Column(String, nullable=False)
    # 年份
    year = Column(String)
    tmdbid = Column(Integer, index=True)
    imdbid = Column(String)
    tvdbid = Column(Integer)
    doubanid = Column(String)
    # Sxx
    seasons = Column(String)
    # Exx
    episodes = Column(String)
    # 海报
    image = Column(String)
    # 下载任务Hash
    download_hash = Column(String, index=True)
    # 种子名称
    torrent_name = Column(String)
    # 种子描述
    torrent_description = Column(String)
    # 种子站点
    torrent_site = Column(String)
    # 附加信息
    note = Column(String)

    @staticmethod
    def get_by_hash(db: Session, download_hash: str):
        return db.query(DownloadHistory).filter(DownloadHistory.download_hash == download_hash).first()

    @staticmethod
    def list_by_page(db: Session, page: int = 1, count: int = 30):
        return db.query(DownloadHistory).offset((page - 1) * count).limit(count).all()
