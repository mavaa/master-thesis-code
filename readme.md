# Code for master thesis "Using Large Language Models for Binary Decompilation"

Python code project for my master thesis which can be found here: [Using Large Language Models for Binary Decompilation](https://hdl.handle.net/11250/3168005)

## Setup

The following packages are needed:
```
radare2
python3
pip3
pkg-config # Required to install r2ghidra
```

TODO: Add more packages

In addition a .env file should be created with an OpenAI API key, looking like:
```
export OPENAI_API_KEY="key here"
```

Setting up and installing python requirements:
```
python -m venv .venv
source init_shell.sh
pip3 install -r requirements.txt
```

Sourcing `init_shell.sh` has to be done each time you start a new terminal.

For the tests:
```
pip3 install -r requirements_dev.txt
```

## Running

To see how to use the main.py program can be used to run the pipeline use `python main.py -h`:

```
usage: main.py [-h] [-d DATA_DIR] [-r RESULTS] [-m MODEL] [-s] [-o] {clean,prepare,print,evaluate}

Run pipeline commands.

positional arguments:
  {clean,prepare,print,evaluate}
                        Command to execute

options:
  -h, --help            show this help message and exit
  -d DATA_DIR, --data-dir DATA_DIR
                        Data directory
  -r RESULTS, --results RESULTS
                        Results filename
  -m MODEL, --model MODEL
                        Model name
  -s, --strip           Strip the binary during compilation
  -o, --objdump         Use objdump instead of r2 for disassembly
```

For the most simple use case, using the 4 sources in data/ (default directory), run `python main.py evaluate`

For decompile-eval tests, first run `python extract_decompile-eval.py` and then `python main.py -d data_decompile_eval evaluate`. The first scripts downloads and creates the separate source directory.

## Testing

Run `ptw -- --cov=src --cov-report=term-missing` to contiously test and produce coverage tests.
