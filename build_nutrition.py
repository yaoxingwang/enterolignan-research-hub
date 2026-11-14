"""Publish aggregate nutrition research artifacts and build the extension page."""

import argparse
import csv
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from shutil import copyfile
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
DOWNLOADS = ROOT / "downloads"
ASSETS = ROOT / "assets"
REPORTS = {
    "charls": ("charls-nutrition-report.html", "CHARLS W6：饮食与抑郁症状", "已完成主分析与代理、权重、协变量、县聚类和题项缺失复核。"),
    "charls-directions": ("charls-function-oral-report.html", "CHARLS W6：功能、口腔与饮食", "已完成任务能力、咀嚼、口腔状态、标准化比例与家户内复核。"),
    "share": ("share-first-report.html", "SHARE 首轮：17 个探索模型", "历史分析阶段；当时尚缺三个补充包。当前纵向结论请看补充报告。"),
    "share-supplement": ("share-supplement-report.html", "SHARE 补充：官方权重与 W6 DBS", "当前更新：五个纵向比较模型、同期 DBS 可行性与 All-waves 参与状态审计。"),
}

OVERVIEW = '''
<section class="section experiment-section" id="research-status" aria-labelledby="status-title">
  <header class="experiment-heading"><div><p class="eyebrow">全部研究线 · 截至 2026-11-14</p><h2 id="status-title">现在有哪些证据</h2></div><a class="btn" href="nutrition.html">进入营养健康支线</a></header>
  <p class="lead">NHANES 尿 ENL/END 与成人脂肪分布仍是主线；CHARLS、SHARE 扩展到饮食、心理和功能健康。各数据集分别解释，不合并不同暴露的效应。</p>
  <div class="table-scroll" tabindex="0" role="region" aria-label="全部研究线当前状态"><table class="status-table"><thead><tr><th>研究线／状态</th><th>实际测量</th><th>当前结果</th><th>解释边界与入口</th></tr></thead><tbody>
  <tr><td>霍山前作<br><span class="tag">研究起点</span></td><td>305 名社区成人；尿肠木脂素、粪便菌群、体型，随访体成分与 CAP</td><td>为公开数据延伸提供问题和机制线索</td><td>本专题未重跑霍山个体数据。<a href="https://pubmed.ncbi.nlm.nih.gov/38874113/">查看原文</a></td></tr>
  <tr><td>NHANES 成人 DXA<br><span class="tag">主分析与稳健性完成</span></td><td>1999–2006 年同人尿 ENL/END 与区域脂肪；主模型 4,228 人</td><td>ENL 每翻倍，躯干脂肪占比差 −0.249 个百分点；肾功能调整后 −0.241</td><td>横断面、单次尿样；尚不能解释为因果。<a href="results.html#main-analysis">主结果与图表</a></td></tr>
  <tr><td>Kim／Sinha 菌群<br><span class="tag">双向验证完成</span></td><td>粪便 ENL 与菌属丰度；验证使用 102／66 名对照</td><td>双向 Spearman ρ 为 0.10／0.17；增量区间跨零</td><td>外部验证较弱，需独立配对队列。<a href="library/dxa-fecal-enl-validation-zh.html">详细报告</a></td></tr>
  <tr><td>膳食木脂素–CAP<br><span class="tag pending">审计完成 · 暂不建模</span></td><td>2017–2018 年食物回顾与实测 CAP；成分映射尚不完整</td><td>18/4,564 个名称候选；克数覆盖 1.153%／1.414%</td><td>未知食物不能记零；尿 ENL 与 CAP 不同周期。<a href="results.html#dietary-cap">可行性结论</a></td></tr>
  <tr><td>CHARLS W6<br><span class="tag">横断面 pilot 完成</span></td><td>每日≥2 种蔬果、CES-D-10；功能、咀嚼、失牙与假牙</td><td>症状主 PR 0.766；全食物调整后 0.852。咀嚼与未达蔬果题标准有关，任务关联在功能调整后减弱</td><td>主症状模型 11,932 人；口腔模型 12,913 人。无 ENL/END。<a href="nutrition.html#charls">查看当前成果</a></td></tr>
  <tr><td>SHARE W8→W9<br><span class="tag">首轮＋官方权重更新完成</span></td><td>每日蔬果频率与 EURO-D；官方纵向权重 25,327 人</td><td>基本模型 0.890（0.751–1.053），n=25,327；扩展模型 0.955（0.824–1.108），n=25,302</td><td>后期筛查阳性比，加权区间包含 1；无起病日期。同样本调整比较见<a href="nutrition.html#share">横断面与纵向结果</a>。</td></tr>
  <tr><td>SHARE W6 DBS<br><span class="tag pending">可行性完成 · 仅描述</span></td><td>2015 年干血斑；同期有效饮食交集仅 447 人</td><td>Kish n≈26.4；结构性问卷路由和权重集中，不拟合正式关联模型</td><td>无 ENL/END 或菌群；后期化验不是再次采样。<a href="nutrition.html#dbs">审计与描述</a></td></tr>
  </tbody></table></div>
  <p class="note">PR 为现患比；随访模型比较基线 EURO-D&lt;4 者的后期筛查状态。CHARLS／SHARE 区间为聚类稳健近似，尚未重建完整分层抽样方差。所有新增分析均为未预注册的探索。</p>
</section>'''

