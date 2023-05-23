from src.scfg.ast_node import ASTNode, CLAUSE_KEYWORDS, AGG_OPS, AGG_OPS_PY
from src.scfg.val_unit import ValUnit

class Select(ASTNode):
    def __init__(self):
        self.is_distinct = False
        self.select_units = []

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Select):
            return False

        if self.is_distinct != other.is_distinct:
            return False
        
        temp = []
        for u in self.select_units:
            if u in other.select_units:
                temp.append(other.select_units.pop(other.select_units.index(u)))
            else:
                return False

        if len(other.select_units) == 0:
            other.select_units = temp
            return True
        else:
            other.select_units += temp
            return False

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'select', "'select' not found"

        len_ = len(tokens)
        idx += 1

        if idx < len_ and tokens[idx] == 'distinct':
            idx += 1
            self.is_distinct = True

        while idx < len_ and tokens[idx] not in CLAUSE_KEYWORDS:
            new_select_unit = SelectUnit()
            idx = new_select_unit.parse_sql(tokens, idx)
            self.select_units.append(new_select_unit)

            if idx < len_ and tokens[idx] == ',':
                idx += 1  # skip ','

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)
        assert tokens[idx] == 'select', "'select' not found"
        idx += 1
        assert tokens[idx] == '('
        idx += 1

        while idx < len_ and tokens[idx] != ')':
            new_select_unit = SelectUnit()
            idx = new_select_unit.parse_python(tokens, idx)
            self.select_units.append(new_select_unit)

            if idx < len_ and tokens[idx] == ',':
                idx += 1  # skip ','

        assert tokens[idx] == ')'
        idx += 1

        if idx < len_ and tokens[idx] == '.distinct':
            idx += 1
            self.is_distinct = True
            assert tokens[idx] == '('
            idx += 1
            assert tokens[idx] == ')'
            idx += 1

        return idx

    def print_sql(self):
        s = "select " + ("distinct " if self.is_distinct else "") + ", ".join([u.print_sql() for u in self.select_units])
        return s

    def print_sql_dict(self):
        return self.print_sql()

    def print_python(self):
        s = "select(" + ", ".join([u.print_python() for u in self.select_units]) + ")" + (".distinct()" if self.is_distinct else "")
        return s


class SelectUnit(ASTNode):
    def __init__(self):
        self.agg_func = None
        self.val_unit = ValUnit()

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, SelectUnit):
            return False
        
        if self.agg_func != other.agg_func:
            return False
        if self.val_unit != other.val_unit:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        if tokens[idx] in AGG_OPS:
            self.agg_func = tokens[idx]
            idx += 1
        
        idx = self.val_unit.parse_sql(tokens, idx)
        return idx

    def parse_python(self, tokens, idx):
        if tokens[idx] in AGG_OPS_PY:
            self.agg_func = AGG_OPS_PY[tokens[idx]]
            idx += 1
            self.val_unit.is_block = True
            assert tokens[idx] == '('
            idx += 1
        
        idx = self.val_unit.parse_python(tokens, idx)

        if self.agg_func is not None:
            assert tokens[idx] == ')'
            idx += 1
        return idx

    def print_sql(self):
        s = self.val_unit.print_sql()
        if self.agg_func is not None:
            s = self.agg_func + s 

        return s

    def print_python(self):
        s = self.val_unit.print_python()
        if self.agg_func is not None:
            s = "func." + self.agg_func + "(" + s + ")"

        return s