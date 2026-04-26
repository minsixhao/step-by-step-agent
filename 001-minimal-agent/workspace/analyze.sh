#!/bin/bash

# 设置输出文件
OUTPUT="report.log"

# 清空输出文件
> "$OUTPUT"

# 找出所有 .txt 文件
txt_files=$(find . -maxdepth 1 -name "*.txt" -type f)

# 总行数计数器
total_lines=0

echo "分析以下文件：" >> "$OUTPUT"

for f in $txt_files; do
    fname=$(basename "$f")
    lines=$(wc -l < "$f")
    echo "  文件: $fname -- 行数: $lines" >> "$OUTPUT"
    total_lines=$((total_lines + lines))
done

echo "" >> "$OUTPUT"
echo "所有 .txt 文件总行数: $total_lines" >> "$OUTPUT"
