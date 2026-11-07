<p align="center">
  <a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

<p align="center">
  <img src="assets/banner.jpg" alt="fishtrap：水墨竹筌与鲤鱼" width="100%">
</p>

<h1 align="center">fishtrap · 得鱼忘筌</h1>

<p align="center"><b>得鱼而忘筌。</b><br>
让 Codex 里的 GPT 盯着你真正想要的结果干活，也不再句句设防。</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2f5d8a" alt="MIT 许可证"></a>
  <img src="https://img.shields.io/badge/适用-Codex%20CLI%20与桌面版-1f2933" alt="适用于 Codex CLI 与桌面版">
  <img src="https://img.shields.io/badge/依赖-无-1a7f37" alt="无依赖">
  <a href="https://github.com/shoal-rat/fishtrap-bench"><img src="https://img.shields.io/badge/评测集-fishtrap--bench-b4540a" alt="fishtrap-bench"></a>
  <!-- ARXIV_BADGE -->
</p>

---

我让 GPT-6.1 帮我给一份网申上传证件照。它挑了一张我报国考时准备的照片，连原文件名一起传了上去：`国考报名照片.JPG`。上传成功了，HR 收到的却是一个写着别的用途的文件。

这类失误都不是因为它不懂。就在同一个会话里，它前面还把另一个文件命名得好好的。问题出在注意力的方向：它满足了指令，过了它看得见的检查，却忘了结果最后是给谁看的。我翻了一个月的真实会话，找出 27 起这样的事故，归结为五种模式。fishtrap 就在这些模式发生的地方下手。

<p align="center"><img src="assets/before-after.zh-CN.svg" alt="GPT 容易跑偏的四个时刻：装与不装 fishtrap 的区别" width="100%"></p>

## 安装：交给你的 GPT

把这句话发给 Codex（CLI 或桌面版都行）：

```text
帮我安装 fishtrap：https://github.com/shoal-rat/fishtrap ，按它的 INSTALL.md 来。
```

它只会问你一件事：你对外发文件时用的名字。然后它自己克隆仓库、运行安装脚本、向你汇报。最后一步得你亲手做，因为 Codex 只运行经过人工信任的 hook：在桌面版打开 **设置 → Hooks**（CLI 里输入 `/hooks`），信任 fishtrap 的五个 hook，然后开一个新会话。

<details>
<summary>手动安装</summary>

```bash
git clone --depth 1 https://github.com/shoal-rat/fishtrap ~/.fishtrap
python3 ~/.fishtrap/install.py --name "你的名字" --alt-names "Your Name,其他写法" --profile ~/path/to/your-profile.md
```

装完同样要去信任 hook。`--profile` 可以不填；如果你有简历或个人信息文件，就指向它。安装脚本会先备份 `~/.codex/AGENTS.md` 和 `~/.codex/hooks.json`，重复运行会原地更新。

</details>

<details>
<summary>网页版或 App 里的 ChatGPT</summary>

hook 只在 Codex 里有，但原则部分哪里都能用。把 [`fishtrap/chatgpt-custom-instructions.md`](fishtrap/chatgpt-custom-instructions.md) 的内容粘贴到 **设置 → 个性化 → 自定义指令**，再开新对话。

</details>

## 工作原理

fishtrap 分两层。

**一、带着理由的原则。** 在 `AGENTS.md` 顶部加一小段：动手前先想清楚结果由谁来评判；把数量、必填项这类要求当作目标之内的约束；每条规则只用到它的理由所及的范围。规则一旦脱离理由，就会用过头或者用不到位，所以每条规则都写明了理由。写作部分也有规定：先说结论，只对真正不确定的地方加限定，替你写申请材料时站在你这边说话。

**二、在跑偏的时刻介入的五个 hook。** 会话开头读进去的指令，过了一百多次工具调用就淡了，而出事往往就在这时：我找到的 7 起严重事故里，有 6 起发生在内容离开本机的那一刻。所以 hook 就守在那里。

<p align="center"><img src="assets/how-it-works.zh-CN.svg" alt="fishtrap 的五个 hook 在会话时间线上的位置" width="100%"></p>

| Hook | 什么时候触发 | 让模型想什么 |
|---|---|---|
| 收件人检查 | 上传文件之前 | 对方会从这个文件名、这个文件里看到什么？ |
| 提交前复读 | 提交或发送之前 | 逐项对照，和用户要的一致吗？ |
| 校验提示重构 | 出现“必填 / 不完整”提示之后 | 这一条本该在这里吗？按审核人希望的方式改。 |
| 需求重申 | 新指令带数字、说“继续”“登录好了”，以及会话压缩之后 | 最初的标准是什么？哪些搁置的事现在可以接着做？ |
| 收尾检查 | 一轮较长的工作结束时 | 请求的每一部分都做完了吗？以实际看到的为准，不靠推测。 |

每个 hook 只问一次，然后放模型继续做。它从不替模型做决定，重试一定能通过。hook 脚本只用 Python 标准库，不联网，状态存在 `~/.codex/hooks/fishtrap/`，内部出任何错误都会安静退出，所以 fishtrap 的 bug 永远不会卡住你的 GPT。

## 效果如何

<!-- RESULTS -->

评测集、判分器和每一次运行记录都公开在 [fishtrap-bench](https://github.com/shoal-rat/fishtrap-bench)。论文里有完整的事故研究、设计说明和评测。

## 常见问题

**会不会让它变得莽撞？** 评测专门查了这一点。大约一半的检查项是“防护”：如果 GPT 矫枉过正，比如删掉必须提供的信息、不敢提交、把对方指定的文件名改掉、问一些自己就能解决的问题，都会判失败。

**会多花很多 token 吗？** 原则部分约 1300 个 token，每个会话只读一次。hook 只在触发时追加一小段提示。实测成本见上面的结果。

**只适用于网申吗？** 事故来自网申，评测也围绕网申设计，因为文件名起错的代价在这里最直观。但原则和 hook 本身是通用的：任何上传、发送、填表，或者步骤很多的长任务都适用。

**它会改动我电脑上的什么？** 只动 `~/.codex`（或 `$CODEX_HOME`）里的三处：`AGENTS.md` 顶部一段带标记的内容、`hooks.json` 里的五条记录、`hooks/fishtrap/` 文件夹。你自己的指令和 hook 原样保留。

**怎么检查或卸载？**

```bash
python3 ~/.fishtrap/install.py --check       # 查看安装情况和最近的 hook 活动
python3 ~/.fishtrap/install.py --uninstall   # 只移除 fishtrap，并保留备份
```

## 为什么叫 fishtrap

> 筌者所以在鱼，得鱼而忘筌。——《庄子·外物》

指令、数量要求、校验规则，都是用来捕鱼的筌。抱着筌忘了鱼的 GPT，就会把 `国考报名照片.JPG` 传给 HR。fishtrap 让它的眼睛一直盯着鱼。

## 引用

<!-- CITATION -->

## 许可证

MIT，见 [LICENSE](LICENSE)。
