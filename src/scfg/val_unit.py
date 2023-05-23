from src.scfg.ast_node import ASTNode, UNIT_OPS
from src.scfg.col_unit import ColUnit

class ValUnit(ASTNode):
    def __init__(self):
        self.is_block = False
        self.val_op = None
        self.col_unit1 = ColUnit()
        self.col_unit2 = None

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, ValUnit):
            return False
        
        if self.val_op != other.val_op:
            return False
        if self.col_unit1 != other.col_unit1:
            return False
        if self.col_unit2 != other.col_unit2:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)
        if tokens[idx] == '(':
            self.is_block = True
            idx += 1

        idx = self.col_unit1.parse_sql(tokens, idx)
        if idx < len_ and tokens[idx] in UNIT_OPS:
            self.val_op = tokens[idx]
            idx += 1
            self.col_unit2 = ColUnit()
            idx = self.col_unit2.parse_sql(tokens, idx)

        if self.is_block:
            assert tokens[idx] == ')'
            idx += 1  # skip ')'

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)

        idx = self.col_unit1.parse_python(tokens, idx)
        if idx < len_ and tokens[idx] in UNIT_OPS:
            self.val_op = tokens[idx]
            idx += 1
            self.col_unit2 = ColUnit()
            idx = self.col_unit2.parse_python(tokens, idx)

        return idx

    def print_sql(self):
        s = self.col_unit1.print_sql()
        if self.val_op is not None:
            s += " " + self.val_op + " " + self.col_unit2.print_sql()

        if self.is_block:
            s = "(" + s + ")"

        return s

    def print_python(self):
        s = self.col_unit1.print_python()
        if self.val_op is not None:
            s += " " + self.val_op + " " + self.col_unit2.print_python()

        return s