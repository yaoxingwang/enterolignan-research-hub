"""Build the offline research portal from local HTML reports and aggregate exports."""

import argparse
from html import escape
from pathlib import Path
import re
from shutil import copyfile


ROOT = Path(__file__).resolve().parent
NAV = {
    "index": "总览", "roadmap": "原始思路", "data": "数据与变量", "results": "分析结果",
    "methods": "清洗流程", "weights": "权重筛选", "literature": "文献与投稿", "next": "下一步",
}
LIBRARY = {
    "original-roadmap.html": ("roadmap", "最初发来的 18 条路线图", "保留最初的研究问题、成本分层和备选方向。"),
    "enterolignan-research-roadmap-18.html": ("roadmap", "扩展版研究路线图", "18 条路线、公开数据核查和饮食菌群论文专题。"),
    "enterolignan-l2-literature-and-publication.html": ("literature", "霍山前作之后，还可以发什么", "方向 1 的近期研究、公开数据与非 MDPI 期刊候选。"),
    "charls-and-chinese-lignan-cvd-review.html": ("literature", "中国人群木脂素与心血管疾病", "CHARLS、CHNS 等数据字段、获取条件与中国证据。"),
    "nhanes-enterolignan-pilot-results-zh.html": ("results", "NHANES 机器学习试跑", "六张图展示腰围、肥胖、HSI 和 CVD 的模型结果。"),
    "dxa-fecal-enl-validation-zh.html": ("results", "成人 DXA 与菌群双向验证", "分周期 DXA 效应及 Kim、Sinha 交叉验证。"),
    "dxa-sensitivity-zh.html": ("results", "成人 DXA 补充分析", "同一样本加入饮食和体力活动，另检查收入贫困比缺失。"),
    "dxa-waist-comparison-zh.html": ("results", "成人 DXA 与腰围同样本比较", "2,078 人的 BMI 调整前后结果与森林图。"),
    "dxa-cycle-validation-zh.html": ("results", "成人 DXA 四周期复核", "早期两期和原两期分开估计，比较躯干、腿部脂肪和腰围。"),
    "dxa-cycle-lifestyle-zh.html": ("results", "成人 DXA 四期生活方式调整", "4,088 人的同样本模型、分期森林图和变量对齐。"),
    "dxa-experiments-zh.html": ("results", "成人 DXA 补充实验", "剂量–反应曲线、性别交互与全身脂肪量调整。"),
    "dxa-robustness-zh.html": ("results", "成人 DXA 稳健性分析", "肾功能同样本调整、周期内加权百分位和调查周期剔除。"),
    "urine-mortality-feasibility-zh.html": ("data", "尿木脂素与 2019 公开死亡随访", "六期有效随访、死因覆盖及 DXA 子样本事件数。"),
    "available-exposure-outcome-screen-zh.html": ("results", "712 个暴露–结局模型", "九个数据模块的关联筛查，另有 54 个分周期模型。"),
    "exposure-outcome-literature-zh.html": ("literature", "现有暴露与结局的文献对照", "按研究周期、暴露、结局和样本对比原始论文。"),
    "med-data-cleaning-zh.html": ("methods", "数据清洗与样本纳入说明", "逐项记录合并键、纳入人数、缺失值和机器学习预处理。"),
    "sas-mortality-code-review-zh.html": ("methods", "尿木脂素与死亡风险的 SAS 代码", "拆解合并、抽样权重、加权 Cox 和公开死因编码。"),
    "next-enterolignan-studies-zh.html": ("next", "前一轮研究路线判断", "成人 DXA、菌群验证和实测 CAP 的开工条件。"),
    "cap-lignan-feasibility-zh.html": ("results", "膳食木脂素与实测 CAP 可行性审计", "NHANES 2017–2018 食物映射覆盖、来源疑点与不建模结论。"),
}


def docs(*names):
    cards = []
    for name in names:
        _, title, description = LIBRARY[name]
        cards.append(f'<article class="doc"><h3>{escape(title)}</h3><p>{escape(description)}</p>'
                     f'<a href="library/{escape(name)}">打开详细报告 <span aria-hidden="true">↗</span></a></article>')
    return '<div class="docs">' + "".join(cards) + "</div>"


def heading(kicker, title, lead):
    return f'<div class="page-head"><p class="eyebrow">{kicker}</p><h1>{title}</h1><p class="lead">{lead}</p></div>'


def layout(key, body):
    menu = "".join(
        f'<a href="{link}.html"' + (' aria-current="page"' if link == key else "") + f'>{label}</a>'
        for link, label in NAV.items()
    )
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="霍山研究的公开数据延伸、数据清洗与分析结果。">
<title>{NAV[key]} · 肠木脂素研究专题</title>
<link rel="stylesheet" href="assets/style.css"><script src="assets/site.js" defer></script></head>
<body><a class="skip" href="#content">跳到正文</a>
<header class="header"><div class="wrap head-inner">
<a class="brand" href="index.html">肠木脂素研究专题</a><nav class="nav" aria-label="专题导航">{menu}</nav>
</div></header>
<main class="wrap" id="content">{body}</main>
<footer><div class="wrap"><span>霍山研究的公开数据延伸 · 更新于 <time datetime="2026-11-12">2026 年 11 月 12 日</time></span><a href="index.html">回专题总览</a></div></footer>
</body></html>'''


HOME = '''
<section class="hero">
  <div class="hero-intro">
    <p class="eyebrow">霍山研究的公开数据延伸</p>
    <h1>肠木脂素与<br>成人脂肪分布</h1>
    <p class="lead">从最初的 18 条思路，到 NHANES 的尿检、DXA 和实测 CAP，再到两套粪便菌群队列的交叉验证。</p>
    <div class="actions"><a class="btn primary" href="results.html#robustness">看最新稳健性分析</a><a class="btn" href="results.html#main-analysis">看主结果</a></div>
  </div>
  <div class="hero-data">
    <p class="eyebrow">当前主结果 · NHANES 成人 DXA</p>
    <div class="hero-number">−0.25</div>
    <p>尿 ENL 每翻倍对应的躯干脂肪占比差，单位为百分点。模型同时纳入 END 并调整 BMI。</p>
    <div class="forest" aria-hidden="true"><span class="line"></span></div><div class="axis" aria-hidden="true"><span>−0.50</span><span>−0.25</span><span>0</span></div>
    <p class="interval">95% CI −0.343 至 −0.156 · 4,228 人 · 四个周期点估计均为负</p>
  </div>
