from torch import nn
from transformers import RobertaTokenizer, T5ForConditionalGeneration

codit_t5 = [
    "<REPLACE_OLD>",
    "<REPLACE_NEW>", 
    "<REPLACE_END>",
    "<INSERT>",
    "<INSERT_END>",
    "<DELETE>",
    "<DELETE_END>"
]

class CodeT5:
    def __init__(self, checkpoint=None, edit_type=None):
        self.max_length = 550
        self.tokenizer = RobertaTokenizer.from_pretrained(checkpoint)
        self.model = T5ForConditionalGeneration.from_pretrained(checkpoint)

        if checkpoint.startswith("Salesforce") and edit_type != "program":
            self.tokenizer.add_tokens(codit_t5)
            self.model.resize_token_embeddings(len(self.tokenizer))