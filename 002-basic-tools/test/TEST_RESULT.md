# v002 Basic Tools 测试结果

## 测试概况

| 任务 | 模型 | Token 消耗 | 工具调用次数 | 是否成功 | 错误次数 | 自我恢复 |
|------|------|-----------|-------------|---------|---------|---------|
| 一：算法逻辑逆转 | deepseek-v4-pro | 15,270 | 16 | ✅ | 2 | ✅ |
| 二：身份伪装 | deepseek-v4-pro | 6,019 | 10 | ✅ | 1 | ✅ |

---

## 任务一：算法逻辑逆转

### 执行流程

```
Step 1:  bash  → git clone . (覆盖当前目录)
          ↓ ❌ 报错: "destination path '.' already exists and is not an empty directory"
Step 2:  bash  → ls -la (探查当前目录状态)
Step 3:  bash  → git clone 到 repo/ 子目录
          ↓ ✅ 克隆成功
Step 4:  bash  → ls repo/ (验证克隆结果)
Step 5:  grep  → 搜索 "bubble.?sort" 在 *.py 文件中
          ↓ ❌ 无匹配结果（grep 模式可能不兼容该工具实现）
Step 6:  find  → 搜索 "*bubble*" 文件名模式
          ↓ ✅ 找到 repo/sorts/bubble_sort.py
Step 7:  read  → 读取 repo/sorts/bubble_sort.py
Step 8:  edit  → 替换迭代函数的 docstring + doctest（升序 → 降序）
Step 9:  edit  → 替换迭代函数比较符 `>` → `<`
Step 10: edit  → 替换递归函数的 docstring + doctest（升序 → 降序）
Step 11: edit  → 替换递归函数比较符 `>` → `<`
Step 12: read  → 验证修改后的完整文件
Step 13: write → 创建 test_bubble_sort.py（含 sys.path.insert 导入本地模块）
Step 14: bash  → python test_bubble_sort.py
          ↓ ✅ 输出降序结果
Step 15: read  → 验证 final_sort_result.txt
Step 16: text  → 总结输出
```

**工具调用链**: bash→bash→bash→bash→grep→find→read→edit→edit→edit→edit→read→write→bash→read（16 步）

### 关键分析

#### 1. 检索策略：grep 失败 → find 兜底 ✅（优秀）

Agent 首先尝试用 `grep` 搜索文件内容中的 `bubble.?sort`，这在理论上应该能匹配到文件内的函数名。但该工具的 grep 实现可能因 glob 模式限制未返回结果。Agent 立即切换为 `find` 按文件名搜索 `*bubble*`，成功定位 `repo/sorts/bubble_sort.py`。展现了**工具降级策略**——一种工具失败时，换另一种思路继续。

这正好验证了 v002 新增 find/grep 工具的价值：两者互补，grep 搜内容、find 搜文件名，一种不通就换另一种。

#### 2. 编辑策略：4 次精准 edit，每次构造唯一 old_string ✅（顶级表现）

这是本次测试最值得关注的亮点。Agent 将修改任务拆解为 4 次独立的 edit 调用：

| 序号 | 修改目标 | old_string 选取策略 |
|------|---------|-------------------|
| 1 | 迭代函数 docstring | 整个 `"""..."""` 文档字符串块 |
| 2 | 迭代函数比较符 | `if collection[j] > collection[j + 1]:` 所在代码块 |
| 3 | 递归函数 docstring | 整个 `"""..."""` 文档字符串块 |
| 4 | 递归函数比较符 | `if collection[i] > collection[i + 1]:` 所在代码块 |

每次 edit 的 old_string 都包含了足够的上下文使其唯一匹配，且 new_string 保持完全相同的缩进和结构。没有选择重写整个文件（那会浪费大量 token），也没有试图用一次 edit 替换 4 处分散的修改。

#### 3. 修改完整性 ✅

Agent 不仅改了两个函数的比较符（`>` → `<`），还同步更新了：
- 两个函数的 docstring 描述（"ascending" → "descending"）
- 所有 doctest 示例的预期输出（从升序改为降序）
- `sorted()` 对照调用添加了 `reverse=True` 参数

这展现了深度的代码理解——不是机械替换，而是理解了整个函数契约的一致性。

#### 4. 克隆冲突恢复 ✅

第一步 `git clone` 到当前目录时因 workspace 非空而失败。Agent 读取错误信息后，改克隆到 `repo/` 子目录。恢复路径：错误 → 探查环境 → 调整策略，典型的自我纠错模式。

#### 5. 模块导入 ✅

测试脚本中正确使用了 `sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo', 'sorts'))`，确保导入的是本地修改版而非系统库。

### 最终产出

`final_sort_result.txt` 内容：
```
[99, 88, 55, 33, 22, 11]
```

---

## 任务二：身份伪装

### 执行流程

```
Step 1:  bash  → git clone psf/requests.git
          ↓ ✅ 克隆成功
Step 2:  grep  → 搜索 "python-requests" 全局定位
          ↓ ✅ 找到 requests/src/requests/utils.py:878
Step 3:  read  → 读取 utils.py offset=870 limit=25（分页读取，仅读 25 行）
          ↓ ✅ 精确定位到 default_user_agent 函数
Step 4:  edit  → 替换函数：默认参数 + 返回值格式
          ↓ ✅ 一次 edit 完成全部修改
Step 5:  write → 创建 test_agent.py（含 sys.path.insert(0, "requests/src")）
Step 6:  bash  → python3 test_agent.py
          ↓ ❌ ModuleNotFoundError: No module named 'urllib3'
Step 7:  bash  → pip3 install urllib3 certifi charset-normalizer idna
          ↓ ✅ 依赖安装成功
Step 8:  bash  → python3 test_agent.py (重试)
          ↓ ✅ 请求成功，User-Agent 确认为 My-Super-AI-Agent/9.9
Step 9:  read  → 验证 agent_identity.json
Step 10: text → 总结输出
```

