class CodeBleuEvaluator:
    def __init__(self, calc_codebleu, lang="c", weights=(0.25, 0.25, 0.25, 0.25), tokenizer=None):
        self.calc_codebleu = calc_codebleu
        self.lang = lang
        self.weights = weights
        self.tokenizer = tokenizer

    def evaluate(self, reference_code, prediction_code):
        return self.calc_codebleu([reference_code], \
                           [prediction_code], \
                           lang=self.lang, \
                           weights=self.weights, \
                           tokenizer=self.tokenizer)
