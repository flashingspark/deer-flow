"""Local, fixed-operation city-statistics tools; no MCP or shell execution."""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

_SCRIPT = Path(__file__).resolve().parent.parent / "skills/custom/china-city-statistics/scripts/city_statistics.py"


async def _run_cli(*args: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if data is not None and len(data) > 2_000_000:
        return {"success": False, "error": "数据超过2MB，请拆分批次"}
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(_SCRIPT),
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(process.communicate(data), timeout=45)
    except BaseException:
        if process.returncode is None:
            process.kill()
        await process.wait()
        raise
    output = stdout if process.returncode == 0 else stderr
    try:
        result = json.loads(output)
    except (ValueError, UnicodeError):
        return {"success": False, "error": "本地统计脚本执行失败", "exit_code": process.returncode}
    if process.returncode != 0:
        return {"success": False, "error": result.get("error", "校验或入库失败")}
    return result


@tool
async def city_statistics_schema() -> dict:
    """获取城市统计JSON字段约束和30项指标字典。原生本地工具，不使用MCP。"""
    return await _run_cli("schema")


@tool
async def save_city_statistics(records: list[dict[str, Any]]) -> dict:
    """将城市统计records数组校验后写入固定SQLite库。来源必须经核实，缺失值为null。返回success和written_count；失败不会部分入库。非MCP。"""
    if not 1 <= len(records) <= 500:
        return {"success": False, "error": "每批必须包含1到500条记录"}
    try:
        return await _run_cli("import", "-", payload={"records": records})
    except (ValueError, OSError, TimeoutError) as exc:
        return {"success": False, "error": str(exc)}


@tool
async def query_city_statistics(city_name: str | None = None, year: int | None = None, limit: int = 100) -> dict:
    """从固定SQLite库按城市和年份读取统计记录，用于核对写入结果。非MCP，不接受SQL或文件路径。"""
    if not 1 <= limit <= 500:
        return {"success": False, "error": "limit必须在1到500之间"}
    args = ["query", "--limit", str(limit)]
    if city_name is not None:
        args.extend(["--city", city_name])
    if year is not None:
        args.extend(["--year", str(year)])
    return await _run_cli(*args)
