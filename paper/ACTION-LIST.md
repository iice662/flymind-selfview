# 你接下来要做的事（按依赖顺序，带时间估计与完成判据）

每一步都写清：**改哪个文件的哪一行**、**跑什么命令**、**怎样算做完**。
方括号里的占位符是当前稿子里仅剩的空缺（已核对，全稿只有这些）：

| 位置 | 内容 |
|---|---|
| `paper/manuscript.md` 第 5 行 | 作者与通讯（`[AUTHOR 1]`、`[AUTHOR 2]`、`[EMAIL]`） |
| 第 7 行 | 单位（`[INSTITUTION, CITY, COUNTRY]`） |
| 第 155 行 | `[REPOSITORY URL]` |
| 第 157 / 165 行 | AI 声明里的 `[MODEL NAME/VERSION]`、`[YYYY-MM-DD]`（各两处，改一致） |
| 第 163 行 | `[FUNDING]`、`[COMPETING INTERESTS]`、`[AUTHOR CONTRIBUTIONS]` |
| 参考文献 5 / 7 / 17 | `[VERIFY]` |

填完自查：`Select-String -Path paper\manuscript.md -Pattern '\[[A-Z]'` 应只剩参考文献编号。

---

## 阶段 0（先做这个）修正后的数字落地

`results/CORRECTION.md` 记录了三个缺陷（body-lock 驱动从未实现 → 原来的"零结果"是与自己比较，
是空的；"visual pool" 混进 176 个 Johnston's organ 细胞；pool 与 relay 数组重叠 6 个细胞）以及修正后的
全部结果。电路已重建（`flymind.brain` SHA256 `FC6B544C…47827AB`），8 个新实验族跑完，
**图已重画**（`main1`–`main4`、`main4b`、`supp1`–`supp4`，图注数字现在自动从 CSV 计算），
但正文数字与图注文字仍是旧版——按顺序做：

1. `python tools\digest.py` 打印修正后每个族的均值、对比（d / P / BF）与剂量趋势；
   用它替换 Abstract / Results / Table 1–3 / 图注里的旧数字。`manuscript.md` 顶部横幅已标出
   哪些小节仍是旧数字。
2. 受影响的三节标题与结论已经改好（yaw、冲突剂量、patch 尺寸），每节标题下都留了修正数字块。
3. 重画图：`python tools\make_main_figures.py`（约 1 分钟）。
4. 交稿前自查：`python tools\verify_headline_numbers.py`。

**新增的两个永久性自查**（这次三个缺陷都是它们能一眼抓住的）：
`patch_level_ratio`（操纵是否真的落到它声称的那些细胞上，见每次运行的 stdout 末段）
与 `results/raw/slice-census.csv` 的 `pop_name`（群体是不是模式名说的那个群体）。

---

## 阶段 0b（10 分钟）先决定一件事

你之前说过"不让 AI 写总结和图表"。若你的场合（课程/期刊/单位）禁止 AI 生成正文文字，
**把 `paper/manuscript.md` 当骨架**：结构、数字、表格、图注都可以留，正文每段用自己的话重写一遍。
数字不用核对——它们全部由 `results/raw/*.csv` 生成，且我用脚本逐条对过。

## 阶段 1（30–60 分钟）填掉 4 处占位符

1. **作者 / 单位 / 通讯**：改 `paper/manuscript.md` 第 5、7 行。
2. **三条文献核对**（用 DOI 反查最快，`https://doi.org/...` 打开看卷页）：
   - 参考文献 5：MaleCNS v1.0（Berg et al., *Cell* 2026）——确认卷、页、DOI。
     查不到就用数据集自身的引用格式 + `https://male-cns.janelia.org/download` 上的建议引用。
   - 参考文献 7：Schlegel et al. 2024, *Nature* **634**, 139–152 —— 确认页码。
   - 参考文献 17：Lin et al. 2023, *eLife* **12**, e78484 —— 若核不到，直接**删掉这条**，
     把"环吸引子/CX 连接组"的引用换成列表里已核实的 Seelig 2015 或 Kim 2017（正文相应位置互换即可）。
3. **稿末声明**：CRediT 贡献、竞争利益、致谢、基金（投稿系统通常另填，也放稿末一份）。

**完成判据**：全稿搜索 `[` 不再出现占位符（除方括号引用编号外）。

## 阶段 2（2–4 小时，或让我代做）图

图**已经生成**在 `paper/figures/`：投稿图集 9 张（`main1`–`main4`、`main4b`、`supp1`–`supp4`，
PDF 矢量 + PNG 300 dpi）+ 归档图集 10 张（`fig1`–`fig7`、`fig5b`、`figS1`、`figS3`）。

