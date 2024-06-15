import re
import pyperclip
from colorama import init, Fore

# 输出预设
init()
success = Fore.GREEN + '[+]' + Fore.RESET
error = Fore.RED + '[x]' + Fore.RESET
warning = Fore.YELLOW + '[!]' + Fore.RESET
debug = Fore.YELLOW + '[!debug]' + Fore.RESET
done = Fore.CYAN + '[>]' + Fore.RESET
separator = '\n================================\n'


def convert_expression(expression: str) -> str:
    """转换表达式中的中文乘号、除号和幂运算符号，并处理小数点。"""
    expression = expression.replace('×', '*').replace('÷', '/').replace('^', '**').replace('{','(').replace('}',')').replace('[','(').replace(']',')').replace('〖','(').replace('〗',')')
    expression = re.sub(r'∜\((.*?)\)', r'(\1)**(1/4)', expression)
    expression = re.sub(r'√\((.*?)\)', r'(\1)**(1/2)', expression)
    expression = re.sub(r'(\d|\))(\()', r'\1*\2', expression)
    expression = re.sub(r'(\d)(\*\*\(1/2\))', r'\1*\2', expression)
    print(f'{debug} 转换结果：{expression}')
    return expression

def calculate_expression(expression: str) -> str:
    """计算转换后的数学表达式的结果。"""
    try:
        result = round(eval(convert_expression(expression)), 4) #四舍五入取小数点后n位数
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