SUMMARY = '''<section class="section panel" id="nutrition-update"><p class="eyebrow">新增 · CHARLS 与 SHARE</p><h2>营养、心理与功能健康支线</h2><p>CHARLS 已完成饮食–抑郁症状及功能／口腔分析。SHARE 已完成首轮 17 个模型、官方 W8→W9 纵向权重的五个比较模型，以及 W6 饮食–DBS 可行性审计。</p><p>CHARLS 的症状关联经逐步调整减弱；SHARE 的扩展纵向估计接近 1。两者测量不同的饮食条目，均不能替代 ENL/END 或菌群机制验证。</p><a class="btn primary" href="nutrition.html">看结果、图表、报告与聚合下载</a></section>'''


def read_rows(prefix, name):
    with (DOWNLOADS / f"{prefix}-{name}").open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def model_table(prefix, name, specs, caption):
    records = {r["model"]: r for r in read_rows(prefix, name)}
    body = []
    for key, label in specs:
        row = records[key]
        estimate = f'{float(row["estimate"]):.3f}（{float(row["ci_low"]):.3f}–{float(row["ci_high"]):.3f}）'
        body.append(f'<tr><td>{escape(label)}</td><td class="tabular">{int(row["n"]):,}</td><td class="tabular">{estimate}</td></tr>')
    return (f'<div class="table-scroll" tabindex="0" role="region" aria-label="{escape(caption)}"><table>'
            '<thead><tr><th>模型</th><th>人数</th><th>比值（聚类稳健近似 95% CI）</th></tr></thead><tbody>'
            + ''.join(body) + '</tbody></table></div>')


def report_cards():
    return '<div class="docs">' + ''.join(
        f'<article class="doc"><h3>{title}</h3><p>{description}</p><a href="library/{name}">打开完整报告 ↗</a></article>'
        for name, title, description in REPORTS.values()) + '</div>'


