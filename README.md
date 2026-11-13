# 肠木脂素研究专题

研究门户汇总 NHANES 尿肠木脂素、成人 DXA 脂肪分布、实测 CAP 可行性审计及相关菌群研究的报告、图表和聚合结果。

- 在线页面：https://yaoxingwang.github.io/enterolignan-research-hub/
- 分析结果：https://yaoxingwang.github.io/enterolignan-research-hub/results.html
- CAP 可行性审计：https://yaoxingwang.github.io/enterolignan-research-hub/library/cap-lignan-feasibility-zh.html

## 本地预览

这是已生成的静态站点，不需要后端或前端编译。可在仓库目录运行：

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

然后访问 http://127.0.0.1:8000/ 。

## 发布

GitHub Pages 使用 `main` 分支的根目录发布。`.nojekyll` 让 Pages 直接提供静态文件。推送页面更新后，等待 Pages 构建完成即可。

`build_portal.py` 保留页面生成逻辑。完整重新生成需要原工作区中的报告源、汇总结果和图片；它不是部署前必须运行的构建步骤。本仓库中的 HTML、资源和下载文件已经生成，可直接部署。

## 目录

- `index.html`、`results.html` 等：专题入口和分栏页面。
- `library/`：完整研究报告。
- `assets/`：图片、样式和页面交互。
- `downloads/`：聚合结果 CSV、JSON 及图表 PDF。

## 结果与数据范围

结果按各报告的研究设计和适用人群解释，横断面关联不代表因果效应。当前资料不足以建立总膳食木脂素–CAP 模型，详见可行性审计。

仓库发布研究报告及聚合结果，不包含个体数据、Phenol-Explorer 成分原表或候选浓度表。数据来源和使用限制见各报告；Phenol-Explorer 数据的商业使用或再分发需遵守其官方条款。本仓库不授予上游数据的额外使用权。
