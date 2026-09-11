# JavaScript 兼容性规范

> 小工具 JavaScript 的最低兼容基线是 **Android 8.1 出场 Chrome / WebView 61**。最终代码必须能在 Chrome 61 解析和运行；iOS 18.4+ 支持的额外能力只能用于能力检测后的增强路径。Chrome 61 完整支持 ES2017，最终代码以 ES2017 为构建目标。

## 1. 语法基线

最终 zip 中的 JS 须兼容 Chrome 61：

- 直接编写并交付 `.js` 时可使用 ES2017，包括 async / await、`Object.entries` / `Object.values`、`Array.prototype.includes`、`String.prototype.padStart` / `padEnd`。
- ES2018+ 语法须由构建链转译，例如对象 spread、异步迭代、可选链、空值合并、逻辑赋值、class 私有字段、static block、BigInt 字面量和 top-level await；更新的运行时 API 仍须做能力检测或提供必要的局部实现。
- 正则表达式避免依赖 lookbehind、Unicode property escapes 等较新的语法特性。

语法不兼容会在脚本解析阶段直接失败，无法通过运行时 `if` 兜底。

## 2. 有构建链与无构建链

### 直接交付静态三件套

没有现成构建链时，不为兼容性临时引入 Babel、core-js 或新的 npm 依赖；直接按 ES2017 编写。

### 项目已有构建链

可以在源码中使用构建链已支持的新语法。Vite 项目使用以下构建目标：

```js
// vite.config.js
export default {
  build: { target: ['es2017', 'chrome61'] },
}
```

最终产物须：

- 转译到 ES2017 / Chrome 61；
- 只把构建后的静态文件放进 zip，不带 `node_modules`、source map 或构建配置。

转译只解决语法，不会自动补齐所有运行时 API。不要因为构建成功就假定新 API 可用。

## 3. 运行时 API

- ES2017 内置 API 和基础 DOM API 可直接使用。
- `String.prototype.replaceAll`、`Array.prototype.at`、`Object.hasOwn`、`structuredClone` 等更新 API 不应直接作为唯一实现路径。
- 使用非基础 Web API 前先做能力检测；不可用时隐藏增强功能、使用简单替代实现或给出清晰提示。
- 只补功能实际需要的小型本地 fallback，不引入整套通用 polyfill；所有代码仍须随包离线交付。
- 能力检测基于对象 / 方法是否存在，不按 UA、机型或系统版本字符串分支。
- 不为被容器明确禁止的能力添加 polyfill；能力边界仍以 [device-capabilities.md](./device-capabilities.md) 为准。

## 4. 跨内核行为

- 日期字符串使用明确的 ISO 格式或拆分为年月日构造，不依赖非标准字符串解析。
- 不依赖对象遍历顺序表达业务优先级；需要顺序时使用数组。
- 对 `Intl` 格式化结果、字体度量、滚动和软键盘行为保留布局余量，不把不同内核的细微差异当作固定输出。
- 触摸、滚动和安全区规则见 [cross-platform-h5.md](./cross-platform-h5.md)。

## 5. 交付检查

- [ ] 直接交付的 JS 不超出 ES2017；使用更新语法时已有构建链负责转译
- [ ] 使用 Vite 时构建目标包含 `es2017` 和 `chrome61`，且 zip 中只保留最终静态文件
- [ ] 新 Web API 有能力检测和局部降级，不使用 UA 猜测能力
- [ ] 未把语法转译误认为运行时 API polyfill
- [ ] 未进行实际设备验证时标记“兼容性未实测”，不宣称已在真机通过
