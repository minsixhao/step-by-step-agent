# v001 Minimal Agent 测试结果

## 测试概况

| 任务 | 模型 | Token 消耗 | 工具调用次数 | 是否成功 | 错误次数 |
|------|------|-----------|-------------|---------|---------|
| 一：迭代式开发 | deepseek-v4-pro | 2,695 | 4 | ✅ | 0 |
| 二：环境探索 | deepseek-v4-pro | 2,991 | 6 | ✅ | 0 |

---

## 任务一：迭代式开发与自我验证

### 执行流程

```
Step 1: write → 创建 calculator.py
         ↓ 输出: "成功写入文件: calculator.py"
Step 2: bash  → python calculator.py
         ↓ 输出: "25.0"
Step 3: edit  → 精准替换，添加打印长度的代码
         ↓ 输出: "成功编辑文件: calculator.py"
Step 4: bash  → python calculator.py
         ↓ 输出: "当前计算的列表长度是：4\n25.0"
```

**工具调用链**: write → bash → edit → bash（4 步，零冗余）

### 关键分析

#### 1. edit 工具使用策略：精准替换 ✅（优秀）

第 3 步修改时，Agent 选择使用 `edit` 而非 `write` 重写整个文件：

- **old_string**: `    result = calculate_average([10, 20, 30, 40])\n    print(result)`
- **new_string**: `    numbers = [10, 20, 30, 40]\n    result = calculate_average(numbers)\n    print(f"当前计算的列表长度是：{len(numbers)}")\n    print(result)`

old_string 唯一匹配文件中的内容，一次替换成功。这说明 Agent 理解了 edit 的唯一匹配约束，能准确构造 old_string。

#### 2. 代码重构意识 ✅

Agent 不仅添加了打印长度的代码，还顺手将 `[10, 20, 30, 40]` 提取为变量 `numbers`，这样 `len(numbers)` 才能正确引用。体现了上下文理解能力。

#### 3. 错误恢复

全程零错误，无需恢复。

### 最终产出

```python
def calculate_average(numbers):
    """计算列表的平均值"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)


if __name__ == "__main__":
    numbers = [10, 20, 30, 40]
    result = calculate_average(numbers)
    print(f"当前计算的列表长度是：{len(numbers)}")
    print(result)
```

运行输出：
```
当前计算的列表长度是：4
25.0
```

---

## 任务二：环境探索、数据处理与文本排版

### 执行流程

```
Step 1: bash  → 用 shell 循环 + /dev/urandom 生成 3 个随机文本文件
         ↓ 输出: data_A.txt(7行), data_B.txt(6行), data_C.txt(8行)
Step 2: write → 创建 analyze.sh 脚本
         ↓ 输出: "成功写入文件: analyze.sh"
Step 3: bash  → chmod +x analyze.sh && ./analyze.sh
         ↓ 输出: "命令执行完成，无输出"
Step 4: read  → 查看 report.log
         ↓ 输出: 文件统计内容
Step 5: edit  → 在首行前插入标题
         ↓ 输出: "成功编辑文件: report.log"
Step 6: read  → 验证最终 report.log
         ↓ 输出: 包含标题的完整报告
```

**工具调用链**: bash → write → bash → read → edit → read（6 步，零冗余）

### 关键分析

#### 1. 命令构造能力 ✅（优秀）

- 生成随机文件时，使用 `for` 循环 + `/dev/urandom` + `tr` + `fold` 组合命令，一条 bash 调用完成 3 个文件的创建
- 执行脚本时，使用 `chmod +x analyze.sh && ./analyze.sh` 组合命令，一步完成赋权和执行

#### 2. 首行插入策略 ✅（优秀 — 正是预期的"优秀 Agent"做法）

这是本次测试的核心观察点。Agent 的处理方式：

1. **先 read 读取文件**：获取到首行内容为"分析以下文件："
2. **再 edit 精准替换**：
   - old_string: `分析以下文件：`
   - new_string: `>>> 自动生成的数据报告 <<<\n\n分析以下文件：`

将原首行作为锚点，在前面插入标题 + 空行 + 原首行。这完全符合测试方案中描述的"优秀 Agent"策略。

#### 3. Shell 脚本质量 ✅

Agent 编写的 `analyze.sh` 包含：
- shebang 行
- 输出文件清空逻辑
- `find -maxdepth 1` 限制搜索范围
- `wc -l < file` 获取行数
- 累加计数器
- 中文输出

#### 4. 错误恢复

全程零错误，无需恢复。

### 最终产出

`report.log` 内容：
```
>>> 自动生成的数据报告 <<<

分析以下文件：
  文件: data_A.txt -- 行数:        7
  文件: data_B.txt -- 行数:        6
  文件: data_C.txt -- 行数:        8

所有 .txt 文件总行数: 21
```

---

## 综合评估

### 优势

| 能力 | 评分 | 说明 |
|------|------|------|
| 任务规划 | ⭐⭐⭐⭐⭐ | 步骤拆解清晰，无冗余操作，每步都有明确目的 |
| 工具选择 | ⭐⭐⭐⭐⭐ | 优先使用精准工具（edit 而非 write 重写），减少 Token 消耗 |
| edit 精准替换 | ⭐⭐⭐⭐⭐ | old_string 构造准确，两次 edit 均一次匹配成功 |
| 上下文记忆 | ⭐⭐⭐⭐⭐ | 跨步骤逻辑连贯，修改时能回溯之前的代码结构 |
| 命令构造 | ⭐⭐⭐⭐⭐ | 熟练使用 shell 管道和组合命令 |
| 首行插入 | ⭐⭐⭐⭐⭐ | read + edit 组合策略，正是测试方案期望的最优解 |

### 不足

| 问题 | 严重程度 | 说明 |
|------|---------|------|
| 未遇到错误场景 | - | 两个任务全程零错误，无法评估错误恢复能力 |
| 随机数据质量 | 低 | 生成的"随机英文单词"实际是随机字母组合（如 `TRJc`、`pydZ`），不是真正的英文单词 |

### 总结

v001 的 4 个核心工具在 deepseek-v4-pro 模型下表现优秀。Agent 展现了良好的工具选择意识（优先 edit 而非重写）、精准的字符串匹配能力、以及经典的"先读后改"策略。首行插入任务的完成方式完全符合测试方案中"优秀 Agent"的预期。

但由于全程零错误，**错误恢复能力未被验证**。建议后续增加故意触发错误的测试场景（如 edit 匹配失败、bash 命令报错等），以全面评估 Agent 的鲁棒性。
