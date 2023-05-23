from src.scfg.ast_node import ASTNode
from src.scfg.select_clause import Select
from src.scfg.from_clause import From
from src.scfg.where import Where
from src.scfg.group_by import GroupBy
from src.scfg.having import Having
from src.scfg.order_by import OrderBy
from src.scfg.limit import Limit

def skip_semicolon(toks, start_idx):
    idx = start_idx
    while idx < len(toks) and toks[idx] == ";":
        idx += 1
    return idx


class Sql(ASTNode):
    def __init__(self):
        self.is_block = False
        self.select = Select()
        self.from_clause = From()
        self.where = None
        self.group_by = None
        self.having = None
        self.order_by = None
        self.limit = None
        self.intersect = None
        self.union = None
        self.except_clause = None

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Sql):
            return False
        
        if self.select != other.select or self.from_clause != other.from_clause:
            return False
        if self.where != other.where:
            return False
        if self.group_by != other.group_by:
            return False
        if self.having != other.having:
            return False
        if self.order_by != other.order_by:
            return False
        if self.limit != other.limit:
            return False
        if self.intersect != other.intersect:
            return False
        if self.union != other.union:
            return False
        if self.except_clause != other.except_clause:
            return False
        return True

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)

        if tokens[idx] == '(':
            self.is_block = True
            idx += 1

        idx = self.select.parse_sql(tokens, idx)
        idx = self.from_clause.parse_sql(tokens, idx)

        if idx < len_ and tokens[idx] == 'where':
            self.where = Where()
            idx = self.where.parse_sql(tokens, idx)

        if idx < len_ and tokens[idx] == 'group' and tokens[idx+1] == 'by':
            self.group_by = GroupBy()
            idx = self.group_by.parse_sql(tokens, idx)

        if idx < len_ and tokens[idx] == 'having':
            self.having = Having()
            idx = self.having.parse_sql(tokens, idx)

        if idx < len_ and tokens[idx] == 'order' and tokens[idx+1] == 'by':
            self.order_by = OrderBy()
            idx = self.order_by.parse_sql(tokens, idx)

        if idx < len_ and tokens[idx] == 'limit':
            self.limit = Limit()
            idx = self.limit.parse_sql(tokens, idx)

        idx = skip_semicolon(tokens, idx)
        if self.is_block:
            assert tokens[idx] == ')'
            idx += 1  # skip ')'
        idx = skip_semicolon(tokens, idx)

        # Spider assumption: only one IEU
        ieu = ['intersect', 'except', 'union']
        while idx < len_ and tokens[idx] in ieu:
            kwd = tokens[idx]
            ieu.remove(kwd)
            idx += 1
            if kwd == "intersect":
                self.intersect = Sql()
                idx = self.intersect.parse_sql(tokens, idx)
            elif kwd == "union":
                self.union = Sql()
                idx = self.union.parse_sql(tokens, idx) 
            else:
                self.except_clause = Sql()
                idx = self.except_clause.parse_sql(tokens, idx)

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)

        idx = self.select.parse_python(tokens, idx)
        idx = self.from_clause.parse_python(tokens, idx)

        if idx < len_ and tokens[idx] == '.where':
            self.where = Where()
            idx = self.where.parse_python(tokens, idx)

        if idx < len_ and tokens[idx] == '.group_by':
            self.group_by = GroupBy()
            idx = self.group_by.parse_python(tokens, idx)

        if idx < len_ and tokens[idx] == '.having':
            self.having = Having()
            idx = self.having.parse_python(tokens, idx)

        if idx < len_ and tokens[idx] == '.order_by':
            self.order_by = OrderBy()
            idx = self.order_by.parse_python(tokens, idx)

        if idx < len_ and tokens[idx] == '.limit':
            self.limit = Limit()
            idx = self.limit.parse_python(tokens, idx)

        # Spider assumption: only one IEU
        ieu = ['intersect', 'except', 'union']
        while idx < len_ and tokens[idx].lstrip(".").rstrip("_") in ieu:
            kwd = tokens[idx].lstrip(".").rstrip("_")
            ieu.remove(kwd)
            idx += 1
            assert tokens[idx] == '('
            idx += 1
            if kwd == "intersect":
                self.intersect = Sql()
                idx = self.intersect.parse_python(tokens, idx)
            elif kwd == "union":
                self.union = Sql()
                idx = self.union.parse_python(tokens, idx) 
            else:
                self.except_clause = Sql()
                idx = self.except_clause.parse_python(tokens, idx)
            assert tokens[idx] == ')', f"{tokens[idx]}, {idx}"
            idx += 1

        return idx

    def print_sql(self):
        s = self.select.print_sql() + " " + self.from_clause.print_sql()

        if self.where is not None:
            s += " " + self.where.print_sql()
        if self.group_by is not None:
            s += " " + self.group_by.print_sql()
        if self.having is not None:
            s += " " + self.having.print_sql()
        if self.order_by is not None:
            s += " " + self.order_by.print_sql()
        if self.limit is not None:
            s += " " + self.limit.print_sql()
        if self.intersect is not None:
            s += " intersect " + self.intersect.print_sql()
        if self.union is not None:
            s += " union " + self.union.print_sql()
        if self.except_clause is not None:
            s += " except " + self.except_clause.print_sql()

        if self.is_block:
            s = "(" + s + ")"

        return s

    def print_sql_dict(self):
        s = {
            "select": self.select.print_sql_dict(),
            "from": self.from_clause.print_sql_dict()
        }
        # s = {"from": self.from_clause.print_sql_dict()}

        if self.where is not None:
            s["where"] = self.where.print_sql_dict()
        if self.group_by is not None:
            s["groupBy"] = self.group_by.print_sql_dict()
        if self.having is not None:
            s["having"] = self.having.print_sql_dict()
        
        # s["select"] = self.select.print_sql_dict()
        
        if self.order_by is not None:
            s["orderBy"] = self.order_by.print_sql_dict()
        if self.limit is not None:
            s["limit"] = self.limit.print_sql_dict()
        
        if self.intersect is not None:
            s["intersect"] = {
                "clause": "intersect subquery0",
                "subquery0": self.intersect.print_sql_dict()
            }
        if self.union is not None:
            s["union"] = {
                "clause": "union subquery0",
                "subquery0": self.union.print_sql_dict()
            }
        if self.except_clause is not None:
            s["except"] = {
                "clause": "except subquery0",
                "subquery0": self.except_clause.print_sql_dict()
            }

        return s

    def print_python(self):
        s = self.select.print_python() + "." + self.from_clause.print_python()

        if self.where is not None:
            s += "." + self.where.print_python()
        if self.group_by is not None:
            s += "." + self.group_by.print_python()
        if self.having is not None:
            s += "." + self.having.print_python()
        if self.order_by is not None:
            s += "." + self.order_by.print_python()
        if self.limit is not None:
            s += "." + self.limit.print_python()

        if self.intersect is not None:
            s += ".intersect({})".format(self.intersect.print_python())
        if self.union is not None:
            s += ".union({})".format(self.union.print_python())
        if self.except_clause is not None:
            s += ".except_({})".format(self.except_clause.print_python())

        return s