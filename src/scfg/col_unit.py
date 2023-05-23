from src.scfg.ast_node import ASTNode, AGG_OPS, AGG_OPS_PY

class ColUnit(ASTNode):
    def __init__(self):
        self.is_block = False
        self.is_distinct = False
        self.agg_func = None
        self.column = Column()

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, ColUnit):
            return False
        
        if self.is_distinct != other.is_distinct:
            return False
        if self.agg_func != other.agg_func:
            return False
        if self.column != other.column:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)

        if tokens[idx] == '(':
            self.is_block = True
            idx += 1

        if tokens[idx] in AGG_OPS:
            self.agg_func = tokens[idx]
            idx += 1
            assert idx < len_ and tokens[idx] == '('
            idx += 1
            if tokens[idx] == "distinct":
                idx += 1
                self.is_distinct = True
            idx = self.column.parse_sql(tokens, idx) 
            assert idx < len_ and tokens[idx] == ')'
            idx += 1
            return idx

        if tokens[idx] == "distinct":
            idx += 1
            self.is_distinct = True
        idx = self.column.parse_sql(tokens, idx)

        if self.is_block:
            assert tokens[idx] == ')'
            idx += 1  # skip ')'

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)

        if tokens[idx].lstrip() in AGG_OPS_PY:
            self.agg_func = AGG_OPS_PY[tokens[idx]]
            idx += 1
            assert idx < len_ and tokens[idx] == '('
            idx += 1
        
        idx = self.column.parse_python(tokens, idx)

        if idx < len_ and tokens[idx] == ".distinct":
            idx += 1
            self.is_distinct = True
            assert tokens[idx] == '('
            idx += 1
            assert tokens[idx] == ')'
            idx += 1

        if self.agg_func is not None:
            assert tokens[idx] == ')'
            idx += 1

        return idx

    def print_sql(self):
        s = self.column.print_sql()
        if self.is_distinct:
            s = "distinct " + s
        if self.agg_func is not None:
            s = self.agg_func + "(" + s + ")"
        if self.is_block:
            s = "(" + s + ")"

        return s

    def print_python(self):
        s = self.column.print_python()
        if self.is_distinct:
            s = s + ".distinct()"
        if self.agg_func is not None:
            s = "func." + self.agg_func + "(" + s + ")"

        return s


class Column(ASTNode):
    def __init__(self):
        self.table = None
        self.col = None

    def parse_sql(self, tokens, idx):
        tok = tokens[idx]
        if tok == "*":
            self.col = "*"
        elif '.' in tok:
            #assert '.' in tok, "SQL must be normalized first"
            tbl, col = tok.split('.')
            self.table = tbl
            self.col = col
        else:
            self.col = tok
        return idx + 1

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Column):
            return False
        
        if self.table != other.table:
            return False
        if self.col != other.col:
            return False
        
        return True

    def parse_python(self, tokens, idx):
        tok = tokens[idx]
        if tok == "\"*\"":
            self.col = "*"
        elif '.c.' in tok:
            #assert '.c.' in tok, "Python column error"
            tbl, col = tok.split('.c.')
            self.table = tbl
            self.col = col
        else:
            self.col = tok
        return idx + 1

    def print_sql(self):
        if self.col == "*":
            return "*"
        elif self.table:
            return self.table + "." + self.col
        else:
            return self.col

    def print_python(self):
        if self.col == "*":
            return "\"*\""
        elif self.table:
            return self.table + ".c." + self.col
        else:
            return self.col