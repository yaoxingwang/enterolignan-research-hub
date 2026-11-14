# 肠木脂素研究专题

研究门户汇总 NHANES 尿肠木脂素、成人 DXA 脂肪分布、实测 CAP 可行性审计及相关菌群研究，并收录 CHARLS／SHARE 的营养、心理与功能健康支线。更新于 2026-11-14。

- 在线页面：https://yaoxingwang.github.io/enterolignan-research-hub/
- 分析结果：https://yaoxingwang.github.io/enterolignan-research-hub/results.html
- CAP 可行性审计：https://yaoxingwang.github.io/enterolignan-research-hub/library/cap-lignan-feasibility-zh.html
- 全部研究线状态：https://yaoxingwang.github.io/enterolignan-research-hub/index.html#research-status
- CHARLS／SHARE：https://yaoxingwang.github.io/enterolignan-research-hub/nutrition.html
- 统一下一步：https://yaoxingwang.github.io/enterolignan-research-hub/next.html

## 本地预览

这是已生成的静态站点，不需要后端或前端编译。可在仓库目录运行：

```bash
python3 -m http.server 8000 --bind 127.0.0.1
```

然后访问 http://127.0.0.1:8000/ 。

## 发布

GitHub Pages 使用 `main` 分支的根目录发布。`.nojekyll` 让 Pages 直接提供静态文件。推送页面更新后，等待 Pages 构建完成即可。

`build_portal.py` 保留页面生成逻辑。使用仓库现有附件重建九个页面：

```bash
python3 build_portal.py --pages-only
```

`build_nutrition.py --charls <CHARLS-output-directory> --share <SHARE-outputs-directory>` 从已完成的本地分析中复制经过检查的聚合表和图表，生成四份可移植的公开报告、附件目录、SHA-256 清单及汇总 ZIP。该步骤不读取原始数据或重跑模型。之后运行上述页面生成命令。

完整重导入旧 NHANES 报告还需要原工作区报告源、汇总结果与图片，以及 `--original`、`--dxa-figure`；部署不依赖这一导入步骤。本仓库静态文件可直接部署。

## 目录

- `index.html`、`results.html` 等：专题入口和分栏页面。
- `library/`：完整研究报告。
- `assets/`：图片、样式和页面交互。
- `downloads/`：聚合结果 CSV、JSON 及图表 PDF。

## 结果与数据范围

结果按各报告的研究设计和适用人群解释，横断面关联不代表因果效应。当前资料不足以建立总膳食木脂素–CAP 模型，详见可行性审计。

CHARLS W6 已完成饮食–症状、功能／口腔与家户敏感性分析；SHARE 保留首轮 17 模型和后续官方纵向权重五模型两阶段。W6 饮食–DBS 有效交集 447 人、Kish n≈26.4，当前仅描述。新支线不测 ENL/END 或菌群，不能直接验证肠木脂素机制。全部为探索性、未预注册分析；CHARLS／SHARE 方差为聚类稳健近似，完整分层推断未实施。

`downloads/nutrition-aggregate-results.zip` 只含汇总表、图表与说明。公开副本已清理本机路径、修复相对链接，并标明历史／当前阶段。功能口腔报告中双人家户咀嚼 PR 的两位小数由 1.29 更正为 1.28，原汇总值为 1.284751786654472，CSV 保留原精度。完整原始分析复现仍需依官方条款申请授权数据。

仓库发布研究报告及聚合结果，不包含个体数据、Phenol-Explorer 成分原表或候选浓度表。数据来源和使用限制见各报告；Phenol-Explorer 数据的商业使用或再分发需遵守其官方条款。本仓库不授予上游数据的额外使用权。