</section>
<section class="section latest-research" aria-labelledby="latest-title">
  <div><h2 id="latest-title">最新分析 · 肾功能与周期稳健性</h2><p>肾功能完整的 3,904 人中，加入 eGFR 和 UACR 后估计为 −0.241 个百分点。周期内排序和三种周期剔除也已完成。</p></div>
  <a href="results.html#robustness">看新结果、森林图与下载 <span aria-hidden="true">↗</span></a>
</section>
<section class="section latest-research" id="diet-cap" aria-labelledby="diet-cap-title"><div><h2 id="diet-cap-title">膳食木脂素与 CAP · 可行性审计完成</h2><p>18/4,564 个食品代码有名称候选，加权克数覆盖首日 1.153%、次日 1.414%。两个回顾日均无完整映射，当前资料不足以建立总摄入模型。</p></div><a href="library/cap-lignan-feasibility-zh.html">查看审计报告与聚合下载 <span aria-hidden="true">↗</span></a></section>
<section class="section" aria-labelledby="overview">
  <h2 id="overview">研究进度</h2>
  <div class="metrics">
    <article class="metric"><strong>18</strong><p>最初的备选课题</p></article>
    <article class="metric"><strong>712</strong><p>已拟合的暴露–结局模型</p></article>
    <article class="metric"><strong>54</strong><p>另做的分周期核查</p></article>
  </div>
</section>
<section class="section" aria-labelledby="chapters">
  <h2 id="chapters">按问题进入</h2>
  <div class="tiles">
    <article class="tile"><h3><a href="roadmap.html">原始思路与方向</a></h3><p>回看初始清单、扩展版路线图和课题取舍。</p></article>
    <article class="tile"><h3><a href="data.html">数据、暴露和结局</a></h3><p>查哪些能同人配对、哪些已分析、哪些仍缺字段。</p></article>
    <article class="tile"><h3><a href="results.html">分析结果与统计</a></h3><p>查看成人 DXA、肥胖模型、CAP 和菌群验证。下载全表。</p></article>
    <article class="tile"><h3><a href="methods.html">清洗和样本纳入</a></h3><p>查看匹配规则、缺失处理和各阶段样本人数。</p></article>
    <article class="tile"><h3><a href="literature.html">文献与投稿</a></h3><p>区分已有研究、同源复核和可扩展的成人 DXA 问题。</p></article>
    <article class="tile"><h3><a href="next.html">下一步研究</a></h3><p>成人 DXA 写作、膳食木脂素映射和菌群外部验证。</p></article>
  </div>
</section>'''

ROADMAP = heading("研究起点", "从 18 条思路到实际分析",
                  "初始清单用于保留当时的选题范围，当前判断以数据实查、模型结果和后续文献为准。") + '''
<div class="split"><section class="panel"><h2>沿着原文的问题推进</h2>
<ol class="steps"><li>从霍山原文的尿 ENL/END、菌群、肥胖和 CAP 出发。</li>
<li>先用公开 NHANES 与已整理的 Kim、Sinha 数据试跑。</li>
<li>由腰围扩展到成人 DXA，再核查跨周期与跨队列结果。</li>
<li>对照近年论文，将腰围作为复核，把成人脂肪分布作为主线。</li></ol></section>
<section class="panel"><h2>当前取舍</h2><p>成人 DXA 有同人尿检与区域体脂。实测 CAP 与尿 ENL 在现有 NHANES 文件里分属不同周期。</p>
<p>中国人群仍单列为后续路线，霍山和 CHARLS 的个体数据没有纳入这批分析。</p>
<a href="next.html">查看最新研究优先级</a></section></div>
<section class="section"><h2>保留的路线图</h2>''' + docs("original-roadmap.html", "enterolignan-research-roadmap-18.html") + "</section>"


DATA_ROWS = [
    ("done", "NHANES 2005–2010", "尿 ENL、END、总量及其他尿植物雌激素", "腰围、BMI、肥胖、血压、病史、肝酶和生化指标", "168 个临床模型。另有 77 个同周期膳食–尿检模型。"),
    ("done", "NHANES 1999–2006", "尿 ENL 与 END", "DXA 躯干脂肪占比、区域脂肪、全身脂肪量、体脂率", "4,570 人尿检与五套 DXA 配对。主回归纳入 4,228 人。"),
    ("done", "NHANES 2017–2018", "首日 24 小时回顾的 11 项营养素", "实测 CAP、肝硬度、体测、病史和血液指标", "231 个模型。纤维–CAP 使用 3,665 人。"),
    ("done", "NHANES 2011–2014", "首日 24 小时回顾的 11 项营养素", "即时记忆、延迟记忆、动物词流畅度、DSST 和综合 Z 分", "55 个模型。"),
    ("done", "Kim / Sinha", "菌属相对丰度；临床模型用粪便 ENL", "粪便 ENL、结直肠病理；Sinha 另有 BMI", "240 / 131 个配对；双向验证用 102 / 66 名对照。"),
    ("partial", "NHANES 食物明细", "膳食木脂素候选映射、DI-GM", "实测 CAP 或认知", "木脂素可行性审计已完成；覆盖不足，未建立总摄入模型。DI-GM 食物组编码仍待整理。"),
    ("pending", "实测尿 ENL/END 与 CAP", "尿肠木脂素", "同一人的实测 CAP", "当前公开文件分属不同周期，缺同人配对。"),
    ("pending", "中国人群与纵向结局", "中国人群木脂素暴露", "新发 CVD 或原文对应结局", "现有分析没有纳入霍山或 CHARLS 个体数据。"),
]
STATUS = {"done": "已分析", "partial": "字段待整理", "pending": "待配对"}


def data_table():
    rows = "".join(
        f'<tr data-status="{status}"><td><span class="tag{" pending" if status != "done" else ""}">{STATUS[status]}</span></td>'
        + "".join(f"<td>{escape(value)}</td>" for value in values) + "</tr>"
        for status, *values in DATA_ROWS
    )
    return '''
