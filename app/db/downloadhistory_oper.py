from pathlib import Path
from typing import Any

from app.db import DbOper
from app.db.models.downloadhistory import DownloadHistory


class DownloadHistoryOper(DbOper):
    """
    下载历史管理
    """

    def get_by_path(self, path: Path) -> Any:
        """
        按路径查询下载记录
        :param path: 数据key
        """
        return DownloadHistory.get_by_path(self._db, path)

    def get_by_hash(self, download_hash: str) -> Any:
        """
        按Hash查询下载记录
        :param download_hash: 数据key
        """
        return DownloadHistory.get_by_hash(self._db, download_hash)

    def add(self, **kwargs):
        """
        新增下载历史
        """
        downloadhistory = DownloadHistory(**kwargs)
        return downloadhistory.create(self._db)

    def list_by_page(self, page: int = 1, count: int = 30):
        """
        分页查询下载历史
        """
        return DownloadHistory.list_by_page(self._db, page, count)

    def truncate(self):
        """
        清空转移记录
        """
        DownloadHistory.truncate(self._db)
