import os
from src.util import create_folder_if_not_exists

base_dir = "data_decompile_eval/disassemblies"
prompt_folder = os.path.join('data_decompile_eval', 'llm4decompileprompts')
create_folder_if_not_exists(prompt_folder)

for output_file in sorted(os.listdir(base_dir)):
    prompt_filename = os.path.join(prompt_folder, f"{output_file}_prompt.txt")
    input_asm = ''
    file_path = os.path.join(base_dir, output_file)
    print(f"reading {file_path}")
    with open(file_path) as f:#asm file
        asm= f.read()
        if '<'+'.text'+'>:' not in asm: #IMPORTANT replace func0 with the function name
            raise ValueError("compile fails")
        asm = '<'+'.text'+'>:' + asm.split('<'+'.text'+'>:')[-1].split('\n\n')[0] #IMPORTANT replace func0 with the function name
        asm_clean = ""
        asm_sp = asm.split("\n")
        for tmp in asm_sp:
            if len(tmp.split("\t"))<3 and '00' in tmp:
                continue
            idx = min(
                len(tmp.split("\t")) - 1, 2
            )
            tmp_asm = "\t".join(tmp.split("\t")[idx:])  # remove the binary code
            tmp_asm = tmp_asm.split("#")[0].strip()  # remove the comments
            asm_clean += tmp_asm + "\n"
    input_asm = asm_clean.strip()
    before = f"# This is the assembly code:\n"#prompt
    after = "\n# What is the source code?\n"#prompt
    input_asm_prompt = before+input_asm.strip()+after
    with open(prompt_filename +'_' + '.asm','w',encoding='utf-8') as f:
        f.write(input_asm_prompt)
