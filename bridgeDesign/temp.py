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
                expression = (expression[:start_index-1] + '(' + expression[start_index:i+1] + 
                              ')**(1/2)' + expression[i+1:])
                break
    return expression

# Example usage:
original_expression = '√((a+b)+c)'
converted_expression = convert_sqrt(original_expression)
print('Original:', original_expression)
print('Converted:', converted_expression)
