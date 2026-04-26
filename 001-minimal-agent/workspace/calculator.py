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