<div class="filter" data-filter aria-label="按状态筛选">
<button type="button" data-filter-value="all" aria-pressed="true">全部</button>
<button type="button" data-filter-value="done" aria-pressed="false">已分析</button>
<button type="button" data-filter-value="partial" aria-pressed="false">字段待整理</button>
<button type="button" data-filter-value="pending" aria-pressed="false">待配对</button>
<span class="filter-count" data-filter-count aria-live="polite">显示 8 个数据模块</span></div>
<div class="table-scroll" tabindex="0" role="region" aria-label="暴露与结局列表">
<table><thead><tr><th>状态</th><th>数据</th><th>暴露</th><th>结局</th><th>当前范围</th></tr></thead>
<tbody>''' + rows + "</tbody></table></div>"


DATA = heading("数据盘点", "数据、暴露和结局",
               "按能否在同一个人或同一个粪便样本中配对组织。状态按当前分析进度更新。") + data_table() + '''
<section class="section"><h2>新增公开随访数据</h2>''' + docs("urine-mortality-feasibility-zh.html") + '''</section>
<section class="section"><h2>膳食木脂素与 CAP 可行性</h2>''' + docs("cap-lignan-feasibility-zh.html") + '''</section>
<div class="callout"><p><strong>数据和脚本位置</strong>　4090 的 <code>/data/wyx/med</code>。结果、样本数和效应区间可以从分析页下载。</p></div>
<div class="actions"><a class="btn" href="results.html#downloads">打开结果与下载</a><a class="btn" href="methods.html">查看变量如何清洗</a></div>'''

RESULTS = heading("已完成的分析", "统计结果与模型",
                  "查看成人 DXA 主结果、跨周期复核和其他结局。表格可下载核对。") + '''
<nav class="result-jumps" aria-label="结果页目录">
  <a href="#main-analysis">四期主结果</a><a href="#robustness">最新稳健性分析</a><a href="#dietary-cap">膳食木脂素 CAP 可行性</a><a href="#experiments">补充实验</a>
  <a href="#other-results">其他结局</a><a href="#downloads">下载数据表</a>