def nutrition_page():
    charls = model_table('charls', 'confounder_sensitivity.csv', [
        ('demographic', '人口学调整，主模型'),
        ('plus_alcohol_walking_chewing', '再调饮酒、步行、咀嚼'),
        ('plus_five_cardiometabolic_diagnoses', '再调吸烟与五项心代谢病史'),
        ('plus_other_three_food_items', '再调其他三类食物'),
        ('asset_sample_plus_assets', '家庭资源敏感性：再调耐用品类别数'),
    ], 'CHARLS 饮食与症状逐步调整')
    share = model_table('share-first', 'model_results.csv', [
        ('w9_primary', 'W9 人口学基础模型'),
        ('w9_extended', 'W9 扩展生活方式与慢病'),
        ('w9_all_foods', 'W9 再调其他食物'),
        ('w9_finance_adjusted', 'W9 再调家庭经济困难'),
    ], 'SHARE W9 横断面调整序列')
    long = model_table('share-supplement', 'longitudinal_model_results.csv', [
        ('long_official_primary', '官方纵向权重，基本调整'),
        ('long_baseline_weight_same_sample', '相同样本，基线权重'),
        ('long_unweighted_same_sample', '相同样本，不加权'),
        ('long_official_base_same_extended', '扩展共同样本，基本调整'),
        ('long_official_extended', '相同扩展样本，扩展调整'),
    ], 'SHARE 官方纵向权重同样本比较')
    return '''
<div class="page-head"><p class="eyebrow">独立支线 · CHARLS／SHARE</p><h1>营养、心理与功能健康</h1><p class="lead">把已完成的问卷研究、纵向权重更新和 DBS 可行性放在一起查看。这里没有实测肠木脂素或菌群，结论沿各自的测量与设计展开。</p></div>
<nav class="result-jumps" aria-label="支线页目录"><a href="#charls">CHARLS 症状</a><a href="#function">功能与口腔</a><a href="#share">SHARE 症状与随访</a><a href="#dbs">W6 DBS 可行性</a><a href="#reports">全部报告与下载</a><a href="#next-nutrition">后续条件</a></nav>
<div class="callout"><p><strong>当前判断：</strong>CHARLS 的横断面关联经调整后保留，但尚无时间顺序；SHARE 的官方加权随访区间包含 1，扩展调整后更接近 1。现有结果支持继续研究饮食与健康脆弱性，不能确认为保护作用或肠木脂素机制。</p></div>
<section class="section experiment-section" id="charls"><header class="experiment-heading"><div><p class="eyebrow">CHARLS W6 · 中国中老年人</p><h2>饮食与抑郁症状：调整后关联减弱</h2></div><a class="btn" href="library/charls-nutrition-report.html">完整报告</a></header>
<div class="split"><article class="panel"><h3>主样本与测量</h3><p><strong>11,932 人／3,991 例筛查阳性／447 个社区。</strong>55–110 岁，按官方应答年度连接。2021、2022、2023 是同一轮的访问年份。</p><p>暴露为每日是否吃≥2 <strong>种</strong>蔬菜或水果；结局为 CES-D-10≥10。它是症状筛查，不是临床抑郁症诊断。</p><p>主 PR 0.766（0.697–0.841）；加权粗症状比例为回答“是”者 29.01%、回答“否”者 42.53%。</p></article><figure class="panel"><a href="assets/charls-confounder_forest.png"><img loading="lazy" src="assets/charls-confounder_forest.png" alt="CHARLS 同样本逐步调整后，蔬果条目的现患比由约 0.766 向 1 移动至 0.852。"></a><figcaption>固定 11,932 人逐步调整；家庭资源模型另限 11,924 人。</figcaption></figure></div>
''' + charls + '''
<p class="note">家庭资源共同样本 11,924 人：加入耐用品前后 PR 为 0.853／0.859。其他食物相互调整改变比较对象，不能直接归因为某一种混杂。</p>
<details class="panel evidence-details"><summary>已完成的稳健性与缺失复核</summary><p>CES-D≥12、连续总分、代理规则、同样本事后分层权重、县级聚类和食物条目 BH 校正均已完成。社区与县聚类主区间分别为 0.697–0.841、0.695–0.843。</p><p>12,840 名基本变量完整者中，908 人未完整回答十题；551 人可由已答分数界定结局，357 人仍不确定。完成概率加权估计约 0.769–0.770，399 次社区 bootstrap 区间约 0.695–0.841；九个未判定结局情景估计为 0.761–0.809。这些检查不能证明缺失可忽略。</p><p><a download href="downloads/charls-missingness_ipw_models.csv">完成概率加权结果</a> · <a download href="downloads/charls-cesd_mnar_scenarios.csv">未判定结局情景</a> · <a download href="downloads/charls-proxy_weight_sensitivity.csv">代理与权重复核</a></p></details></section>
<section class="section experiment-section" id="function"><header class="experiment-heading"><div><p class="eyebrow">CHARLS W6 · 另一条横断面问题</p><h2>谁更难达到蔬果题标准</h2></div><a class="btn" href="library/charls-function-oral-report.html">功能、口腔与家户报告</a></header>
<p>此处结局改为 DA128 回答“否”。功能共同样本 12,925 人；口腔与慢病完整样本 12,913 人、1,998 事件、150 个匿名县。与上面的 CES-D 完整题项样本不同。</p>
<div class="tiles"><article class="tile"><span class="tag">任务关联明显减弱</span><h3>购物或做饭困难</h3><p>固定 12,925 人，人口学调整 PR 1.368（1.213–1.542）；加一般功能后 1.039（0.837–1.290）。购物题反映健康／记忆相关任务能力，不测社区食品供给。</p></article><article class="tile"><span class="tag">个体模型关联保留</span><h3>不能吃苹果等硬食</h3><p>同样本 PR 由 1.407 变为 1.378。进一步纳入口腔状态、家庭资源及慢病，12,913 人中 PR 1.343（1.191–1.514）。</p></article><article class="tile"><span class="tag pending">家户内仍不精确</span><h3>家庭条件与反向因果</h3><p>9,004 名双人家户成员加权 PR 1.285（1.101–1.500）；790 对结局不同的家户内条件 OR 1.244（0.935–1.655）。PR 与未加权条件 OR 不直接比较。</p></article></div>
<div class="section split"><figure class="panel"><a href="assets/charls-food_function_standardized.png"><img loading="lazy" src="assets/charls-food_function_standardized.png" alt="四组从粗比例到一般功能调整后的标准化比较，任务困难的差异减弱。"></a><figcaption>同时咀嚼与任务困难者和均无困难者：粗差 16.99 个百分点；功能调整后差 5.05（0.29–9.80）个百分点。</figcaption></figure><article class="panel"><h3>口腔模型的绝对差</h3><p>标准化后，能吃硬食者未达蔬果题标准的比例为 <strong>13.21%</strong>，不能者 <strong>17.81%</strong>，差 <strong>4.60（2.61–6.59）个百分点</strong>。</p><p>全口失牙、假牙和硬食能力分别建模；127 个失牙题空白来自既往失牙跳题，其中 79 人仍能吃硬食，不能将空白记为无失牙或不能咀嚼。</p><p>四种食物回答在同样本分别建模；奶制品接近无关联，蔬果、蛋／豆、肉／鱼／家禽结果见报告与全表。绝对差未支持明确年龄交互，也不能将访问年份差异解释为趋势。</p><a download href="downloads/charls-oral_diet_standardized.csv">下载标准化比例与分组表</a></article></div>
<p class="note">同一家户编号不能确认共餐或两人互为配偶。帮助题在无困难者中属于结构性跳题；同期帮助状态不能估计照护收益。全部为未预注册 pilot，尚未形成正式稿件。</p></section>
<section class="section experiment-section" id="share"><header class="experiment-heading"><div><p class="eyebrow">SHARE · 欧洲多国</p><h2>从横断面关联到官方加权随访</h2></div><a class="btn" href="library/share-supplement-report.html">当前补充报告</a></header>
<div class="callout"><p><strong>测量不同：</strong>SHARE 的暴露是“每日吃蔬菜或水果”的频率，CHARLS 是“每日≥2 种”。SHARE 结局 EURO-D≥4 与 CES-D-10 也不是相同量表，不合并这两套效应。</p></div>
<h3>首轮 W9 横断面：61,463 人、28 国</h3>''' + share + '''
<p class="note">上表各行样本量不同。固定扩展共同样本的基本模型 PR 为 0.894；扩展后为 0.929。家庭经济困难完整样本 60,509 人的最终估计接近 1。17 个首轮模型作为独立阶段保留。</p>
<h3>W8→W9：官方纵向权重的五个比较</h3><p>基线 EURO-D&lt;4 者有 26,394 名有效重访者；官方个体纵向正权重覆盖其中 <strong>25,327 人、26 国、4,215 例后期阳性</strong>，中位间隔 2.08 年。未获官方权重的 1,067 人均来自荷兰，缺失原因尚未确认。</p>
''' + long + '''
<p class="note">前三行固定 25,327 人，后两行固定 25,302 人／4,212 事件。基本随访模型已调整基线连续 EURO-D 与间隔；扩展模型再加生活方式及慢病。不加权结果不能替代加权结论。</p>
<div class="section split"><figure class="panel"><a href="assets/share-supplement-longitudinal_weights_forest.png"><img loading="lazy" src="assets/share-supplement-longitudinal_weights_forest.png" alt="SHARE 官方纵向权重、基线权重与不加权结果比较；官方加权基本与扩展模型的区间均包含 1。"></a><figcaption>所有区间为聚类稳健近似；纵向权重不自动校正额外的饮食／量表完整病例选择。</figcaption></figure><article class="panel"><h3>随访审计完成，不把未访当死亡</h3><p>34,733 名基线阴性者中，26,947 人有 W9 主访谈，26,394 人满足分析条件，553 人的分析随访不完整。</p><p>其余 7,786 人没有 W9 主访谈：状态 Alive 1,511、Dead 1,114、Unknown 4,625、设计缺失 −99 为 536。保留这些分类，不将失访统一解释为死亡。</p><p>这里比较后期筛查状态：没有观察起病日期、期间缓解或所有幸存者结局，不能报告临床新发抑郁症或人口发病率。</p><a download href="downloads/share-supplement-allwaves_attrition_states.csv">下载参与／死亡状态审计</a></article></div></section>
<section class="section experiment-section" id="dbs"><header class="experiment-heading"><div><p class="eyebrow">SHARE W6 · 2015 年样本</p><h2>DBS：交集可连上，设计仍不足以建模</h2></div><a class="btn" href="library/share-supplement-report.html">查看路由与指标描述</a></header>
<div class="split"><article class="panel"><p><strong>24,218</strong> 名 DBS 参与者全部一对一连接到 W6 主访谈；有效同期蔬果回答 554 人 → 年龄合格 464 → BR 本人作答 448 → 正权重 <strong>447 人</strong>。</p><p>纵向版问卷 55,402 人中该蔬果题有效回答为 0，表明大量空白来自结构性路由。447 人的 <strong>Kish n=26.4</strong>；最大权重占 15.00%，前十占 46.62%。选择与权重集中共同限制分析。</p><p>当前只提供选中样本描述，<strong>未拟合正式饮食–DBS 多变量模型</strong>。不通过删权重或协变量寻找有利结果。</p></article><figure class="panel"><a href="assets/share-supplement-w6_overlap.png"><img loading="lazy" src="assets/share-supplement-w6_overlap.png" alt="W6 干血斑与有效饮食交集从 24,218 人递减至 447 人。"></a><figcaption>同期有数据不等于具有足够的共同测量与代表性。</figcaption></figure></div>
<p>CRP 可描述 415 人、HbA1c 350、HDL 272、总胆固醇 419、甘油三酯 418；指标交集各异。CRP final 封顶 10 mg/L、甘油三酯 final 封顶 500 mg/dL，已单列未封顶描述。</p><p class="note">完整 DBS 有 21 项指标；后 14 项的文献单位与实际发布尺度尚未全部核清。DBS 是非空腹毛细血样，不等同空腹静脉血。2015 年采样与后期检测年份需区分；无 ENL/END 或菌群。DBS 权重不能与 W8／W9 权重相乘。</p></section>
<section class="section" id="reports"><h2>全部报告与聚合下载</h2>''' + report_cards() + '''
<div class="actions"><a class="btn primary" download href="downloads/nutrition-aggregate-results.zip">下载全部支线聚合表与图表</a><a class="btn" href="downloads/nutrition-downloads.html">逐项查看文件目录</a><a class="btn" download href="downloads/nutrition-publication-manifest.json">公开附件校验清单</a><a class="btn" href="downloads/nutrition-README.md">文件与复现说明</a></div><p class="note">公开附件为研究报告、统计汇总和图表；不包含原始授权 ZIP、个人记录、ID 或链接表。报告中的历史输入状态保留并标注；当前 SHARE 为十个已归档数据包。</p></section>
<section class="section panel" id="next-nutrition"><h2>接下来需要满足哪些条件</h2><ol class="steps"><li><strong>CHARLS：先固定研究问题，再接早期轮次。</strong>W4 早期咀嚼→W6 饮食状态尚属设计；需获取并统一问卷、跳题、时间、失访与权重。缺同口径基线饮食时，不能研究“饮食变化”。W5 可补既往功能与症状。</li><li><strong>SHARE：先处理推断与选择问题。</strong>完整分层抽样方差、额外完整病例选择及荷兰纵向权重覆盖仍待解决。当前已有五模型更新，不需要重复首轮筛查。</li><li><strong>DBS：先确认共同测量与发布尺度。</strong>现有结构性交集不足以支持原定正式模型；保持描述结论。若寻找替代设计，需另定问题和样本，不将其包装成机制验证。</li><li><strong>原肠木脂素主线：继续成人 DXA 写作准备。</strong>独立生物标志物／菌群配对样本仍是机制外部验证的关键条件。</li></ol><p><a href="index.html#research-status">回看全部研究线</a> · <a href="next.html">查看统一下一步</a></p></section>'''


