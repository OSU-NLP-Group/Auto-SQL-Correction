from src.scfg.ast_node import ASTNode
from src.scfg.cond import Cond

class Where(ASTNode):
    def __init__(self):
        self.cond = Cond()

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Where):
            return False

        if self.cond != other.cond:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'where', "'where' not found"
        idx += 1
        idx = self.cond.parse_sql(tokens, idx)
        return idx

    def parse_python(self, tokens, idx):
        assert tokens[idx] == '.where', "'.where' not found"
        idx += 1
        assert tokens[idx] == '('
        idx += 1
        idx = self.cond.parse_python(tokens, idx)
        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        return "where " + self.cond.print_sql()
    
    def print_sql_dict(self):
        subqs = []
        clause = "where " + self.cond.print_sql_dict(subqs)
        if len(subqs) > 0:
            c = {"clause": clause}
            for i in range(len(subqs)):
                c[f"subquery{i}"] = subqs[i]
            return c
        else:
            return clause

    def print_python(self):
        return "where({})".format(self.cond.print_python())