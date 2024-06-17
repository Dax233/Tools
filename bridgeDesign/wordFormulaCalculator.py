# -*- coding: utf-8 -*-
## wordFormulaCalculator
### github.com/Dax233/Tools
#### MICENCE: AGPL
##### By: BakaDax
##### 更新于2024/06/16

import re
import pyperclip
import numpy as np
from colorama import init, Fore


# 输出预设
init()
success = Fore.GREEN + '[+]' + Fore.RESET
error = Fore.RED + '[x]' + Fore.RESET
warning = Fore.YELLOW + '[!]' + Fore.RESET
debug = Fore.YELLOW + '[!debug]' + Fore.RESET
done = Fore.CYAN + '[>]' + Fore.RESET
separator = '\n================================\n'

def trigonometric_functions(expression):
    while '\"sin\"' in expression:
        start_index = expression.find('\"sin\" ') + 6
        for i in range(start_index,len(expression)):
            if expression[i] == '∘' and expression[i-2:i] == '**' :
                print(np.sin(int(expression[start_index:i-2])*np.pi/180))
                expression = (expression[:start_index-6] + str(np.sin(int(expression[start_index:i-2])*np.pi/180)) + expression[i+1:])
                break
    while '\"cos\"' in expression:
        start_index = expression.find('\"cos\" ') + 6
        for i in range(start_index,len(expression)):
            if expression[i] == '∘' and expression[i-2:i] == '**' :
                print(np.sin(int(expression[start_index:i-2])*np.pi/180))
                expression = (expression[:start_index-6] + str(np.cos(int(expression[start_index:i-2])*np.pi/180)) + expression[i+1:])
                break
    while '\"tan\"' in expression:
        start_index = expression.find('\"tan\" ') + 6
        for i in range(start_index,len(expression)):
            if expression[i] == '∘' and expression[i-2:i] == '**' :
                print(np.sin(int(expression[start_index:i-2])*np.pi/180))
                expression = (expression[:start_index-6] + str(np.tan(int(expression[start_index:i-2])*np.pi/180)) + expression[i+1:])
                break
    return expression

def convert_sqrt(expression):
    while '√' in expression:
        start_index = expression.find('√') + 1
        # Initialize the parentheses counter
        parentheses_count = 0
        for i in range(start_index, len(expression)):
            if expression[i] == '(':
                parentheses_count += 1
            elif expression[i] == ')':
                parentheses_count -= 1
            # When the counter is zero, we found the matching closing parenthesis
            if parentheses_count == 0:
                # Insert the power of (1/2) at the right position
                expression = (expression[:start_index-1] + '(' + expression[start_index:i+1] + ')**(1/2)' + expression[i+1:])
                break
    return expression

def convert_sqrt_4(expression):
    while '√' in expression:
        start_index = expression.find('∜') + 1
        # Initialize the parentheses counter
        parentheses_count = 0
        for i in range(start_index, len(expression)):
            if expression[i] == '(':
                parentheses_count += 1
            elif expression[i] == ')':
                parentheses_count -= 1
            # When the counter is zero, we found the matching closing parenthesis
            if parentheses_count == 0:
                # Insert the power of (1/4) at the right position
                expression = (expression[:start_index-1] + '(' + expression[start_index:i+1] + 
                              ')**(1/4)' + expression[i+1:])
                break
    return expression


def convert_expression(expression: str) -> str:
    """转换表达式中的中文乘号、除号和幂运算符号，并处理小数点。"""
    expression = expression.replace('×', '*').replace('÷', '/').replace('^', '**').replace('{','(').replace('}',')').replace('[','(').replace(']',')').replace('〖','(').replace('〗',')').replace(' ','').replace('\/', '/').replace('%', '*0.01')
    """转换万恶的根号符号"""
    expression = convert_sqrt(expression)
    expression = convert_sqrt_4(expression)
    """算三角函数"""
    expression = trigonometric_functions(expression)
    # expression = re.sub(r'∜\((.*?)\)', r'(\1)**(1/4)', expression)
    # expression = re.sub(r'√\((.*?)\)', r'(\1)**(1/2)', expression)
    expression = re.sub(r'(\d|\))(\()', r'\1*\2', expression)
    expression = re.sub(r'(\d)(\*\*\(1/2\))', r'\1*\2', expression)
    # print(f'{debug} 转换结果：{expression}')
    return expression

def calculate_expression(expression: str) -> str:
    """计算转换后的数学表达式的结果。"""
    try:
        result = round(eval(convert_expression(expression)), 4) # round it!
        pyperclip.copy(result)
        return f"{success} 计算结果为：{result}\n{success} 输入\"stop\"终止程序\n{separator}"
    except Exception as e:
        return f"{error} 表达式有误: {e}"

def main(isRunning):
    """主函数，获取用户输入并计算表达式结果。"""
    print("\n")
    user_input = input(f"{done} 请输入您的算式：")
    if user_input != 'stop' :
        result = calculate_expression(user_input) 
    else :
        result = f'{success} 程序成功退出！'
        isRunning = 0
    print(result)
    return isRunning

if __name__ == "__main__":
    isRunning = 1
    while isRunning == 1:
        isRunning = main(isRunning)
