# CSS 兼容性规范

> 小工具 CSS 的最低兼容基线是 **Android 8.1 出场 Chrome / WebView 61**。这不等于只能写旧 CSS：交付物采用“Chrome 61 可用的基线层 + 能力检测后的增强层”，在新内核上使用更合适的 CSS 能力。

## 1. 基线原则

- 基线层保证布局、文字、按钮和核心交互在 Chrome 61 可用；增强层可以使用新 CSS 改善布局、视觉或交互。
- 按功能点提供回退与增强，不维护两套完整页面或两份完整样式表，避免双份样式逐渐漂移。
- 根据特性选择检测方法：能用声明级回退的按层叠覆盖，能准确查询的使用 `@supports`，语法检测无法证明实际布局行为时使用 JS 做最小行为检测。
- 浏览器会静默丢弃无法解析的选择器、声明或整条 at-rule。不能像 JS 一样靠异常发现 CSS 不兼容，必须检查最终产物和实际布局。
- 兼容性以最终 zip 内的 CSS 为准。源码使用了构建工具，不代表产物已经兼容。

## 2. Chrome 61 不可作为唯一实现的能力

以下能力晚于 Chrome 61，不能作为唯一实现。先提供基线路径，再用适合该能力的检测方式启用增强。

| 能力 | 基线写法 / 降级方式 |
| --- | --- |
| Flexbox `gap` / `row-gap` / `column-gap` | 基线用子项单边 `margin`；增强用 JS 实际测量 Flex 布局后切换 class，不能只检测 `gap` 属性语法 |
| `aspect-ratio` | 固定媒体尺寸，或用百分比 `padding-top` 比例盒；内容绝对定位 |
| `min()` / `max()` / `clamp()` | 先写固定值、百分比或 `calc()`，再用媒体查询分档 |
| `inset`、`margin-inline`、`padding-block` 等逻辑属性 / 简写 | 使用 `top/right/bottom/left` 与 `margin-left/right`、`padding-top/bottom` 等物理属性 |
| `overflow: clip` | 使用 `overflow: hidden` |
| `:focus-visible` | 先提供 `:focus` 样式；增强规则不能让键盘焦点在基线端消失 |
| `:has()` | 由 JS 在父元素上切换状态 class |
| Container Queries（`@container`） | 使用 viewport 媒体查询，或由 JS 按容器尺寸切换 class |
| Subgrid | 使用普通 Grid、Flex 或显式轨道尺寸 |
| CSS Nesting、Cascade Layers（`@layer`）、`@property` | 已有构建链能可靠展开时才在源码使用；最终产物不得保留为核心规则 |
| `dvh` / `svh` / `lvh` | 先用 `%` / `100vh`；受软键盘影响的全屏高度用 JS 维护 CSS 变量并保留静态兜底 |
| `color-mix()`、`oklab()`、`oklch()` 等现代颜色 | 先写 `#hex`、`rgb()`、`rgba()` 或 `hsl()` 颜色 |
| `backdrop-filter` | 先给不依赖模糊的实色 / 半透明背景；模糊仅作增强，并同时考虑 `-webkit-backdrop-filter` |
| `text-wrap: balance` 等现代排版属性 | 保留普通换行；不要让其决定关键区域高度 |

## 3. 布局与前缀

Chrome 61 可使用 Flexbox、基础 Grid、媒体查询、CSS Variables、`calc()`、transform、transition 和 animation。仍须处理以下跨端差异：

- Flex 子项内有长文本、图片或滚动区域时，按方向显式设置 `min-width: 0` 或 `min-height: 0`，避免内容撑破容器。
- Flex 间距先用子项 `margin` 形成基线；需要时通过行为检测启用 `gap` 并清除 margin。动态增删子项时确认首尾间距仍正确。
- Grid 只使用基础显式 / 隐式轨道；间距使用 Chrome 61 可解析的 `grid-gap`。不要使用 Subgrid、Masonry 或依赖新语法的自动布局。
- 需要隐藏文本时使用 `overflow: hidden; text-overflow: ellipsis; white-space: nowrap`。多行截断使用 `display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: <行数>; overflow: hidden`，并保证截断失效时页面仍可用。
- `user-select`、`appearance`、文字截断和毛玻璃等 WebKit 相关能力按需同时写 `-webkit-` 前缀与标准声明。不要机械给所有属性加前缀。
- 关键操作不能只在 `:hover` 出现；触摸端默认可见，并可用 `@media (hover: hover)` 增加鼠标悬停效果。

## 4. 基线层与增强层

### 声明回退和 `@supports`

先写 Chrome 61 可用的完整基线，再覆盖增强：

```css
.panel {
  background: rgba(255, 255, 255, 0.96);
}

@supports ((-webkit-backdrop-filter: blur(12px)) or (backdrop-filter: blur(12px))) {
  .panel {
    background: rgba(255, 255, 255, 0.72);
    -webkit-backdrop-filter: blur(12px);
    backdrop-filter: blur(12px);
  }
}
```

同一属性使用“旧值在前、新值在后”的回退顺序：

```css
.page {
  min-height: 100vh;
  min-height: var(--app-height, 100vh);
}
```