</nav>
<div class="split" id="main-analysis"><section class="panel"><h2>成人 DXA 四周期复核</h2>
<p>1999–2006 年合并 4,228 人。尿 ENL 每翻倍，调整 BMI 后躯干脂肪占比平均低 <strong>0.249 个百分点</strong>（95% CI −0.343 至 −0.156）。</p>
<p>早期两期和原两期的估计均为负。单列肌酐和仅保留 DXA 未插补者时结果相近。</p><a href="library/dxa-cycle-validation-zh.html">看跨周期、区域脂肪与腰围比较</a></section>
<figure class="panel"><img src="assets/dxa-cycles.png" alt="成人 DXA 四个调查周期与合并估计。四个周期的点估计均为负。"><figcaption>按调查周期报告估计与 95% CI。</figcaption></figure></div>
<section class="section panel"><h2>四期生活方式敏感性分析</h2><p>在同一批 4,088 人中，同时加入膳食和活动后，躯干脂肪占比差由 −0.259 变为 <strong>−0.239 个百分点</strong>（95% CI −0.330 至 −0.148）。</p><a href="library/dxa-cycle-lifestyle-zh.html">看四期调整结果、森林图和变量映射</a></section>
<section class="section experiment-section" id="robustness" aria-labelledby="robustness-title">
  <header class="experiment-heading">
    <div><p class="eyebrow">最新完成 · NHANES 1999–2006</p><h2 id="robustness-title">肾功能、周期内百分位与周期剔除</h2></div>
    <a class="btn" href="library/dxa-robustness-zh.html">完整报告与方法</a>
  </header>
  <div class="experiment-grid">
    <figure class="panel experiment-chart">
      <h3>同样本肾功能调整与周期剔除</h3>
      <a href="assets/dxa-robustness-forest.png" aria-label="打开肾功能和周期剔除森林图原图"><img src="assets/dxa-robustness-forest.png" loading="lazy" alt="肾功能同样本模型与三种周期剔除中，ENL 每翻倍的躯干脂肪占比估计和 95% CI 均位于零以下。"></a>
      <figcaption>上图使用同一批 3,904 人；下图按剩余调查年数重算权重。效应单位均为 ENL 每翻倍。</figcaption>
    </figure>
    <dl class="experiment-findings">
      <div><dt>肾功能完整样本 · 3,904 人</dt><dd><strong>−0.241 <small>个百分点</small></strong><p>加入 eGFR、平方项和 UACR 后的估计。95% CI −0.331 至 −0.150；同样本调整前为 −0.248。</p></dd></div>
      <div><dt>周期内加权百分位 · 4,088 人</dt><dd><strong>−0.505 <small>个百分点</small></strong><p>周期内每升高 25 个百分位的估计。95% CI −0.716 至 −0.294。此单位与每翻倍不同。</p></dd></div>
      <div><dt>三种周期剔除</dt><dd><strong>−0.262 至 −0.209</strong><p>分别剔除 2003–2004、2005–2006 和 1999–2002 四年块。三种方案的 95% CI 均位于零以下，单位为百分点／ENL 每翻倍。</p></dd></div>
    </dl>
  </div>
  <div class="experiment-grid experiment-followup">
    <figure class="panel experiment-chart">
      <h3>周期内加权百分位复核</h3>
      <a href="assets/dxa-percentile-forest.png" aria-label="打开周期内加权百分位森林图原图"><img src="assets/dxa-percentile-forest.png" loading="lazy" alt="ENL 每升高 25 个百分位的合并估计为负。四个单周期点估计均为负，其中两个周期的 95% CI 跨零。"></a>
      <figcaption>排序使用各期两年尿检权重。四期点估计均为负，1999–2000 和 2003–2004 的区间跨零。</figcaption>
    </figure>
    <aside class="panel experiment-resources" aria-labelledby="robustness-files">
      <h3 id="robustness-files">化验口径与可复核文件</h3>
      <p>血清肌酐按官方字典校准。用原始 ENL/END 单列尿肌酐，再调 eGFR 和尿白蛋白时，估计为 <strong>−0.234</strong>（95% CI −0.325 至 −0.144）。</p>
      <p>4,088 人中有 184 人缺少血清肌酐；尿白蛋白和尿肌酐均可配对。结果继续按横断面关联解释。</p>
      <ul class="link-list">
        <li><a download href="downloads/dxa-robustness-estimates.csv">64 条估计 CSV</a></li>
        <li><a download href="downloads/dxa-renal-audit.csv">化验配对审计 CSV</a></li>
        <li><a download href="downloads/dxa-robustness-forest.pdf">肾功能与周期剔除 PDF</a></li>
        <li><a download href="downloads/dxa-percentile-forest.pdf">百分位森林图 PDF</a></li>
      </ul>
      <a href="next.html#dxa-next">查看已完成事项与后续工作 →</a>
    </aside>
  </div>
</section>
<section class="section panel" id="dietary-cap" aria-labelledby="dietary-cap-title"><h2 id="dietary-cap-title">膳食木脂素与实测 CAP：当前资料不足以建模</h2><p>严格名称候选为 18/4,564 个食物代码。加权食品克数覆盖首日 1.153%、次日 1.414%；两个回顾日均无完整映射。所有候选仍未完成暴露计算所需的审核。</p><p>未匹配食物保持未知。3 个候选记录存在待核对的来源单位疑点；现有尿 ENL/END 与 CAP 周期不同，不能逐人联结。</p><p><a href="library/cap-lignan-feasibility-zh.html">查看方法、限制和来源审计</a></p><ul class="link-list"><li><a download href="downloads/cap-lignan-coverage.csv">两日覆盖率汇总 CSV</a></li><li><a download href="downloads/cap-lignan-feasibility-summary.json">聚合可行性与来源 JSON</a></li></ul></section>
<section class="section experiment-section" id="experiments" aria-labelledby="experiments-title">
  <header class="experiment-heading">
    <div><p class="eyebrow">NHANES 1999–2006 · 4,088 人</p><h2 id="experiments-title">成人 DXA 补充实验</h2></div>
    <a class="btn" href="library/dxa-experiments-zh.html">完整报告与方法</a>
  </header>
  <div class="experiment-grid">
    <figure class="panel experiment-chart">
      <h3>尿 ENL 的剂量–反应曲线</h3>
      <a href="assets/dxa-dose-response.png" aria-label="打开剂量–反应曲线原图"><img src="assets/dxa-dose-response.png" loading="lazy" alt="样条曲线和线性模型都呈负向，样条的逐点 95% 置信区间以阴影显示。"></a>
      <figcaption>以加权中位数 326.2 μg/g 肌酐为参照。阴影为样条逐点 95% CI。</figcaption>
    </figure>
    <dl class="experiment-findings">
      <div><dt>剂量–反应</dt><dd><strong>P=0.092</strong><p>非线性证据有限，主模型继续用 ENL 每翻倍的线性估计。</p></dd></div>
      <div><dt>性别交互</dt><dd><strong>P=0.263</strong><p>男性和女性的躯干脂肪占比估计均为负，交互区间跨零。</p></dd></div>
      <div><dt>调整 BMI 与全身脂肪量</dt><dd><strong>−0.240 <small>个百分点</small></strong><p>尿 ENL 每翻倍的躯干脂肪占比差。95% CI −0.330 至 −0.149。</p></dd></div>
    </dl>
  </div>
  <div class="experiment-grid experiment-followup">
    <figure class="panel experiment-chart">
      <h3>性别与脂肪总量调整对照</h3>
      <a href="assets/dxa-experiments-forest.png" aria-label="打开性别与脂肪总量调整森林图原图"><img src="assets/dxa-experiments-forest.png" loading="lazy" alt="森林图显示男女的估计均为负，三种体型或脂肪总量调整方案的估计接近。"></a>
      <figcaption>上图是性别交互模型中的分组估计。下图使用同一批人比较三种调整方案。</figcaption>
    </figure>
    <aside class="panel experiment-resources" aria-labelledby="experiment-files">
      <h3 id="experiment-files">支持结果与下载</h3>
      <p>同时控制 BMI 和全身脂肪量时，躯干与双腿脂肪量之比低 <strong>1.18%</strong>（95% CI −1.63% 至 −0.73%）。结果按横断面关联解读。</p>
      <ul class="link-list">
        <li><a download href="downloads/dxa-experiment-estimates.csv">补充实验估计 CSV</a></li>
        <li><a download href="downloads/dxa-dose-response.csv">曲线坐标 CSV</a></li>
      </ul>
      <a href="#robustness">看已完成的肾功能与周期稳健性分析 →</a>
    </aside>
  </div>
