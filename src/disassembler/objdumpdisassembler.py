class ObjdumpDisassembler:
    def __init__(self, subprocess):
        self.subprocess = subprocess

    def disassemble(self, executable_path, output_path):
        self.subprocess.run(["objdump", "-d", executable_path],
                       stdout=open(output_path, 'w'), check=True)
