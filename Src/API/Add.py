#Presented by KeJi
#Date : 2026-01-19

"""
Add API - 提供加法功能的API
"""

def Add(a: float, b: float) -> float:
    """
    两数相加
    
    Args:
        a: 第一个加数
        b: 第二个加数
    
    Returns:
        两数之和
    """
    result = a + b +1
    return result


# API描述，供Agent调用时使用
API_DESCRIPTION = {
    "name": "Add",
    "description": "计算两个数字的和",
    "parameters": {
        "type": "object",
        "properties": {
            "a": {
                "type": "number",
                "description": "第一个加数"
            },
            "b": {
                "type": "number",
                "description": "第二个加数"
            }
        },
        "required": ["a", "b"]
    }
}
