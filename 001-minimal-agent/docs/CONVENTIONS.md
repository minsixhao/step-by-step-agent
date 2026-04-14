# 开发规范

## 代码规范

- **所有注释使用中文**: 包括行内注释、文档字符串、函数说明等
- **变量和函数名使用英文**: 保持代码的可读性和通用性
- **文档字符串使用中文**: 模块、类、函数的文档说明使用中文

## Git 工作流

### 分支说明

- `main` - 仅包含文档（README、版本索引、学习路线等）
- `version/xxx` - 各版本的代码分支

### 工作流

**初始化时**:
```bash
# 1. 先创建 main 分支，只放文档
git init
# 创建 README.md 等文档...
git add .
git commit -m "Initial commit: 项目文档"
git branch -M main
git push -u origin main

# 2. 然后创建第一个代码分支
git checkout -b version/001-minimal-agent
# 把代码复制进来...
git add .
git commit -m "version/001-minimal-agent"
git push -u origin version/001-minimal-agent
```

**后续开发**:
- 修改文档 → 在 main 分支修改
- 写代码 → 在 version/xxx 分支