1. **先看一遍**：
   ```powershell
   explorer D:\projects\science\paper\figures
   ```
   逐张确认坐标轴、单位、误差棒、n 标注。要改配色/字号/面板，改 `tools/make_main_figures.py`
   （或它复用的 `tools/make_figures.py`：`C` 配色、`SHORT` 刻度标签、`rcParams`）后重跑：
   ```powershell
   python tools\make_main_figures.py            # 投稿图集全部
   python tools\make_main_figures.py main4      # 单张
   python tools\make_figures.py fig5            # 归档图集单张
   ```
2. **4 张主图的合并已经做完了**：`main1`（电路与标定）、`main2`（传播）、`main3`（光流）、
   `main4`（朝向：零结果 + 冲突剂量），另加 `main4b` 作对照图（rate/drive 双平、三档增益、
   贝叶斯）。Science 正刊限 4 图时把 `main4b` 并入 `main4` 或移入补充即可。
3. **图注**：`paper/manuscript.md` 的 "Figure legends" 段已按这套编号重写，搬进投稿系统即可。
   务必保留两句：刻度里 `self*` 的星号＝操纵臂；误差棒＝95% CI（不是 SEM）。
4. 决定要不要 **Fig. 1A 的真实解剖示意图**（现在是柱状普查图）。要的话需要另一条数据管线
   （MaleCNS 网格/骨架渲染），我可以做。

**完成判据**：主图 ≤4 张、每张有图注、字体嵌入（PDF 已是）、单栏 3.5 in / 双栏 7.0 in。

## 阶段 3（1–2 小时）仓库与数据可用性

```powershell
cd D:\projects\science
# 建议上传的（合计约 25 MB）
#   flymind.brain                     21.4 MB   回路本体（或改为"脚本可重建"+SHA256）
#   tools/**                          代码：4 个 C# 工具 + 4 个 Python 脚本 + ps1
#   results/**         3.7 MB         逐 trial CSV、stdout、全部 md 报告
#   paper/**                          稿件、图、投稿信、补充材料
#   circuit-schematic.md              电路简图
#   terraria-fly-mod/**               可交互实现（可选）
# 绝对不要上传：
#   malecns\edges.bin                 3.04 GB  ← 写"可由 tools/export_edges.py 重建"
#   malecns\*.feather                 1.0 GB + 43 MB + 14 MB ← 公开可下载，给 URL 即可
```

- 建 GitHub 仓库或 Zenodo（要 DOI 就用 Zenodo）。
- README 要写一条**从零到出图**的命令链；**这一步我可以代写**（含 SHA256 校验、期望运行时间）。
- 拿到 URL/DOI 后回填 `paper/manuscript.md` 第 155 行。

**完成判据**：审稿人能按 README 在 30 分钟内复现 Fig. 4 与 Fig. 5。

## 阶段 4（30 分钟）投稿系统材料

- **Cover letter**：`paper/cover-letter.md` 已写好；只差**推荐审稿人**（建议三类各一人：
  ① 果蝇 CX/朝向回路，② 连接组约束建模，③ 等效性检验/贝叶斯方法）。
- **Reporting summary**（Science 要求）：这是投稿系统的表单，只能你填；需要的话我把每项该写什么列出来。
- 作者贡献、竞争利益、基金号。

## 阶段 5（决定）投哪

有了剂量–反应 + 行为读出（转向保真度）+ 三档增益复现，命中率排序建议：

1. **PLoS Computational Biology** 或 **eLife**：模型 + 方法学 + 行为读数，最匹配，审稿周期可控。
2. **Nature Communications**：如果想把"缺失 vs 矛盾"抬成一般性结论，需要补感受野映射（见下）。
3. **Science（Report 短格式）**：可以试，但要把 4 图压到"缺失 vs 矛盾 + drive-matching 陷阱"两条卖点，
   并把 Limitations 里那三条（切片 1.1% 突触、CX 占比 17.3%、κ 单一标定）主动放到正文。

---

## 我可以继续做的（你回一句话即可）

| 你说 | 我做 | 用时 |
|---|---|---|
| ~~"合并图"~~ | 已完成：`main1`–`main4` + `main4b` + `supp1`–`supp4`，图注同步重写 | — |
| ~~"整理 S2"~~ | 已完成：`paper/supplementary-note-S2.md`（AI 披露 + 提示词全文日志） | — |
| "写 README" | 仓库 README + 一键复现脚本 + 数据可用性段落 | 30 min |
| "Reporting summary" | 逐项列出 Science 表单该填什么 | 20 min |
| "感受野映射" | 下载 `syn-partners`(6.8 GB) + ROI，把 soma 代理换成真实视野区域 | 数小时，最容易被审稿人质疑的一点 |
| "行为闭环" | 让 mod 的 fly agent 直接用下行读出飞，给出"错误自画像 → 飞得更差"的闭环 | 2–3 h |
| "解剖示意图" | Fig 1A 换成 MaleCNS 网格渲染的真实解剖图 | 2–4 h |
