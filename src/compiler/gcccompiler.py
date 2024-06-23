class GCCCompiler:
    def __init__(self, subprocess, should_strip=False):
        self.subprocess = subprocess
        self.should_strip = should_strip

    def compile(self, source_path, output_path):
        self.subprocess.run(['gcc', '-c', '-o', output_path, source_path], check=True)

        if self.should_strip:
            self.subprocess.run(["strip", output_path], check=True)