安全区须先保留普通值，再使用容器注入变量与 `env()`：

```css
.bottom-bar {
  padding-bottom: 0;
  padding-bottom: var(--safe-area-inset-bottom, env(safe-area-inset-bottom, 0px));
}
```

`@supports` 适合检测 `aspect-ratio`、`backdrop-filter`、动态视口单位等能由单个声明准确表达的能力。需要由 JS 切换 class 时，可以使用 `CSS.supports()` 检测同类声明。任何检测路径都必须保留基础样式。

### Flex gap 必须检测布局行为

`CSS.supports('gap', '1px')` 和 `@supports (gap: 1px)` 只能证明浏览器认识该属性和值，不能证明 `gap` 在 Flexbox 中生效；支持 Grid gap、但不支持 Flex gap 的内核也可能通过语法检测。需要启用 Flex gap 时，实际创建一次 Flex 容器并测量：

```js
function supportsFlexGap() {
  var flex = document.createElement('div');
  flex.style.position = 'absolute';
  flex.style.visibility = 'hidden';
  flex.style.display = 'flex';
  flex.style.flexDirection = 'column';
  flex.style.rowGap = '1px';
  flex.appendChild(document.createElement('div'));
  flex.appendChild(document.createElement('div'));
  document.body.appendChild(flex);
  var supported = flex.scrollHeight === 1;
  flex.parentNode.removeChild(flex);
  return supported;
}

if (supportsFlexGap()) {
  document.documentElement.classList.add('supports-flex-gap');
}
```

对应 CSS 只维护一套组件规则，其中 margin 是基线，gap 是增强：

```css
.actions {
  display: flex;
}

.actions > * + * {
  margin-left: 12px;
}

.supports-flex-gap .actions {
  column-gap: 12px;
}

.supports-flex-gap .actions > * + * {
  margin-left: 0;
}
```

行为检测放在包内经典脚本中，并在 `document.body` 存在后、核心页面渲染前执行。检测一次即可，不要在 resize 或渲染循环中反复测量。

不要用 UA、Android 版本或机型字符串决定样式能力。能力检测决定是否启用增强，Chrome 61 基线层始终保留。

## 5. 有构建链与无构建链

### 直接交付静态文件

没有现成构建链时，不为 CSS 兼容性临时引入 PostCSS、Autoprefixer 或新的 npm 依赖；直接按 Chrome 61 基线编写。

### 项目已有构建链

将目标浏览器至少设置为：

```text
Chrome >= 61
ios_saf >= 18.4
```

- 可使用已有的 Autoprefixer 补必要前缀；若源码使用 nesting 等新语法，须确认已有插件会把它转换成普通 CSS。
- Autoprefixer 只补前缀，不会把 Flex `gap`、`aspect-ratio`、`:has()`、Container Queries 或动态视口单位自动改写成等价的旧布局。
- 压缩器也须使用相同浏览器目标，避免把兼容写法重新合并成 Chrome 61 无法解析的现代语法。
- 交付前检查构建后的 CSS；zip 中只保留最终静态产物，不带 source map 和构建配置。

## 6. 视口、安全区与实测

- 页面宽度使用 `%`、Flex 或基础 Grid，不写死 `375px` 等单一机型宽度。
- `100vh` 在移动端地址栏、容器高度变化和软键盘出现时可能不等于可视高度。关键全屏区域优先使用父容器百分比；必须跟随可视高度时，由 JS 监听尺寸变化并维护 `--app-height`，同时保留 `100vh` 回退。
- 安全区规则须配合 `viewport-fit=cover`，具体组合见 [cross-platform-h5.md](./cross-platform-h5.md)。
- 现代桌面浏览器或 PC 模拟器通过不等于 Chrome 61 通过。能够运行旧内核时，至少检查首屏、滚动区、弹层、表单、横竖屏 / 尺寸变化和核心交互；无法运行时在交付说明中标记“Chrome 61 CSS 兼容性未实测”。

## 7. 交付检查

- [ ] Chrome 61 基线层能够独立完成核心布局和交互，新内核通过能力检测启用增强层
- [ ] 未维护两套完整 CSS；只为实际使用的现代能力提供局部回退与增强
- [ ] Flex gap 使用布局行为检测，或仅使用 margin 基线；未把 `@supports (gap: ...)` / `CSS.supports('gap', ...)` 当作 Flex gap 检测
- [ ] `aspect-ratio`、`clamp()`、逻辑属性、`:has()`、Container Queries、Subgrid、CSS Nesting、动态视口单位等实际使用项均有合适的回退与检测 / 构建转换
- [ ] Flex 子项已检查溢出与滚动，必要处有 `min-width: 0` / `min-height: 0`
- [ ] 关键操作在触摸端可见，不依赖 `:hover`；焦点样式不只依赖 `:focus-visible`
- [ ] 安全区、全屏高度、软键盘、长文本和多行截断均有基线回退
- [ ] 使用构建链时已检查最终 CSS，而不是只检查源码或 Autoprefixer 是否运行
- [ ] 未进行 Chrome 61 / Android 8.1 实际验证时明确标记“CSS 兼容性未实测”
