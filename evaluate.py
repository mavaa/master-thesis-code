from codebleu import calc_codebleu

def read_code_from_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    return code

# Read reference and prediction from their respective files
reference_file_path = 'references.txt'
prediction_file_path = 'predictions.txt'

reference_code = read_code_from_file(reference_file_path)
prediction_code = read_code_from_file(prediction_file_path)

result = calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)
print(result)
