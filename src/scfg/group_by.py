from src.scfg.ast_node import ASTNode, CLAUSE_KEYWORDS
from src.scfg.col_unit import ColUnit

class GroupBy(ASTNode):
    def __init__(self):
        self.col_units = []

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, GroupBy):
            return False
        
        temp = []
        for u in self.col_units:
            if u in other.col_units:
                temp.append(other.col_units.pop(other.col_units.index(u)))
            else:
                return False

        if len(other.col_units) == 0:
            other.col_units = temp
            return True
        else:
            other.col_units += temp
            return False

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'group', "'group' not found"
        idx += 1
        assert tokens[idx] == 'by', "'group by' not found"
        idx += 1

        len_ = len(tokens)
        while idx < len_ and not (tokens[idx] in CLAUSE_KEYWORDS or tokens[idx] in (")", ";")):
            new_col = ColUnit()
            idx = new_col.parse_sql(tokens, idx)
            self.col_units.append(new_col)
            if idx < len_ and tokens[idx] == ',':
                idx += 1  # skip ','
            else:
                break

        return idx

    def parse_python(self, tokens, idx):
        assert tokens[idx] == '.group_by', "'.group_by' not found"
        idx += 1
        assert tokens[idx] == '('
        idx += 1
        len_ = len(tokens)
        while idx < len_ and tokens[idx] != ")":
            new_col = ColUnit()
            idx = new_col.parse_python(tokens, idx)
            self.col_units.append(new_col)
            
            if idx < len_ and tokens[idx] == ',':
                idx += 1  # skip ','

        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        return "group by " + ", ".join([u.print_sql() for u in self.col_units])

    def print_sql_dict(self):
        return self.print_sql()

    def print_python(self):
        return "group_by({})".format(", ".join([u.print_python() for u in self.col_units]))