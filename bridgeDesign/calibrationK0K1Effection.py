import re
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
    """转换校验K0与K1值计算公式"""
    expression = re.sub(r'\s', r' ', expression)
    numberGroup = expression.split(' ')
    expression = '(' + numberGroup[0]+ '+' + numberGroup[8] + ')/2'
    i = 1 
    while i < 8 :
        expression = expression + '+' + numberGroup[i]
        i = i + 1
    print(f'{debug} 转换结果：{expression}')
    return expression

def calculate_expression(expression: str) -> str:
    """计算转换后的数学表达式的结果。"""
    try:
        result = round(eval(convert_expression(expression)), 4) #四舍五入取小数点后n位数
        return f"{success} 计算结果为：{result}\n"
    except Exception as e:
        return f"{error} 表达式有误: {e}"

def main(isRunning):
    """主函数，获取用户输入并计算表达式结果。"""
    print("\n")
    user_input = input(f"{done} 请输入您的输入文件路径：")
    if user_input != 'stop' :
        with open(user_input,'r') as read_file:
            content = read_file.readlines()
            result = ''
            for i in range(len(content)):
                result = result + calculate_expression(content[i])
            result = result + f'{success} 输入\"stop\"终止程序\n{separator}'
    else :
        result = f'{success} 程序成功退出！'
        isRunning = 0
    print(result)
    return isRunning

if __name__ == "__main__":
    isRunning = 1
    while isRunning == 1:
        isRunning = main(isRunning)