</section>
<section class="section panel"><h2>2003–2006 年生活方式敏感性分析</h2><p>在同一批 2,050 人中，尿 ENL 每翻倍的估计由 −0.267 变为 <strong>−0.245 个百分点</strong>（95% CI −0.380 至 −0.109）。</p><p><a href="library/dxa-sensitivity-zh.html">查看同样本对照和收入缺失</a> · <a href="assets/dxa-trunk-fat.png">原两期森林图</a></p></section>
<section class="section panel"><h2>用腰围复核成人 DXA</h2><p>同样本加入 BMI 后，腰围点估计由 −1.027 cm 变为 −0.161 cm。再调生活方式后，腰围区间跨零，躯干脂肪占比的估计仍为负。</p><a href="library/dxa-waist-comparison-zh.html">查看 2,078 人的比较与森林图</a></section>
<section class="section" id="other-results"><h2>其余结果</h2>
<div class="table-scroll" tabindex="0" role="region" aria-label="其他模型结果"><table><thead><tr><th>模块</th><th>读数</th><th>解读</th></tr></thead><tbody>
<tr><td>腰围</td><td>ENL 每翻倍，平均低 0.96 cm</td><td>单暴露筛查。三个周期方向一致。</td></tr>
<tr><td>肥胖分类</td><td>2009–2010 验证集 AUC 0.626 → 0.653</td><td>逻辑回归加入 ENL/END 后的增量。基线为人口学特征和吸烟。</td></tr>
<tr><td>纤维与 CAP</td><td>每 5 g/千 kcal 对应 −8.35 dB/m，块内 Q=0.046</td><td>重叠 NHANES 周期已有相同方向的论文。</td></tr>
<tr><td>既往复合 CVD 与认知</td><td>复合 CVD 的 ENL 区间跨 1；认知模型未过块内校正</td><td>按各自的数据和结局口径解读。</td></tr>
<tr><td>粪便菌群与 ENL</td><td>双向 Spearman ρ 为 0.10 和 0.17</td><td>两方向加入菌属的增量区间均跨零。</td></tr>
</tbody></table></div></section>
<section class="section"><h2>完整分析报告</h2>''' + docs("nhanes-enterolignan-pilot-results-zh.html",
    "dxa-fecal-enl-validation-zh.html", "available-exposure-outcome-screen-zh.html") + '''</section>
<section class="section" id="downloads"><h2>下载结果表</h2>
<div class="actions"><a class="btn primary" download href="downloads/nhanes-microbiome-all-models-zh.csv">712 个模型 · 中文 CSV</a>
<a class="btn" download href="downloads/nhanes-urine-cycles-zh.csv">54 个分周期模型 · 中文 CSV</a>
<a class="btn" download href="downloads/dxa-sensitivity-estimates.csv">成人 DXA 敏感性分析 · CSV</a>
<a class="btn" download href="downloads/dxa-waist-estimates.csv">DXA 和腰围模型 · CSV</a>
<a class="btn" download href="downloads/dxa-cycle-estimates.csv">DXA 四周期模型 · CSV</a>
<a class="btn" download href="downloads/dxa-cycle-audit.csv">DXA 四周期样本 · CSV</a>
<a class="btn" download href="downloads/dxa-cycle-contrast.csv">两个时期的估计差 · CSV</a>
<a class="btn" download href="downloads/dxa-cycle-lifestyle-estimates.csv">四期生活方式模型 · CSV</a>
<a class="btn" download href="downloads/dxa-cycle-lifestyle-audit.csv">四期生活方式样本 · CSV</a>
<a class="btn" download href="downloads/dxa-experiment-estimates.csv">补充实验估计 · CSV</a>
<a class="btn" download href="downloads/dxa-dose-response.csv">剂量–反应曲线 · CSV</a>
<a class="btn" download href="downloads/dxa-dose-quantiles.csv">尿 ENL 加权分位数 · CSV</a>
<a class="btn" download href="downloads/urine-mortality-audit.csv">死亡随访核查 · CSV</a>
<a class="btn" download href="downloads/dxa-robustness-estimates.csv">最新稳健性分析 · 64 条估计 CSV</a>
<a class="btn" download href="downloads/dxa-renal-audit.csv">肾功能配对审计 · CSV</a>
<a class="btn" download href="downloads/dxa-percentile-audit.csv">周期内百分位审计 · CSV</a>
<a class="btn" download href="downloads/dxa-deletion-audit.csv">周期剔除权重审计 · CSV</a>
<a class="btn" download href="downloads/dxa-robustness-verification.json">模型复现核查 · JSON</a>
<a class="btn" download href="downloads/dxa-robustness-forest.pdf">肾功能与周期剔除图 · PDF</a>
<a class="btn" download href="downloads/dxa-percentile-forest.pdf">周期内百分位图 · PDF</a></div></section>'''

METHODS = heading("从原表到分析", "清洗流程与样本流失",
                  "按数据来源分别合并和筛选。回归的完整病例规则与机器学习的训练集填补分开记录。") + '''