def sanitize_report(source, target, prefix, link_map, notice):
    text = source.read_text(encoding="utf-8")
    # Both rendered image metadata and embedded source Markdown carry local paths.
    text = text.replace(str(source.parent) + '/', f'../assets/{prefix}-')
    for old, new in link_map.items():
        text = text.replace(f'href="{old}"', f'href="{new}"')
        text = text.replace(f']({old})', f']({new})')
    if prefix == 'charls':
        text = text.replace('research_directions.html', 'charls-function-oral-report.html')
    if source.name == 'research_directions.html':
        text = text.replace('1.29（1.10–1.50）', '1.28（1.10–1.50）')
    nav = ('<nav class="med-hub-reader" aria-label="专题归档导航"><a href="../index.html">← 专题总览</a>'
           '<a href="../nutrition.html">返回营养健康支线</a><span>探索性研究报告</span></nav>'
           f'<aside style="margin:20px auto;padding:16px;max-width:1100px;background:#e6f1ec;color:#162d2b;border-left:4px solid #07594d">{notice}</aside>')
    text, heads = re.subn(r'</head\s*>', '<link rel="stylesheet" href="../assets/reader.css"></head>', text, count=1, flags=re.I)
    text, bodies = re.subn(r'<body\b[^>]*>', lambda m: m[0] + nav, text, count=1, flags=re.I)
    if heads != 1 or bodies != 1 or '/Users/' in text:
        raise ValueError(f'Publication sanitation failed: {source.name}')
    target.write_text(text, encoding='utf-8')


