import sys
import os

# 将 repo/sorts 目录加入模块搜索路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo', 'sorts'))

from bubble_sort import bubble_sort_iterative

# 测试数组
arr = [99, 22, 55, 11, 88, 33]
print(f"原始数组: {arr}")

# 使用修改后的降序冒泡排序
sorted_arr = bubble_sort_iterative(arr)
print(f"降序排序后: {sorted_arr}")

# 将结果写入 final_sort_result.txt
with open('final_sort_result.txt', 'w') as f:
    f.write(str(sorted_arr))

print("结果已写入 final_sort_result.txt")
