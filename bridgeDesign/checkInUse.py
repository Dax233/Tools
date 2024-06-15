import os
import errno

def is_file_in_use(file_path):
    try:
        # 尝试以独占模式打开文件
        with os.open(file_path, os.O_WRONLY | os.O_EXCL) as f:
            pass
        return False
    except OSError as e:
        # 如果是因为文件被占用而无法打开，则返回True
        return e.errno == errno.EACCES

# 使用示例
file_path = 'C:\\Users\\13218\\AppData\\Local\\Temp\\tmp4at8p0rx'
if is_file_in_use(file_path):
    print("文件被占用")
else:
    print("文件未被占用")