<div class="split"><section class="panel"><h2>合并与变量构建</h2>
<ol class="steps"><li>NHANES 用调查周期与 <code>SEQN</code> 匹配。粪便队列在队列内按 <code>Sample</code> 匹配。</li>
<li>检查测量状态、年龄、权重与暴露数据。尿代谢物先按肌酐校正，再取 log₂。</li>
<li>按每个回归需要的变量保留完整病例。机器学习的缺失填补只在训练集拟合。</li>
<li>DXA 五套数据分别估计，再按 Rubin 规则合并估计与方差。</li></ol></section>
<section class="panel"><h2>成人 DXA 四期的人数变化</h2>
<p class="tabular"><strong>4,623</strong> 尿检合格 → <strong>4,570</strong> 五套 DXA 配对 → <strong>4,228</strong> 协变量完整</p>
<p>调整 BMI 前后使用同一批人。未插补敏感性分析纳入 3,313 人。2003–2006 年的收入缺失另有同样本分析。</p>
<a href="weights.html">拆开看权重这一步</a></section></div>
<section class="section"><h2>数据清洗与代码复核</h2>''' + docs("med-data-cleaning-zh.html",
    "sas-mortality-code-review-zh.html") + "</section>"

WEIGHTS = heading("NHANES 抽样设计", "选权重、合并周期和限定人群",
                  "先判断变量按哪个调查组件采集，再看合并了多少年。成年人、非孕和完整病例各有独立的纳入条件。") + '''
