from src.scfg.ast_node import ASTNode, CLAUSE_KEYWORDS, ORDER_OPS
from src.scfg.val_unit import ValUnit

class OrderBy(ASTNode):
    def __init__(self):
        self.order_units = []

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, OrderBy):
            return False
        
        temp = []
        for u in self.order_units:
            if u in other.order_units:
                temp.append(other.order_units.pop(other.order_units.index(u)))
            else:
                return False

        if len(other.order_units) == 0:
            other.order_units = temp
            return True
        else:
            other.order_units += temp
            return False

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'order', "'order' not found"
        idx += 1
        assert tokens[idx] == 'by', "'order by' not found"
        idx += 1

        len_ = len(tokens)
        while idx < len_ and not (tokens[idx] in CLAUSE_KEYWORDS or tokens[idx] in (")", ";")):
            new_unit = OrderUnit()
            idx = new_unit.parse_sql(tokens, idx)
            self.order_units.append(new_unit)
            
            if idx < len_ and tokens[idx] == ',':
                idx += 1  # skip ','
            else:
                break

        return idx

    def parse_python(self, tokens, idx):
        assert tokens[idx] == '.order_by', "'.order_by' not found"
        idx += 1
        assert tokens[idx] == '('
        idx += 1
        len_ = len(tokens)
        while idx < len_ and tokens[idx] != ")":
            new_unit = OrderUnit()
            idx = new_unit.parse_python(tokens, idx)
            self.order_units.append(new_unit)
            
            if idx < len_ and tokens[idx] == ',':
                idx += 1  # skip ','

        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        return "order by " + ", ".join([u.print_sql() for u in self.order_units])

    def print_sql_dict(self):
        return self.print_sql()

    def print_python(self):
        return "order_by({})".format(", ".join([u.print_python() for u in self.order_units]))


class OrderUnit(ASTNode):
    def __init__(self):
        self.is_asc = True
        self.val_unit = ValUnit()

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, OrderUnit):
            return False
        
        if self.is_asc != other.is_asc:
            return False
        if self.val_unit != other.val_unit:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)
        idx = self.val_unit.parse_sql(tokens, idx)
            
        if idx < len_ and tokens[idx] in ORDER_OPS:
            if tokens[idx] == "desc":
                self.is_asc = False
            idx += 1

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)
        idx = self.val_unit.parse_python(tokens, idx)

        assert idx < len_ and tokens[idx].lstrip(".") in ORDER_OPS, f"{tokens[idx]}"
        if tokens[idx] == ".desc":
            self.is_asc = False
        else:
            assert tokens[idx] == ".asc"
        idx += 1

        assert tokens[idx] == '('
        idx += 1
        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        return self.val_unit.print_sql() + (" asc" if self.is_asc else " desc")

    def print_python(self):
        return self.val_unit.print_python() + (".asc()" if self.is_asc else ".desc()")