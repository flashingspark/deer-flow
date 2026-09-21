# 城市公开统计数据 → JSON → SQLite

现有 DeerFlow 自定义技能 `china-city-statistics` 加上现有 `city-statistics` MCP 服务即可完成，不需要新数据库服务或修改核心框架。

Ubuntu 用户：win10；项目：`/home/win10/deer-flow`。

## 使用

打开 DeerFlow 的默认助手，新建对话，选择 `china-city-statistics` 技能（不要选择禁用了技能的 public-research-agent），发送：

> 使用 china-city-statistics，采集北京市、上海市2024年的常住人口、GDP、一般公共预算收入。只用官方来源，输出结构化JSON并写入SQLite，查询确认写入结果，缺失值用null。

MCP 调用顺序：get_city_statistics_schema → save_city_statistics → query_city_statistics。实际工具名前缀为 `city-statistics_`。

## 存储与字段

数据库：`/home/win10/deer-flow/skills/custom/china-city-statistics/data/city_statistics.db`
表：`city_statistics`，每行一个城市年度指标。

| 字段 | 类型 | 含义 |
|---|---|---|
| city_name / year | TEXT / INTEGER | 完整城市名称 / 统计年份 |
| indicator_code / indicator_name / dimension | TEXT | 固定指标代码、名称、六类维度 |
| value / value_text / unit | REAL或NULL / TEXT / TEXT | 数值、原始文本、单位 |
| scope / time_point / value_origin | TEXT | 统计口径、时点、official_direct或calculated |
| source_name / source_url / source_quote | TEXT | 来源名称、链接、原文依据 |
| status | TEXT | verified或missing |
| id / raw_json / created_at | 自动生成 | 主键、结构化原始数据、首次写入时间 |

30个指标覆盖六类需求；字段及指标清单由 `scripts/models.py` 唯一定义，通过MCP向模型提供JSON Schema。source_quote是模型读到的原文，不由程序伪造。结构校验不能代替事实核验。

保持现有唯一键(city_name,year,indicator_code,source_url)：相同键更新，不重复插入；不同统计口径/单位/时点/来源类型拒绝覆盖。不同来源保留多条，不可直接求和或重复计数。全批先校验，在单事务中提交，任意错误均不写入该批。

## 本地检查

```bash
cd /home/win10/deer-flow
backend/.venv/bin/python skills/custom/china-city-statistics/scripts/query_database.py
backend/.venv/bin/python -m unittest discover -s skills/custom/china-city-statistics/scripts -p test_database.py -v
```

测试只使用临时SQLite文件。正式库原有记录保留，不代表已通过新校验；历史示例数据需人工核验，不应当作真实统计数据引用。

修改MCP程序后在新会话使用；若旧会话仍缓存旧进程，可在DeerFlow中重新连接city-statistics服务。部署前文件和数据库备份位于技能目录的backups中。
