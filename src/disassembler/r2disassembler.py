class R2Disassembler:
    def __init__(self, r2_runner):
        self.r2_runner = r2_runner

    def disassemble(self, executable_path, output_path):
        self.r2_runner.run('pd', executable_path, output_path)
