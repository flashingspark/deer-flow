from mcp.server.fastmcp import FastMCP

from database import query_city_statistics as query_db
from database import save_city_statistics as save_db
from models import CityStatistic, CityStatisticBatch, DIMENSIONS

mcp = FastMCP("city-statistics")


@mcp.tool()
def get_city_statistics_schema() -> dict:
    """读取城市统计JSON字段约束和六类指标字典；采集入库前调用。"""
    return {
        "schema": CityStatisticBatch.model_json_schema(),
        "indicators": [
            {"indicator_code": code, "dimension": dim, "indicator_name": name}
            for code, (dim, name) in DIMENSIONS.items()
        ],
    }


@mcp.tool()
def save_city_statistics(records: list[CityStatistic]) -> dict:
    """将有来源依据的结构化城市统计数据原子写入SQLite；相同键更新，不重复增加。"""
    return save_db([record.model_dump() for record in records])


@mcp.tool()
def query_city_statistics(
    city_name: str | None = None, year: int | None = None, limit: int = 100
) -> dict:
    """按城市和年份查询已保存的数据，核对入库结果。"""
    return query_db(city_name, year, limit)


if __name__ == "__main__":
    mcp.run(transport="stdio")