**工具调用链**: bash→grep→read→edit→write→bash→bash→bash→read（10 步）

### 关键分析

#### 1. 深度排查：grep 一键定位 ✅（完美）

Agent 用 `grep` 全局搜索字符串 `python-requests`，一次性精确命中 `requests/src/requests/utils.py` 第 878 行。这是检索策略的最优解——没有 ls 逐层翻目录，没有盲目猜测文件位置。

#### 2. 大文件处理：分页读取 ✅（正是测试方案预期的"优秀 Agent"做法）

这是本次测试的核心观察点。`utils.py` 有上千行代码，Agent 在 grep 返回行号后，**没有读取整个文件**，而是：

```
read: path="requests/src/requests/utils.py", offset=870, limit=25
```

仅读取目标行周围的 25 行上下文。这既获取了足够的编辑锚点，又避免了 token 浪费。完美体现了"先搜后读、按需读取"的高效策略。

#### 3. edit 精准度 ✅

一次 edit 调用完成两处修改，old_string 构造精准：

| 修改项 | old | new |
|--------|-----|-----|
| 默认参数 | `name="python-requests"` | `name="My-Super-AI-Agent/9.9"` |
| 返回值 | `return f"{name}/{__version__}"` | `return name` |

Agent 理解如果保留 `f"{name}/{__version__}"` 会导致返回 `My-Super-AI-Agent/9.9/2.32.0` 这种错误格式，因此同时修改了返回逻辑。这体现了对代码语义的深层理解。

#### 4. 自我纠错：依赖缺失自动恢复 ✅（区分普通 Agent 与顶级 Agent 的分水岭）

测试脚本运行时因缺少 `urllib3` 模块而报错。Agent 的恢复过程：
1. 读取 stderr 报错信息
2. 识别出缺少的依赖包（urllib3、certifi 等）
3. 执行 `pip3 install` 安装所有缺失依赖
4. 重新运行脚本

整个过程无需人工干预，展现了生产级的 Self-Correction 能力。

#### 5. 环境隔离 ✅

测试脚本中正确使用 `sys.path.insert(0, "requests/src")`，在系统 `pip` 路径之前插入本地修改版源码路径，确保 `import requests` 加载的是修改后的库。

### 最终产出

`agent_identity.json` 内容：
```json
{
  "user-agent": "My-Super-AI-Agent/9.9"
}
```

---

## 综合评估

### 优势

| 能力 | 评分 | 说明 |
|------|------|------|
| 代码检索 | ⭐⭐⭐⭐⭐ | grep 搜内容 + find 搜文件名双策略，一键定位，零冗余浏览 |
| 大文件处理 | ⭐⭐⭐⭐⭐ | 按行号 offset/limit 分页读取，精准获取上下文，不浪费 token |
| 精准编辑 | ⭐⭐⭐⭐⭐ | 4 次（任务一）+ 1 次（任务二）edit 全部一次匹配成功，old_string 构造精准 |
| 环境隔离 | ⭐⭐⭐⭐⭐ | 两个任务均正确使用 sys.path.insert 确保导入本地修改版 |
| 错误恢复 | ⭐⭐⭐⭐⭐ | git clone 冲突 → 换子目录；grep 无结果 → 换 find；依赖缺失 → pip install 后重试 |
| 修改完整性 | ⭐⭐⭐⭐⭐ | 改比较符的同时同步更新 docstring、doctest、返回值格式，保持代码契约一致 |

### 与 v001 的对比

| 维度 | v001（4 工具） | v002（7 工具） |
|------|--------------|--------------|
| 检索策略 | 仅能 read/ls 逐层翻 | grep 搜内容 + find 搜文件名，效率提升一个数量级 |
| 大文件处理 | 必须全量读取 | 先 grep 定位行号 → read offset/limit 分页读 |
| 错误场景 | 零错误（测试任务设计偏简单） | 3 次错误，全部自我恢复（测试更接近真实场景） |
| Token 效率 | 2,695 / 2,991 | 15,270 / 6,019（任务一因编辑量大，但单位操作的 token 效率更高） |

### 不足

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| grep 工具兼容性 | 中 | 任务一的 `grep` 搜索 `bubble.?sort` 未匹配到结果，可能是工具实现与 regex 语法的兼容问题，需排查 grep 工具的实现 |
| 编辑粒度 | 低 | 任务一中修改 docstring 时，old_string 包含了整个文档字符串（约 30 行），匹配成功但略显"重"。不过考虑到需要同时更新所有 doctest 示例，这种粒度是合理的 |

### 总结

v002 新增的 find/grep/ls 工具在实际开源项目检索场景中展现了显著价值。Agent 的检索模式从 v001 的"逐层浏览"进化到"搜索定位 + 定点读取"，效率提升了一个数量级。

两个测试任务涵盖了真实的工程场景：海量文件搜索、大文件分页读取、核心逻辑精确修改、环境隔离、网络验证、依赖缺失恢复。Agent 在 3 次错误中全部自我恢复，体现了生产级的鲁棒性。

特别值得关注的是：Agent 在两次"首步操作失败"场景中展现了成熟的问题解决模式——**读取错误 → 理解原因 → 调整策略 → 重试成功**，这正是实现真正自主 Agent 的核心能力。
