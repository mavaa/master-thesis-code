from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

if __name__ == '__main__':
    model_path = 'LLM4Binary/llm4decompile-6.7b-v1.5' # V1.5 Model
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path,torch_dtype=torch.bfloat16).cuda()

    with open("data_decompile_eval/llm4decompileprompts/task_000_d.txt_prompt.txt_.asm",'r') as f:#optimization level O0
        asm_func = f.read()
    inputs = tokenizer(asm_func, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=2048)### max length to 4096, max new tokens should be below the range
    c_func_decompile = tokenizer.decode(outputs[0][len(inputs[0]):-1])

    with open(fileName +'.c','r') as f:#original file
        func = f.read()

    print(f'original function:\n{func}')# Note we only decompile one function, where the original file may contain multiple functions
    print(f'decompiled function:\n{c_func_decompile}')
