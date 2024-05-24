import os
from codebleu import calc_codebleu

def read_code_from_file(file_path):
    with open(file_path, 'r') as file:
        code = file.read()
    return code

if __name__ == '__main__':
    base_path="data_codebleu_examples"
    reference_file=os.path.join(base_path, "reference.txt")

    reference_code = read_code_from_file(reference_file)

    for i in range(4):
        filename=f'src{i+1}.txt'
        prediction_code = read_code_from_file(os.path.join(base_path, filename))
        bleu = calc_codebleu([reference_code], [prediction_code], lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None)


        print(f"Results for {filename}:")
        for key, value in bleu.items():
            print(f"{key}: {value:.2%}")
