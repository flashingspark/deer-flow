---
name: china-city-statistics
description: 采集、比较、分析中国城市公开统计数据，覆盖人口、经济、财政收入、投资消费、产业企业及公共资源；将带来源的结构化JSON校验后写入SQLite。
---

# 全国主要城市公开统计数据采集分析助手

使用现有 web_search 检索工具采集官方数据，使用 city-statistics MCP 工具保存和查询。

## 最简执行流程

1. 明确城市、年份和指标。用户没有给范围时先询问，不擅自进行全国全量采集。
2. 调用 `city-statistics_get_city_statistics_schema` 获取 JSON Schema 和指标字典。严格使用字典中的 indicator_code、indicator_name、dimension。
3. 检索国家统计局、地方统计局、城市统计公报/年鉴及其他政府官网，读取原文。不得根据模型记忆补数，不得杜撰链接或原文。
4. 输出结构为 `{"records": [...]}`。每个记录必须包含 city_name、year、indicator_code、indicator_name、dimension、value、unit、scope、time_point、value_origin、source_name、source_url、source_quote、status；可带 value_text。城市使用完整名称，例如“北京市”。
5. 调用 `city-statistics_save_city_statistics`，传入 records 数组。工具以强类型 JSON Schema 约束参数，程序再次校验后在一个事务中入库。500条以内一批。
6. 调用 `city-statistics_query_city_statistics` 按城市、年份核对结果。只按工具实际返回的 written_count 报告写入条数；该计数包含更新，不能称为净新增。调用失败时修正数据重试一次，仍失败则如实说明，不声称已入库。
7. 最终简要说明采集范围、写入条数、数据来源、缺失项和口径限制。用户要求分析时再生成分析表格；Markdown表格不能替代入库JSON。

## 字段及统计口径

- 一行=一个城市、年份、指标、来源。数据库保留现有唯一键(city_name, year, indicator_code, source_url)，重复提交更新同一记录。
- scope写清行政区域、人群、价格口径及数据版本，例如“全市；全体居民”或“全市；现价；初步核算”。time_point写“全年”“年末”或“年平均”。相同唯一键但口径、时点、单位或value_origin不同，工具拒绝覆盖，应核实而非绕过。
- value必须是有限数值，百分数如5.2%填5.2，unit填%。保留来源单位；value_text保存原文数值文本。绝对量与增速使用不同指标代码。
- 官方直接值：status=verified、value_origin=official_direct，来源名称、HTTP(S)链接和原文引用均不可空。verified表示采集者核对了原文，程序只校验结构，不自动认证网页真实性。
- 未找到：status=missing、value=null，绝不可用0代替。保留已知来源或留空；在最终回复说明检索范围。
- 计算值：value_origin=calculated，source_quote必须包含公式、输入值及对应来源，source_url指向主要官方来源。解释和推测只放在分析文字，不作为事实数值入库。
- 工具报错或不可用时，保留JSON并报告未入库，不自动生成假的来源补齐。

## 比较规则

只有年份、单位、统计口径、时点和版本可比时才排名；城市是比较对象，不要求城市名称相同。
不可混用全体/城镇居民、年末/年平均人口、初值/修订GDP、现价/不变价、行政区/城区、官方值/媒体估计。
报告区分 verified_fact、calculated_result、inferred_interpretation；推断使用“可能”等措辞，不能声称因果关系。
