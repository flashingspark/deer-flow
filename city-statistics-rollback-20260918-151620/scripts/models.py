"""Validated wire format shared by the model, MCP and SQLite writer."""

from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

DIMENSIONS = {
    "population_resident": ("人口与社会结构", "常住人口"),
    "population_registered": ("人口与社会结构", "户籍人口"),
    "population_change": ("人口与社会结构", "人口增量"),
    "urbanization_rate": ("人口与社会结构", "城镇化率"),
    "population_density": ("人口与社会结构", "人口密度"),
    "gdp_total": ("经济发展", "地区生产总值"),
    "gdp_growth": ("经济发展", "GDP增速"),
    "gdp_per_capita": ("经济发展", "人均GDP"),
    "primary_industry_value": ("经济发展", "第一产业增加值"),
    "secondary_industry_value": ("经济发展", "第二产业增加值"),
    "tertiary_industry_value": ("经济发展", "第三产业增加值"),
    "primary_industry_share": ("经济发展", "第一产业占比"),
    "secondary_industry_share": ("经济发展", "第二产业占比"),
    "tertiary_industry_share": ("产业与企业", "第三产业占比"),
    "budget_revenue": ("财政与收入", "一般公共预算收入"),
    "budget_expenditure": ("财政与收入", "一般公共预算支出"),
    "disposable_income": ("财政与收入", "居民人均可支配收入"),
    "fixed_asset_investment_growth": ("投资与消费", "固定资产投资增速"),
    "retail_sales": ("投资与消费", "社会消费品零售总额"),
    "imports_exports": ("投资与消费", "进出口总额"),
    "industrial_value_added": ("产业与企业", "规上工业增加值"),
    "industrial_value_added_growth": ("产业与企业", "规上工业增加值增速"),
    "hightech_value_added": ("产业与企业", "高新技术产业增加值"),
    "hightech_value_added_growth": ("产业与企业", "高新技术产业增加值增速"),
    "enterprise_count": ("产业与企业", "企业数量"),
    "metro_length": ("公共资源与基础设施", "地铁运营里程"),
    "medical_institutions": ("公共资源与基础设施", "医疗机构数"),
    "hospital_beds": ("公共资源与基础设施", "医疗床位数"),
    "universities": ("公共资源与基础设施", "高校数量"),
    "public_transit_vehicles": ("公共资源与基础设施", "公共交通运营车辆数"),
}


class CityStatistic(BaseModel):
    model_config = ConfigDict(
        extra="forbid", str_strip_whitespace=True, allow_inf_nan=False
    )

    city_name: str = Field(min_length=1, description="完整城市名称，例如北京市")
    year: int = Field(strict=True, ge=1900, le=2100)
    indicator_code: str = Field(min_length=1, description="指标字典中的固定代码")
    indicator_name: str = Field(min_length=1)
    dimension: str = Field(min_length=1)
    value: float | None = Field(description="数值；未找到用null，不得用0占位")
    value_text: str | None = Field(default=None, description="官方原始数值及单位文本")
    unit: str = Field(
        min_length=1, description="保留来源单位；百分数填数值而非小数比例"
    )
    scope: str = Field(min_length=1, description="地域、人群、价格、数据版本等统计口径")
    time_point: str = Field(min_length=1, description="全年、年末、年平均等")
    value_origin: Literal["official_direct", "calculated"] = "official_direct"
    source_name: str = ""
    source_url: str = ""
    source_quote: str = ""
    status: Literal["verified", "missing"]

    @model_validator(mode="after")
    def check_evidence(self):
        expected = DIMENSIONS.get(self.indicator_code)
        if expected != (self.dimension, self.indicator_name):
            raise ValueError("指标代码、维度和名称必须匹配指标字典")
        if self.status == "missing":
            if self.value is not None:
                raise ValueError("missing记录的value必须为null")
        else:
            if self.value is None or not all(
                (self.source_name, self.source_url, self.source_quote)
            ):
                raise ValueError("verified记录必须有数值、来源名称、链接及原文依据")
        if self.source_url:
            url = urlsplit(self.source_url)
            if url.scheme not in ("http", "https") or not url.hostname:
                raise ValueError("来源必须是有效的HTTP(S)链接")
            if url.hostname in ("example.com", "example.org", "example.net"):
                raise ValueError("不能使用示例域名作为数据来源")
        return self


class CityStatisticBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    records: list[CityStatistic] = Field(min_length=1, max_length=500)