def publish(charls, share):
    specs = [
        ('charls', charls, ['analysis_summary.json', 'food_function_feasibility.json', 'food_function_household_audit.json', 'oral_diet_audit.json', 'oral_household_audit.json']),
        ('share-first', share / 'share', ['analysis_summary.json']),
        ('share-supplement', share / 'share_w6_dbs', ['analysis_summary.json', 'participation_code_labels.json']),
    ]
    published = []
    for prefix, source, json_names in specs:
        for path in sorted(list(source.glob('*.csv')) + [source / name for name in json_names] + list(source.glob('*.pdf'))):
            if path.suffix == '.csv':
                with path.open(encoding='utf-8-sig', newline='') as handle:
                    header = next(csv.reader(handle))
                if any(h.lower() in {'id', 'mergeid', 'householdid', 'communityid', 'hhid'} for h in header):
                    raise ValueError(f'Identifier column in {path.name}')
            if path.suffix in {'.csv', '.json'} and '/Users/' in path.read_text():
                raise ValueError(f'Local absolute path in {path.name}')
            target = DOWNLOADS / f'{prefix}-{path.name}'
            copyfile(path, target)
            published.append(target)
        for path in sorted(source.glob('*.png')):
            copyfile(path, ASSETS / f'{prefix}-{path.name}')
    for key, source, prefix in [
        ('charls', charls / 'report.html', 'charls'),
        ('charls-directions', charls / 'research_directions.html', 'charls'),
        ('share', share / 'share/report.html', 'share-first'),
        ('share-supplement', share / 'share_w6_dbs/report.html', 'share-supplement'),
    ]:
        link_map = {p.name.removeprefix(prefix + '-'): '../downloads/' + p.name for p in published if p.name.startswith(prefix + '-')}
        link_map.update({'report.html': 'charls-nutrition-report.html', '../../README.md': '../downloads/nutrition-README.md',
                         'analysis_plan.md': '../downloads/share-supplement-analysis_plan.md'})
        notice = '公开归档版：仅整理既有分析，不新增模型。CHARLS W6 为横断面 pilot，2021–2023 是同一轮的访问年份。'
        if key == 'charls-directions':
            notice += ' 本副本将双人家户咀嚼 PR 的两位小数更正为 1.28（原汇总值 1.28475）；详细表保留完整精度。跨轮次部分仍为设计。'
        if key == 'share':
            notice = '<strong>首轮历史报告：</strong>本页保留首轮 17 模型及当时七包输入／三包缺口的状态。当前三个补充包已归档，共十包；官方纵向权重与 W6 DBS 更新请看<a href="share-supplement-report.html">补充报告</a>。'
        if key == 'share-supplement':
            notice = '<strong>当前补充阶段：</strong>官方 W8→W9 个体纵向权重五模型＋W6 饮食–DBS 可行性＋All-waves 参与状态审计。与首轮结果分别保留。'
        sanitize_report(source, ROOT / 'library' / REPORTS[key][0], prefix, link_map, notice)
    plan = DOWNLOADS / 'share-supplement-analysis_plan.md'
    copyfile(share / 'share_w6_dbs/analysis_plan.md', plan)
    published.append(plan)
    readme = DOWNLOADS / 'nutrition-README.md'
    readme.write_text('''# 营养健康支线公开附件

更新日期：2026-11-14。

- CHARLS W6：饮食与 CES-D-10、功能与口腔、标准化和家户内分析。
- SHARE 首轮：17 个探索模型；保留当时输入状态，纵向更新见补充。
- SHARE 补充：官方 W8→W9 纵向权重五模型、W6 DBS 可行性、All-waves 状态审计。

CSV/JSON 均为统计汇总；PDF 为图表。没有原始授权 ZIP、个人记录、ID 或链接表。
图中 CI 按各报告的聚类近似或 bootstrap 方法解释，未恢复完整分层设计。
饮食条目不等同定量木脂素，CES-D/EURO-D 为筛查量表，观察性结果不能识别因果。

复现网页：在仓库根目录运行 `python3 build_portal.py --pages-only`。
公开表可核对页面数字；完整原始分析需要依官方条款独立申请 CHARLS／SHARE 数据，
遵守访问条件后复现问卷路由、样本选择、权重与模型。此附件本身不构成独立的原始分析复现包。

文件前缀：`charls-`、`share-first-`、`share-supplement-`。
`nutrition-publication-manifest.json` 记录每个公开附件的大小和 SHA-256。
报告中的双人家户口腔咀嚼 PR 从 1.29 更正为 1.28，依据汇总原值 1.284751786654472；未更改结果表。
''', encoding='utf-8')
    published.append(readme)
    manifest = {'updated': '2026-11-14', 'scope': 'Aggregate tables and figures only; no participant records or licensed source archives.',
                'files': [{'file': p.name, 'bytes': p.stat().st_size, 'sha256': sha256(p.read_bytes()).hexdigest()} for p in sorted(published)]}
    manifest_path = DOWNLOADS / 'nutrition-publication-manifest.json'
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with ZipFile(DOWNLOADS / 'nutrition-aggregate-results.zip', 'w', ZIP_DEFLATED) as bundle:
        for path in sorted(published) + [manifest_path]:
            bundle.write(path, path.name)
    links = ''.join(f'<li><a download href="{p.name}">{p.name}</a> <small>({p.stat().st_size:,} bytes)</small></li>' for p in sorted(published))
    catalog = f'<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>营养健康聚合附件目录</title><link rel="stylesheet" href="../assets/style.css"><main class="wrap"><a href="../nutrition.html#reports">← 返回营养健康支线</a><h1>聚合附件目录</h1><p>全部 {len(published)} 个表格、图表及说明文件。仅统计汇总。</p><ul class="link-list">{links}</ul></main></html>'
    (DOWNLOADS / 'nutrition-downloads.html').write_text(catalog, encoding='utf-8')
    print(f'Published {len(published)} aggregate artifacts, four reports, and figure assets.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--charls', required=True, type=Path)
    parser.add_argument('--share', required=True, type=Path, help='Directory containing share/ and share_w6_dbs/.')
    args = parser.parse_args()
    publish(args.charls, args.share)
