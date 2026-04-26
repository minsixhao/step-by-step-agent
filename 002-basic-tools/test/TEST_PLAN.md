# v002 Basic Tools 测试方案

## 测试目标

针对 v002 新增的 3 个工具（find、grep、ls），验证 Agent 的：
- **代码检索能力**：能否在海量文件中用正确策略快速定位目标（grep 搜索内容 → find 搜索文件名 → read 定点读取）
- **精准编辑能力**：在真实开源项目的复杂文件中，能否构造精确的 old_string 进行局部替换
- **环境隔离能力**：测试脚本中是否知道用 `sys.path.insert` 覆盖系统库，确保导入的是本地修改版
- **错误恢复能力**：遇到依赖缺失、目录非空等运行时错误时，能否读取报错并自我纠错

## 测试环境

- **模型**: deepseek-v4-pro
- **工作目录**: `002-basic-tools/workspace/`
- **可用工具**: read、write、edit、bash、find、grep、ls

---

## 测试任务一：算法逻辑逆转（偏重代码理解与精准编辑）

### 测试重点

海量文件中定位特定算法、理解核心逻辑、精确替换关键比较符、跨目录模块导入。

直接复制下面的 Agent Prompt，粘贴到 `python run.py` 的输入框里：

### Agent Prompt

> 请将 GitHub 上的 `https://github.com/TheAlgorithms/Python` 仓库克隆到当前工作区。我需要你找到经典的『冒泡排序（Bubble Sort）』算法的实现代码，并修改它的核心逻辑，使其从默认的升序排序改为**降序排序**。
>
> 完成源码修改后，请在工作区根目录新建一个 Python 测试脚本，在脚本中引入你刚刚修改过的本地冒泡排序函数，并对数组 `[99, 22, 55, 11, 88, 33]` 进行排序。
>
> 最后，执行这个测试脚本，并将排序后的完整数组结果输出到一个名为 `final_sort_result.txt` 的文件中。

### 验证方法

1. **结果验证**：打开 `final_sort_result.txt`，内容是 `[99, 88, 55, 33, 22, 11]` 则通过。
2. **Session 记录分析点**：
   - **检索策略**：是否优先用 grep/find 定位？还是无脑 ls 逐层翻？
   - **编辑策略**：4 处修改（迭代函数比较符、递归函数比较符、两个 docstring）是分别 edit 还是重写整个文件？
   - **模块导入**：测试脚本是否正确设置 `sys.path` 引入本地修改版？
   - **克隆冲突**：workspace 非空时 git clone 会报错，Agent 如何恢复？

### 预期输出

`final_sort_result.txt` 内容：
```
[99, 88, 55, 33, 22, 11]
```

---

## 测试任务二：知名框架底层的"身份伪装"（偏重深度搜索与网络验证）

### 测试重点

复杂工程目录中搜索不起眼的配置项、分页读取大文件、环境隔离、网络验证、依赖缺失时的自我纠错。

直接复制下面的 Agent Prompt，粘贴到 `python run.py` 的输入框里：

### Agent Prompt

> 请将 Python 知名请求库的源码 `https://github.com/psf/requests` 克隆到工作区。我需要你修改它的底层源码，改变其默认的 HTTP 请求头特征。
>
> 请在它的源码中寻找定义默认 `User-Agent` 的位置（通常包含 `python-requests` 字样），并将其精确替换为 `My-Super-AI-Agent/9.9`。
>
> 修改完毕后，请在工作区根目录编写一个 Python 测试脚本。请注意，**脚本中必须直接导入并使用你刚刚修改的本地库代码**（绝不能使用系统 pip 自带的 requests）。让该脚本对 `https://httpbin.org/user-agent` 发起一个 GET 请求。
>
> 最后，将该请求返回的 JSON 响应内容完整保存到工作区根目录的 `agent_identity.json` 文件中。

### 验证方法

1. **结果验证**：打开 `agent_identity.json`，包含 `"user-agent": "My-Super-AI-Agent/9.9"` 则通过。
2. **Session 记录分析点**：
   - **深度排查**：是否 grep 全局搜索 `python-requests` 一键定位到 `utils.py`？
   - **大文件处理**：`utils.py` 上千行，是分页读取（offset/limit）还是一口气读全文件？
   - **环境隔离**：测试脚本是否用 `sys.path.insert` 覆盖系统 pip 版本？
   - **自我纠错**：运行脚本时大概率因缺少依赖报错，Agent 能否根据 stderr 自行安装依赖并重试？

### 预期输出

`agent_identity.json` 内容应包含：
```json
{
  "user-agent": "My-Super-AI-Agent/9.9"
}
```
