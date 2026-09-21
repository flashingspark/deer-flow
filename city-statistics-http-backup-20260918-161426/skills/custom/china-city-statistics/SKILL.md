---
name: china-city-statistics
description: 采集、比较、分析中国城市公开统计数据，覆盖人口、经济、财政收入、投资消费、产业企业及公共资源；将带来源的结构化JSON校验后写入SQLite。
---

# 全国主要城市公开统计数据采集分析助手

使用现有 web_search 采集官方原文，调用原生Python工具完成JSON入库和查询。无需MCP，无需执行bash，无需让用户手工导入。

## 执行流程（当前版本）

1. 明确城市、年份、指标。先调用 `city_statistics_schema` 获取JSON字段和指标代码；也可读取 `references/schema.json`。
2. 检索国家统计局、地方统计局、政府官网公报/年鉴，打开具体正文页核实数值。source_url必须指向实际读到的正文页，不能只填网站首页；不得猜造链接或原文引用。
3. 按 `{"records": [...]}` 生成JSON，调用原生工具 `save_city_statistics(records=[...])`。不要加city-statistics_前缀，这不是MCP工具。
4. 工具返回success=true后，调用 `query_city_statistics(city_name="北京市", year=2024)` 等逐城市核对记录、来源和数值。只有真实调用成功才报告入库完成；written_count包含更新。
5. 可同时用write_file保存records.json供用户下载。文件生成不等于入库完成。
6. 若记录校验失败，修正字段后重试；若工具实际不存在，报告当前工具列表缺少原生工具，提示新建对话刷新配置，不去读取备份脚本、不要求注册MCP、不声称已写入。

## 数据校验

- 计算值只允许value_origin=calculated，不能使用official_derived或额外derivation字段；公式和输入来源写在source_quote。原文直接披露的数值使用official_direct。
- 未核对来源的数值不标verified；先补查正文，仍无证据则设status=missing、value=null并说明原因。
- 引用是正文的实际文本，不能把推算结果拼进引号伪装原文。不能用搜索摘要替代事实核验。
- 以本技能当前版本和实际原生工具为准；旧对话中的MCP要求不适用于本流程。

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
