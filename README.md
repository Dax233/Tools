# formulacalc

把 Word 里复制的公式（UnicodeMath 线性文本）直接粘进终端就能出数。

这是 [Dax233/Tools](https://github.com/Dax233/Tools) 中
`bridgeDesign/wordFormulaCalculator.py` 的翻新版本：
旧脚本用字符串 replace 链 + 裸 `eval()` 硬凑，这次换成了一个**独立实现的
UnicodeMath 子集解析器**——没有 eval、没有 numpy/colorama，零运行时依赖。

```text
Word 公式  "sin" 30^∘ + √(16)
   ↓ 复制 / 粘贴
formulacalc  →  4.5
```

## 这是什么

2024 年桥梁设计课的 Word 工作流：在 Word 里用公式编辑器写算式（复制出来是 UnicodeMath
线性文本），粘进终端，得到数值结果。旧脚本完成了这件事，但留下一堆事故：

| 旧脚本的问题 | 现在 |
| --- | --- |
| 裸 `eval()`，`__import__("os").system(...)` 真的会执行 | 解析成 AST 后按白名单求值，任何 Python 代码都进不来 |
| cos/tan 分支复制粘贴了 `print(np.sin(...))`，求值时会喷 debug 数字 | 求值阶段不打印任何东西 |
| `∜` 分支的 while 条件写成了 `√`，四次根号是死代码 | 递归下降直接支持 `∜` |
| `"sin" x`、`√(4` 这类输入会卡进不收敛的 while | 解析期直接抛 `ExpressionError` |
| 角度用 `int()` 截断，`30.5°` 算错 | 支持小数/负数角度 |
| 每次计算都顺手 `pyperclip.copy()` | 只有显式 `--copy` 才写剪贴板 |
| 裸 `except Exception` 吞掉一切 | 明确的错误信息 + 退出码 |

## 安装

需要 Python >= 3.9（实现只用了标准库）。

```bash
python -m venv .venv
.venv/bin/pip install -e .

# 可选：要用 --clipboard / --copy 再装剪贴板依赖
.venv/bin/pip install -e '.[clip]'
```

不安装也能在仓库根目录直接用 `python -m formulacalc` 运行。
安装后会得到 `formulacalc` 命令（entry point）。

## 用法

### 1. 位置参数

```bash
formulacalc '"sin" 30^∘ + √(16)'
# 4.5
```

注意表达式里有引号、`^`、空格时要用单引号包起来，防止 shell 抢先处理。

### 2. 从 stdin 读（管道 / 交互粘贴）

```bash
echo '3×4÷2' | formulacalc
# 6

# 交互式：输入 formulacalc 回车，然后从 Word 粘贴公式，Ctrl-D 结束
formulacalc
```

stdin 的换行会被当作空白，所以多行粘贴也 OK。

### 3. 剪贴板

```bash
pip install 'formulacalc[clip]'      # 可选依赖
# Linux 还需要 xclip 或 xsel

formulacalc --clipboard             # 直接算剪贴板里的公式
formulacalc '"sin" 30^∘' --copy     # 算完把结果写回剪贴板
```

默认**不会**读写剪贴板；只有 `--clipboard` / `--copy` 才会碰它。

### 4. 输出控制

```bash
formulacalc '1/3' --precision 6     # 0.333333
formulacalc '"cos" 60^∘' --debug    # stderr: 归一化: cos 60；stdout: 0.5
formulacalc '2*3' --json            # {"expression": "2*3", "normalized": "2*3", "result": 6.0}
```

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 计算成功 |
| 1 | 表达式解析 / 求值错误（`ExpressionError`） |
| 2 | 用法或输入错误（缺少输入、`--clipboard` 不可用、参数冲突……） |

结果只走 stdout，错误只走 stderr，方便脚本里 `result=$(formulacalc ...)`。

## 支持的语法映射

归一化阶段把 Word/UnicodeMath 的符号翻译成 ASCII 记号，解析器只认 ASCII：

| Word / UnicodeMath 写法 | 归一化后 | 含义 |
| --- | --- | --- |
| `×` `·` `⋅` `✕` | `*` | 乘法 |
| `÷` `／` | `/` | 除法 |
| `−` `–` `—` `－` | `-` | 减号 |
| `＋` `＊` `％` | `+` `*` `%` | 全角运算符 |
| `^` `**` | `**` | 乘方（右结合） |
| `√` | — | 平方根（可嵌套） |
| `∜` | — | 四次根号（可嵌套） |
| `(` `)` `[` `]` `{` `}` `〖` `〗` `（` `）` | `(` `)` | 括号（全部视作圆括号） |
| `"sin"` `“cos”` 等引号 | 去掉引号 | Word 复制函数名时带的引号 |
| `^∘`、`°` | 去掉 | 角度标记（三角函数默认就是角度制） |
| `%` | — | 百分比后缀，`50%` = 0.5 |
| `π` / `pi` | — | 圆周率常量 |
| 全角数字 `０`–`９` | `0`–`9` | 数字 |

支持的函数：

| 函数 | 说明 |
| --- | --- |
| `sin` / `cos` / `tan` | **按角度制**计算（`sin 30` = `sin(30°)` = 0.5），支持小数/负数 |
| `sqrt(x)` 或 `√x` | 平方根 |
| `root4(x)` 或 `∜x` | 四次根号 |

算符优先级（从低到高）：`+ -` → `* /`（含隐式乘法）→ 一元正负号 → `**` → `%`。

隐式乘法：`2(3+4)`、`(1+2)(3+4)`、`2√9`、`2π`、`2sin(30)` 都按乘法处理。

## 安全说明

* 源码里**没有** `eval` / `exec` / `compile`，`tests/test_security.py` 会扫描包内所有源码的 AST 来保证这一点；
* 求值器只认六种 AST 节点（数字、常量、一元/二元运算、函数、百分比），认不出的节点直接报错；
* 函数表写死在源码里，不存在"按名字从 globals() 里取函数"的路径；
* 输入长度上限 4096 字符、语法树嵌套上限 64 层、指数绝对值上限 1000，防止 DoS；
* 未知标识符在**解析阶段**就抛 `ExpressionError`——`__import__("os").system(...)` 根本走不到求值；
* `--clipboard` / `--copy` 是唯一会读写系统剪贴板的入口，默认完全静默。

## 测试

```bash
python -m venv .venv
.venv/bin/pip install pytest
.venv/bin/python -m pytest -q
```

测试覆盖：

* 旧脚本事故表的每一条（三角函数、根号、幂、百分比、隐式乘法、括号变体……）；
* 求值时**不打印任何杂讯**；
* 小数/负数角度、嵌套根号、嵌套函数、`π` 常量；
* 除零、负数开根、NaN/∞、超长输入、超深括号、未知变量（不死循环）；
* CLI 退出码、stdout/stderr 分流、stdin 管道、`--copy` 只在显式指定时才写剪贴板；
* 源码无 `eval`/`exec` 扫描、注入不执行、无第三方依赖。

## 与旧脚本的迁移

旧入口 `bridgeDesign/wordFormulaCalculator.py` 保留为**薄兼容壳**，旧逻辑已全部删除：

```bash
# 旧习惯仍然可用（会提示已迁移，然后调用新包）
python bridgeDesign/wordFormulaCalculator.py '"sin" 30^∘'

# 等价的新写法
python -m formulacalc '"sin" 30^∘'
formulacalc '"sin" 30^∘'        # 安装后
```

行为差异（迁移时注意）：

1. **默认不写剪贴板**：旧脚本每次计算都会 `pyperclip.copy()`；现在需要 `--copy`。
2. **不再有交互式 `stop` 循环**：改成一次性 CLI，需要连续计算时用管道或 shell 循环。
3. **不再依赖 numpy/colorama**：三角函数用标准库 `math`，角度制语义与旧脚本一致。
4. **错误不再是"表达式有误: ..."一段文本**，而是退出码 1 + stderr 上带位置信息的错误（位置指回你粘贴的原文）。
5. 旧脚本的 `∜` 死代码、cos/tan debug 打印、`int()` 角度截断都修掉了。

## 仓库内其它文件

本次翻新**只**新增/修改与 wordFormulaCalculator 相关的文件：

* 新增：`formulacalc/`、`tests/`、`pyproject.toml`、`README.md`；
* 修改：`bridgeDesign/wordFormulaCalculator.py`（改为兼容壳）、`.gitignore`（忽略 venv/缓存）。

`wordtools/*.bas` 宏、`bridgeDesign/db.py`、`PACounter.py`、
`calibrationK0K1Effection.py`、`requirement.txt`、`LICENSE` 均未改动。

## 许可

AGPL-3.0-or-later（与原仓库一致）。新增文件头均带
`# SPDX-License-Identifier: AGPL-3.0-or-later`。