<div class="split">
<section class="panel"><h2>用两份教程核查一次</h2>
<ol class="steps">
<li><strong>X 轴选组件。</strong> 先看变量的采集方案。完整访谈、MEC、实验室子样本、膳食回顾各有适用权重。</li>
<li><strong>Y 轴合并周期。</strong> 选定同类组件后，按调查时长合并。含 1999–2000 且合并后续周期时，从 1999–2002 年的专用四年权重起算。</li>
<li><strong>Domain 定义研究人群。</strong> 年龄、妊娠和完整病例规则决定谁进入估计。方差计算保留原抽样分层与 PSU 结构。</li></ol>
<p>权重还校正组件无应答和人口校准。教程中的 <code>PROC FREQ</code> 演示加权百分比，报告标准误和区间要用带分层与 PSU 的调查方法。</p>
<p><a href="https://wwwn.cdc.gov/nchs/nhanes/tutorials/weighting.aspx">CDC 权重教程</a> · <a href="https://wwwn.cdc.gov/nchs/nhanes/tutorials/varianceestimation.aspx">CDC 方差与 Domain 教程</a></p></section>
<section class="panel weight-demo"><h2>用两条记录看权重</h2>
<p>示例中两人的腰围是 60 cm 和 100 cm。第一人的权重固定为 100。</p>
<label for="example-weight">调节第二人的权重 <output id="example-weight-value" for="example-weight">300</output></label>
<input id="example-weight" type="range" min="0" max="500" step="25" value="300">
<div class="values"><div>普通均值 <strong>80 cm</strong></div><div>加权均值 <output id="weighted-mean" for="example-weight" aria-live="polite">90.0</output> cm</div></div>
<p>这是演示值。第二人的权重为零时，加权均值只由第一人的记录贡献。</p></section></div>
<section class="section"><h2>我们实际筛掉了多少人</h2>
<p>2005–2010 尿检原表与人口表配对后，先限定 ≥20 岁并排除记录为怀孕的人。这一步之后还有 5,359 人。</p>
<div class="table-scroll" tabindex="0" role="region" aria-label="各周期权重筛选人数"><table><thead><tr><th>周期</th><th>权重字段</th><th>筛选前</th><th>零权重</th><th>正权重</th></tr></thead><tbody>
<tr><td>2005–2006</td><td><code>WTSB2YR</code></td><td>1,428</td><td>23</td><td>1,405</td></tr>
<tr><td>2007–2008</td><td><code>WTSB2YR</code></td><td>1,880</td><td>29</td><td>1,851</td></tr>
<tr><td>2009–2010</td><td><code>WTSA2YR</code></td><td>2,051</td><td>11</td><td>2,040</td></tr>
<tr><td><strong>合计</strong></td><td>尿检子样本权重</td><td><strong>5,359</strong></td><td><strong>63</strong></td><td><strong>5,296</strong></td></tr>
</tbody></table></div>
<p class="note">这一阶段无缺失权重。5,296 人中有 4,991 人的 ENL、END 和肌酐可用，ENL–腰围完整病例最终是 4,419 人。<a href="https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2005/DataFiles/PHYTO_D.htm">2005–2006 尿检字典</a> · <a href="https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2009/DataFiles/PHYTO_F.htm">2009–2010 尿检字典</a></p></section>
<section class="section"><h2>不同分析用的权重</h2>
<div class="table-scroll" tabindex="0" role="region" aria-label="模型权重表"><table><thead><tr><th>分析</th><th>使用的权重</th><th>口径</th></tr></thead><tbody>
<tr><td>2003–2006 成人 DXA × 尿 ENL/END</td><td>两期各用 <code>WTSB2YR × 2/4</code></td><td>尿检组件决定权重。20–69 岁、排除记录为怀孕和完整病例属于研究域。五套 DXA 数据沿用个人权重。</td></tr>
<tr><td>四期成人 DXA × 尿 ENL/END</td><td>1999–2002 年 <code>WTSPH4YR × 4/8</code>，2003–2006 两期各 <code>WTSB2YR × 2/8</code></td><td>早期四年块单独估计时直接使用 <code>WTSPH4YR</code>。</td></tr>
<tr><td>腰围 × 尿 ENL/END</td><td>前两期 <code>WTSB2YR</code>，末期 <code>WTSA2YR</code>，各乘 2/6</td><td>2005–2010 三期。腰围取自 MEC，尿检子样本覆盖共同分析所需变量。</td></tr>
<tr><td>SAS 附件的尿木脂素 × 死亡</td><td>1999–2002 年 <code>WTSPH4YR × 4/12</code>，后四期的尿检权重各乘 2/12</td><td>权重对应基线的 12 个调查年份。死亡随访月数用于 Cox 时间轴。</td></tr>
<tr><td>首日膳食 × CAP 或认知</td><td><code>WTDRD1</code></td><td>首日回顾可靠并且权重为正。使用两天回顾对应 <code>WTDR2D</code>。2003–2004 年 FFQ 另用 <code>WTS_FFQ</code>。</td></tr>
<tr><td>首日膳食 × 尿代谢物，或为 DXA 模型加膳食</td><td>尿检子样本权重</td><td>MEC 首日回顾覆盖更广。检查尿检样本的回顾无应答。膳食是主要暴露时，还要检查回顾星期分布及相应权重调整。</td></tr>
<tr><td>尿 ENL × 空腹血糖或空腹甘油三酯</td><td>核对尿检与空腹子样本的交集</td><td>两个采样组件交叉时，先确认是否有重叠和共同权重。必要时按交集设计重新计算，不能仅按有效样本人数挑权重。</td></tr>
<tr><td>Kim、Sinha</td><td>两队列各自分析</td><td>它们没有使用 NHANES 的抽样权重。</td></tr>
</tbody></table></div>
<p><a href="https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2003/DataFiles/DR1TOT_C.htm">首日与两日回顾字典</a> · <a href="https://wwwn.cdc.gov/nchs/nhanes/Search/variablelist.aspx?Component=Dietary">FFQ 权重字段</a> · <a href="https://wwwn.cdc.gov/nchs/data/nhanes/analyticguidelines/99-10-analytic-guidelines.pdf">1999–2010 年抽样分析指南</a> · <a href="https://www.cdc.gov/nchs/data/series/sr_02/sr02-184-508.pdf">NCHS 的回顾与子样本权重说明</a></p></section>
<section class="section panel"><h2>实际核查 Domain 和完整病例</h2>
<p>成人 DXA 在限制年龄及协变量前保存正权重尿检样本的分层和 PSU。拟合用符合条件的人，计算方差时按原设计汇总各 PSU 的贡献，缺少分析成员的 PSU 贡献记零。2003–2006 年各期的主模型和生活方式模型均覆盖 15 个分层、30 个 PSU。</p>
<p>收入缺失会缩小分析样本。Domain 处理保留设计结构，缺失对代表性的影响通过单独的敏感性分析评估。附件 SAS 在建总库时先删去未满 18 岁和死亡状态缺失者，代码复用时应检查分析域与 PSU 覆盖。</p>
<p><a href="library/dxa-sensitivity-zh.html">成人 DXA 的收入缺失检查</a> · <a href="library/sas-mortality-code-review-zh.html">SAS 代码逐步拆解</a></p></section>'''

LITERATURE = heading("和原始论文对照", "相关文献与投稿判断",
                     "区分相同暴露、相同结局和重叠样本。早期的期刊候选保留在对应报告里。") + '''
<div class="split"><section class="panel"><h2>最接近的工作</h2>
<p>同一 NHANES 周期已有青少年尿 ENL/END 与 DXA 的研究。成人结果的区别在躯干脂肪占比、BMI 条件模型和分周期结果。</p>
<p><a href="https://www.nature.com/articles/s41390-025-04363-9">青少年 DXA 原文</a> · <a href="https://pubmed.ncbi.nlm.nih.gov/38874113/">霍山原文</a></p></section>
<section class="panel"><h2>高度重叠的方向</h2>
<p>尿 ENL 与腰围、纤维与连续 CAP、尿 ENL 与既往卒中都有重叠周期的论文。当前适合用于复核和讨论。</p>
<p><a href="https://doi.org/10.1186/s12876-024-03256-1">纤维与 CAP 原文</a> · <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC13193793/">既往卒中原文</a></p></section></div>
<section class="section"><h2>文献专题</h2>''' + docs("exposure-outcome-literature-zh.html",
    "enterolignan-l2-literature-and-publication.html", "charls-and-chinese-lignan-cvd-review.html") + "</section>"

NEXT = heading("研究计划", "下一步做什么",
               "围绕当前结果最清楚、与霍山原文最接近的分析安排下一轮。") + '''
