# Review Radius

![Review Radius 英文主视觉，传达修复审查意见背后模式的理念](assets/readme/review-radius-hero.png)

**修复审查意见所揭示的同类缺陷。**

一项面向 Codex、以证据为依据的 GitHub PR 审查反馈处理技能。

Review Radius 以审查意见为起点，在明确边界内检查相关代码中是否还存在
由同一原因造成的缺陷。它先验证反馈，再提炼被破坏的不变量，检查相关代码
范围，最后依据实现状态和验证证据完成审查响应。可安装的技能 ID 仍为
`review-response`。

[English](README.md) · [한국어](README.ko.md) ·
[设计](docs/design.md) ·
[实验](docs/experiments/2026-08-04-code-navigation-tool-routing.md) ·
[品牌指南](BRAND.zh-CN.md)

## 为什么选择 Review Radius

审阅者通常指出最先显现的症状。如果只修改被点名的那一行，同类缺陷可能
仍留在并列实现、别名调用方、失败路径、配置变体或测试中。

![审查意见如何扩展为同类缺陷检查、有边界的审计和证据闭环](assets/readme/review-radius-workflow.png)

检查半径只扩展到已验证的原因和 PR 获准变更的范围。它比逐行被动修补更
完整，也比借机进行无关重构更克制。

## 工作原则

1. **把意见视为信号。** 保留审阅者观察到的事实，在确定修复边界前提炼
   被破坏的不变量。
2. **有边界地扩展。** 检查可信的相关代码，但不把一次审查变成无关的清理
   工作。
3. **用证据完成闭环。** 对候选项分类，验证不变量，并且只在实现状态足以
   支持结论时解决审查会话。

## 安装

```sh
npx skills add <repository-url> \
  --skill review-response \
  --agent codex \
  -y
```

本地开发时，可使用当前检出目录：

```sh
npx skills add "$PWD" --skill review-response --agent codex -y
```

处理 PR 审查反馈时，以 `$review-response` 调用该技能。

## 导航策略

工具按问题类型选择，不会机械地全部执行：

- 用 `rg` 查找字面量和配置；
- 用 AST 查找语法结构相似的代码；
- 用 LSP 确认符号、别名、实现和调用方；
- 用最新代码图检查有边界的直接或传递关系；
- 用聚焦测试或运行时观察确认动态行为。

在合成 TypeScript 固件中，压缩路由的召回率和精确率均为 100%，令牌代理值
为 451；原始文本搜索的代理值为 1694。这只验证路由机制，并不能证明其在
大型真实仓库中的性能。

## 边界

Review Radius 不会：

- 把一条审查意见扩大为通用重构；
- 仅凭文本相似或推断出的图关系确认缺陷；
- 依据单一搜索工具宣称检查完整；
- 为了让 PR 看起来已清理完毕而关闭含糊或受阻的反馈；
- 取代仓库测试、CI 或运行时证据。

项目名称为 Review Radius，`review-response` 是保持兼容的技能 ID。公开
冲突检查未在 GitHub 和主要包注册表中发现同名项目，但
`reviewradius.com` 已被注册，商标可用性仍未确认。请参阅
[简体中文品牌指南](BRAND.zh-CN.md)和
[名称与语言验证记录](docs/brand/name-and-language-validation.md)。

## 许可证

Review Radius 采用 [MIT License](LICENSE)。
