<p align="center">
  <a href="https://nsh.virgogalaxy.com/">
    <img src="apps/playground/public/favicon.svg" alt="Virgo NSH 标志" width="96" height="96" />
  </a>
</p>

<h1 align="center">Virgo NSH</h1>

<p align="center">
  <a href="https://github.com/virgo-galaxy/virgo-nsh/actions/workflows/ci.yml">
    <img src="https://github.com/virgo-galaxy/virgo-nsh/actions/workflows/ci.yml/badge.svg?branch=main" alt="CI status" />
  </a>
  <a href="https://www.npmjs.com/package/@virgo-nsh/highlighter">
    <img src="https://img.shields.io/npm/v/@virgo-nsh/highlighter?logo=npm&amp;cacheSeconds=300" alt="npm version" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license" />
  </a>
  <a href="package.json">
    <img src="https://img.shields.io/badge/node.js-24.x-339933?logo=nodedotjs&amp;logoColor=white" alt="Node.js 24.x" />
  </a>
  <a href="package.json">
    <img src="https://img.shields.io/badge/pnpm-11.25.0-F69220?logo=pnpm&amp;logoColor=white" alt="pnpm 11.25.0" />
  </a>
</p>

<p align="center">
  <a href="README.md">English</a> | 简体中文
</p>

<p align="center">
  <a href="https://nsh.virgogalaxy.com/">打开 Playground</a>
</p>

Virgo NSH（Neural Semantic Highlighting）在浏览器中为源码和文件格式提供语义高亮。
它在 Web Worker 中运行 ONNX 模型，返回经过转义的 HTML 和语义标记区间。

## 快速开始

在使用 Vite 等 ESM 构建工具的前端项目中安装。

```bash
npm install @virgo-nsh/highlighter
```

### 准备模型

npm 包提供高亮引擎和主题。应用需要提供匹配的 ONNX 模型及 JSON 元数据，
浏览器会在首次使用对应模型时下载。

使用 `0.1.0` 或 `0.1.1` 时，下载并解压[对应的模型源码快照](https://github.com/virgo-galaxy/virgo-nsh/archive/7109bac49340b94ad5350778e32ee0d4196c5698.tar.gz)。
在解压后的目录下使用 Node.js 24 和 pnpm 11 运行以下命令。

```bash
pnpm install --frozen-lockfile
pnpm build:packages
node scripts/export-model-assets.mjs --models typescript,css
```

将 `artifacts/browser/models/` 的内容复制到前端项目的 `public/models/`，
保留 `v1/` 目录结构。这两组模型覆盖 JS、TS、JSX、TSX、CSS、SCSS 和 Less。
使用其他版本时，按对应 npm README 中的链接下载快照。
独立模型托管、签名 URL 和按需选择模型见[模型部署指南](docs/model-delivery.md)。

### 高亮代码

在原生 Vite 项目的 `index.html` 中加入以下内容。

```html
<div id="example">
  <pre class="nsh"><code></code></pre>
</div>
<script type="module" src="/main.js"></script>
```

在 `index.html` 同级目录下创建 `main.js`。

```js
import { createHighlighter } from "@virgo-nsh/highlighter";
import "@virgo-nsh/highlighter/theme.css";

const highlighter = createHighlighter({
  modelBaseUrl: "/models/",
  languages: ["tsx", "scss"],
});

const source = "const App = () => <button>Hello</button>;";
const example = document.querySelector("#example");
example.querySelector("code").textContent = source;

try {
  const { html } = await highlighter.highlight(source, { language: "tsx" });
  example.innerHTML = html;
} catch (error) {
  console.error("Could not highlight the example", error);
}
```

运行 `npx vite`，打开命令输出的地址。请通过 HTTPS 或 localhost 访问，并使用
支持模块 Worker、WebAssembly SIMD 和 Web Crypto 的浏览器。多个代码块可以复用同一个
高亮器，应用不再使用它时调用 `close()`。

## React、Vue 和原生 JavaScript

三种接入方式共用同一个 npm 包和模型部署方式。

- [React 示例](examples/react/README.md)提供可复用的 `CodeBlock.tsx`。
- [Vue 示例](examples/vue/README.md)提供可复用的 `CodeBlock.vue`。
- [原生 JavaScript 示例](examples/vanilla/README.md)提供完整的 Vite 页面，并演示如何
  使用 `highlightElement` 高亮已有代码块。

使用 [`observeElement()`](packages/highlighter/README.npm.md#highlight-on-scroll)
可以在已有代码块接近视口时才触发高亮。

## 主题

默认样式包含浅色和深色两套配色。在父元素上设置 `data-nsh-theme="dark"` 即可切换。
导入 `@virgo-nsh/highlighter/themes.css` 可以使用全部三套主题。

[主题切换与自定义 CSS 指南](docs/themes.md)

## 支持的语言与评测

NSH 有 **40 个模型包**，覆盖编程语言和文件格式。JSON/JSONC、XML/SVG 等格式共用
模型。每个推理窗口处理 **512 个 UTF-8 字节**，更长的内容会分成多个窗口处理。

[支持范围、模型大小和评测结果](docs/model-benchmarks.md)

## 本地开发

使用 Node.js 24 和 pnpm 11.25.0 在仓库中启动 Playground。

```bash
pnpm install --frozen-lockfile
pnpm dev
```

打开 <http://127.0.0.1:3000/>。[贡献指南](CONTRIBUTING.md)介绍检查和 PR 流程，
[开发文档](docs/development.md)介绍工作区结构、训练和评估。

## 许可证

项目自行编写的代码和文档采用 [MIT 许可证](LICENSE)。
模型权重和第三方材料适用各自的许可条款。
