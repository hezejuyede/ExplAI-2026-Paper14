# ExplAI-2026 / Paper 14 / R5 / 2026-11-04 — 科研与投稿最终核对

## 已经真实完成
- Dry Bean 原始 13,611 行 / 去重 13,543 行；Rice 3,810 行：均已用真实 CSV 数据运行五折，三种模型、两坐标表示。
- R5 表 4–8 与附录使用的是同一套新执行实验，不再把旧稿历史均值与本次复算输出混写。
- Table 4 增加 mean original-point TV；Table 5 有折间 SD、范围及概率基准；Table 5b 有 B0/B1 内部排名稳定性及 max block drift；Appendix A 有 36 组六变量 B0/B1 mean±SD（180 条原始折块记录在 CSV 中）。
- 执行 1,000 次配对 Bootstrap；重算 SHAP 0.50.0 和 LR permutation；298,183 条样本-块 TV 界诊断 0 次违规。
- 13,611 原始版 vs 13,543 去重版复算：Dry Bean 两个核心块的方向均分别保持 15/15；原稿数字差异另存 CSV，不隐藏差异。
- PDF 已自动生成 12 页 A4，嵌入 Libertinus Serif/Sans，图表用 Matplotlib 绘制，无生成式 AI 图像。
- 两位审稿人逐条回复 Word/PDF，CMT 最简修改说明 PDF 可编辑并已渲染核查。

## 作者审核和期刊/会议条件：仍不能伪称已完成
1. CMT 最新邮件要求 3 项：新版 PDF、亲笔签署的 CEUR 作者协议扫描件、简短修改说明。签字必须本人在纸上用墨水完成，当前没有签字版本。
2. 会方 CEURART ODT 官方模板（https://drive.google.com/file/d/1WI8lFBUaIqG3HC844HEWPzydL63eUvLt/view?usp=sharing）暂时未取得实际模板字节。R5 已通过 A4、字体、脚注、页数预检，**并非官方模板精确一致性证明**。提交前建议把作者审定内容粘贴/移植到官方 ODT 并再次导出。
3. 审稿人要求真正公开、版本固定的代码归档。目前有完整的本地 ZIP、源码、原始 CSV 与 SHA256，但**尚未发布 GitHub/Zenodo 永久 URL/DOI**，不能编造链接。发布后填入论文 Data and Code Availability。
4. 历史稿没有完整记载 LR-C、HGB 学习率和各模型种子绑定。R5 实际使用的 LR-C=1、HGB 学习率=0.1、种子设定是有记录的新独立复算，不能倒称原作者历史超参数。对账文件详列数值差异。
5. AI 工具参与了这一版文本修订和分析代码辅助，必须如实由作者核对披露并自审是否满足 CEUR 生成式 AI 政策。任何由 AI 建议的科学解释必须经作者独立审核，否则不应提交。
6. 作者署名与 ORCID 以 CMT 的三作者顺序为准：Xin Li、Bojian Guo、Asel Kartanova。历史 Author Console 显示后两人 Attested=No，提交前请本人核查作者授权。
7. 最终演讲人、Zoom 或现场选择及提交动作依然需要 CMT 中的作者本人完成。该 ZIP 不代表已经最终录用或正式出版。

## 运行方式
`python VERIFY_EXISTING_RESULTS.py`：快速检查已有数据、哈希、关键 30/30。
Windows 双击 `RUN_REAL_UCI_WINDOWS.bat`；Linux/macOS 运行 `bash RUN_REAL_UCI_UNIX.sh` 可独立重跑真实数据（需 Python 3.13 安装 requirements.txt，运算比较耗时）。

## 数据来源
- UCI Dry Bean (2020) DOI:10.24432/C50S4B，CC BY 4.0。
- UCI Rice (Cammeo and Osmancik) (2019) DOI:10.24432/C5MW4Z，CC BY 4.0。

## 截止与三项 CMT 文件
会方最新邮件：2026-11-08 23:59 AoE（Bishkek 2026-11-09 17:59）。`CMT_upload_candidates/` 仅有 PDF 和 summary；作者协议没有签字，没有上传到 CMT。

当前状态：**科研证据对接和审稿回复实际完成，剩余作者专属手续与正式模板/公开发布未完成，严禁把 AUTHOR_REVIEW 当作无条件清稿。**
