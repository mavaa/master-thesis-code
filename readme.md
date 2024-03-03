# Initial process

## Compiling and creating disassembly

main.c contains some simple code, with a Makefile to build it. Then I create a disassembly using:

```
make
radare2 -qc "pd @ main" main > disassembly.txt
```

NOTE: To output the disassembly, you HAVE to do `$ echo 'e scr.color=1' >> ~/.radare2rc` to disable color output!

## Dataset creation

The source code will be the reference data. To use it whith CodeBLEU it needs to be put on a single line so that
```
#include <stdio.h>

int main() {
    printf("Hello, World!\n");
    return 0;
}
```
becomes
```
#include <stdio.h> int main() { printf("Hello, World!\n"); return 0; }
```
This file should be called references.txt

## Prediction

The disassembly should be fed into a LLM with a fitting prompt to make it reconstruct the original source code. The code reconstructed by the LLM should be put in a file `predictions.txt`, on a single line in the same way as the reference.


Then something along of the following code can be used to run evaluation:
```
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
```

A requirement.txt file for python requirements should also be produced.
