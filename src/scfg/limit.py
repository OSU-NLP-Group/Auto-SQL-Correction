from src.scfg.ast_node import ASTNode

class Limit(ASTNode):
    def __init__(self):
        self.lim_val = 0

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Limit):
            return False

        return self.lim_val == other.lim_val

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'limit', "'limit' not found"
        idx += 1
        self.lim_val = int(tokens[idx])
        idx += 1

        return idx

    def parse_python(self, tokens, idx):
        assert tokens[idx] == '.limit', "'.limit' not found"
        idx += 1
        assert tokens[idx] == '('
        idx += 1
        self.lim_val = int(tokens[idx])
        idx += 1
        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        return f"limit {self.lim_val}"

    def print_sql_dict(self):
        return self.print_sql()

    def print_python(self):
        return f"limit({self.lim_val})"