<section class="panel" id="dxa-next">
  <h2>成人 DXA：三项稳健性分析已完成</h2>
  <p>主结局继续使用躯干脂肪占比。最新结果支持负向横断面关联，并补充了化验口径和周期依赖的检查。</p>
  <ol class="next-experiments">
    <li><h3>已完成：肾功能与尿液稀释</h3><p>3,904 人的同样本估计由 −0.248 变为 −0.241 个百分点。另以原始 ENL/END 单列尿肌酐和尿白蛋白复核。</p><span class="tag">化验校准和配对已核查</span></li>
    <li><h3>已完成：周期内加权百分位</h3><p>每升高 25 个百分位的合并估计为 −0.505 个百分点。四期点估计均为负，其中两个周期的区间跨零。</p><span class="tag">效应单位单独报告</span></li>
    <li><h3>已完成：调查周期剔除</h3><p>三种方案的每翻倍估计为 −0.262 至 −0.209 个百分点。按保留调查年数重算尿检权重，区间均位于零以下。</p><span class="tag">两个后期周期及早期四年块</span></li>
  </ol>
  <p><a href="results.html#robustness">看森林图与下载</a> · <a href="library/dxa-robustness-zh.html">看完整报告与方法</a></p>
</section>
<section class="section panel" id="manuscript-next">
  <h2>后续：围绕成人脂肪分布整理稿件</h2>
  <ol class="steps">
    <li>固定主结局和每翻倍线性模型，汇总样本流程、主表和补充结果。</li>
    <li>把肾功能、周期内百分位、周期剔除与已有补充实验纳入方法和讨论。</li>
    <li>对照已有青少年 DXA 与成人肥胖研究，准确界定成人脂肪分布的增量。</li>
  </ol>
  <p class="note">稿件尚未起草。本轮完成的是三项预定分析；横断面设计、单次尿样和完整病例选择仍限制解释。</p>
</section>
<section class="section panel"><h2>死亡随访已核对事件数</h2><p>1999–2010 年尿检样本有 2,056 例全因死亡，DXA 和腰围共同样本有 217 例。既有论文已使用 2019 版研究尿 ENL 与死亡。</p><a href="library/urine-mortality-feasibility-zh.html">查看分周期和死因覆盖</a></section>
<section class="section split">
<article class="panel"><h2>膳食木脂素与 CAP</h2><p>可行性审计已完成。覆盖不足且来源单位尚有疑点，当前不拟合总膳食木脂素–CAP 模型。后续需先补齐成分来源、单位和食品形态审核。</p><a href="library/cap-lignan-feasibility-zh.html">查看可行性审计与继续实验条件</a></article>
<article class="panel"><h2>菌群评分外部验证</h2><p>当前双向验证结果偏弱。优先寻找可独立配对肠木脂素与菌群的样本，继续核对检测平台和表型定义。</p><a href="library/dxa-fecal-enl-validation-zh.html">查看双向验证</a></article></section>
<section class="section"><h2>研究路线的历史版本</h2>''' + docs("next-enterolignan-studies-zh.html") + "</section>"


def archive(source, target, module):
    html = source.read_text(encoding="utf-8")
    nav = (f'<nav class="med-hub-reader" aria-label="专题归档导航"><a href="../index.html">← 专题总览</a>'
           f'<a href="../{module}.html">返回{NAV[module]}</a><span>既有报告</span></nav>')
    html, head_count = re.subn(r"</head\s*>", '<link rel="stylesheet" href="../assets/reader.css"></head>', html,
                              count=1, flags=re.IGNORECASE)
    html, body_count = re.subn(r"<body\b[^>]*>", lambda m: m[0] + nav, html, count=1, flags=re.IGNORECASE)
    if head_count != 1 or body_count != 1:
        raise ValueError(f"Could not add archive navigation to {source.name}")
    target.write_text(html, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, default=ROOT.parent)
    parser.add_argument("--original", required=True, type=Path)
    parser.add_argument("--dxa-figure", required=True, type=Path)
    args = parser.parse_args()
    pages = dict(index=HOME, roadmap=ROADMAP, data=DATA, results=RESULTS, methods=METHODS,
                 weights=WEIGHTS, literature=LITERATURE, next=NEXT)
    for key, body in pages.items():
        (ROOT / f"{key}.html").write_text(layout(key, body), encoding="utf-8")
    for name, (module, _, _) in LIBRARY.items():
        source = args.original if name == "original-roadmap.html" else args.reports / name
        archive(source, ROOT / "library" / name, module)
    for name in ("nhanes-microbiome-all-models-zh.csv", "nhanes-urine-cycles-zh.csv",
                 "dxa-sensitivity-estimates.csv", "dxa-waist-estimates.csv", "urine-mortality-audit.csv",
                 "dxa-cycle-estimates.csv", "dxa-cycle-audit.csv", "dxa-cycle-contrast.csv",
                 "dxa-cycle-lifestyle-estimates.csv", "dxa-cycle-lifestyle-audit.csv",
                 "dxa-experiment-estimates.csv", "dxa-dose-response.csv", "dxa-dose-quantiles.csv",
                 "dxa-robustness-estimates.csv", "dxa-renal-audit.csv", "dxa-percentile-audit.csv",
                 "dxa-deletion-audit.csv", "dxa-robustness-verification.json",
                 "dxa-robustness-forest.pdf", "dxa-percentile-forest.pdf",
                 "cap-lignan-feasibility-summary.json", "cap-lignan-coverage.csv"):
        copyfile(args.reports / name, ROOT / "downloads" / name)
    copyfile(args.dxa_figure, ROOT / "assets" / "dxa-trunk-fat.png")
    for name in ("dxa-cycles.png", "dxa-dose-response.png", "dxa-experiments-forest.png",
                 "dxa-robustness-forest.png", "dxa-percentile-forest.png"):
        copyfile(args.reports / name, ROOT / "assets" / name)


if __name__ == "__main__":
    main()
