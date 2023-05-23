from src.scfg.ast_node import ASTNode, CLAUSE_KEYWORDS, JOIN_KEYWORDS, WHERE_OPS
from src.scfg.col_unit import ColUnit
from src.scfg.val_unit import ValUnit

OP_MAP = {'=': '==', '>': '>', '<': '<', '>=': '>=', '<=': '<=', '!=': '!='}
FUNC_MAP = {'between': 'between', 'in': 'in_', 'like': 'like', 'is': 'is_', 'exists': 'exists'}
OP_MAP_PY = {'==': '=', '>': '>', '<': '<', '>=': '>=', '<=': '<=', '!=': '!='}
FUNC_MAP_PY = {'.between': 'between', '.in_': 'in', '.like': 'like', '.is_': 'is', '.exists': 'exists'}

class Cond(ASTNode):
    def __init__(self):
        self.and_conds = []

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Cond):
            return False
        
        temp = []
        for u in self.and_conds:
            if u in other.and_conds:
                temp.append(other.and_conds.pop(other.and_conds.index(u)))
            else:
                return False

        if len(other.and_conds) == 0:
            other.and_conds = temp
            return True
        else:
            other.and_conds += temp
            return False

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)
        while idx < len_:
            new_and_cond = AndCond()
            idx = new_and_cond.parse_sql(tokens, idx)
            self.and_conds.append(new_and_cond)

            if idx < len_ and (tokens[idx] in CLAUSE_KEYWORDS or tokens[idx] in (")", ";") or tokens[idx] in JOIN_KEYWORDS):
                break

            if idx < len_:
                assert tokens[idx] == "or", "Error condition: idx: missing 'or' {}, tok: {}".format(idx, tokens[idx])
                idx += 1  # skip or

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)

        if tokens[idx] == "or_":
            idx += 1
            assert tokens[idx] == '('
            idx += 1

            while idx < len_ and tokens[idx] != ')':
                new_and_cond = AndCond()
                idx = new_and_cond.parse_python(tokens, idx)
                self.and_conds.append(new_and_cond)

                if tokens[idx] == ',':
                    idx += 1

            assert tokens[idx] == ')'
            idx += 1
        else:
            new_and_cond = AndCond()
            idx = new_and_cond.parse_python(tokens, idx)
            self.and_conds.append(new_and_cond)

        return idx

    def print_sql(self):
        return " or ".join([c.print_sql() for c in self.and_conds])

    def print_sql_dict(self, subqs=[]):
        return " or ".join([c.print_sql_dict(subqs) for c in self.and_conds])

    def print_python(self):
        if len(self.and_conds) == 1:
            return self.and_conds[0].print_python()
        else:
            s = "or_({})".format(
                ", ".join([c.print_python() for c in self.and_conds])
            )
            return s


class AndCond(ASTNode):
    def __init__(self):
        self.cond_units = []

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, AndCond):
            return False
        
        temp = []
        for u in self.cond_units:
            if u in other.cond_units:
                temp.append(other.cond_units.pop(other.cond_units.index(u)))
            else:
                return False

        if len(other.cond_units) == 0:
            other.cond_units = temp
            return True
        else:
            other.cond_units += temp
            return False

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)
        while idx < len_:
            new_cond = CondUnit()
            idx = new_cond.parse_sql(tokens, idx)
            self.cond_units.append(new_cond)

            if idx < len_ and (tokens[idx] == "or" or tokens[idx] in CLAUSE_KEYWORDS or tokens[idx] in (")", ";") or tokens[idx] in JOIN_KEYWORDS):
                break

            if idx < len_:
                assert tokens[idx] == "and", "Error condition: missing 'and' idx: {}, tok: {}".format(idx, tokens[idx])
                idx += 1  # skip and

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)

        if tokens[idx] == "and_":
            idx += 1
            assert tokens[idx] == '('
            idx += 1

            while idx < len_ and tokens[idx] != ')':
                new_cond = CondUnit()
                idx = new_cond.parse_python(tokens, idx)
                self.cond_units.append(new_cond)

                if tokens[idx] == ',':
                    idx += 1

            assert tokens[idx] == ')'
            idx += 1
        else:
            new_cond = CondUnit()
            idx = new_cond.parse_python(tokens, idx)
            self.cond_units.append(new_cond)

        return idx

    def print_sql(self):
        return " and ".join([c.print_sql() for c in self.cond_units])

    def print_sql_dict(self, subqs):
        return " and ".join([c.print_sql_dict(subqs) for c in self.cond_units])

    def print_python(self):
        if len(self.cond_units) == 1:
            return self.cond_units[0].print_python()
        else:
            s = "and_({})".format(
                ", ".join([c.print_python() for c in self.cond_units])
            )
            return s


class CondUnit(ASTNode):
    def __init__(self):
        self.not_op = False
        self.op = None
        self.val_unit = ValUnit()
        self.val1 = None
        self.val2 = None

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, CondUnit):
            return False
        
        if self.not_op != other.not_op:
            return False
        if self.op != other.op:
            return False

        if (
            self.op == "=" and 
            isinstance(self.val1.val, ColUnit) and
            isinstance(other.val1.val, ColUnit)
        ):
            if self.val_unit != other.val_unit:
                if (
                    self.val_unit.val_op is None and
                    self.val_unit.col_unit2 is None and
                    self.val_unit.col_unit1 == other.val1.val
                ):
                    if (
                        other.val_unit.val_op is None and
                        other.val_unit.col_unit2 is None and
                        self.val1.val != other.val_unit.col_unit1
                    ):
                        return False
                else:
                    return False
            elif self.val1 != other.val1:
                return False
        else:
            if self.val_unit != other.val_unit:
                return False
            if self.val1 != other.val1:
                return False
        
        if self.val2 != other.val2:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        len_ = len(tokens)

        idx = self.val_unit.parse_sql(tokens, idx)
        if tokens[idx] == 'not':
            self.not_op = True
            idx += 1

        assert idx < len_ and tokens[idx] in WHERE_OPS, "Error condition: incorrect operation idx: {}, tok: {}".format(idx, tokens[idx])
        self.op = tokens[idx]
        idx += 1

        self.val1 = Val()
        idx = self.val1.parse_sql(tokens, idx)
        if self.op == "between":  # between..and... special case: dual values
            assert tokens[idx] == 'and'
            idx += 1
            self.val2 = Val()
            idx = self.val2.parse_sql(tokens, idx)

        assert (tokens[idx] in ("and", "or") or tokens[idx] in CLAUSE_KEYWORDS or tokens[idx] in (")", ";") or tokens[idx] in JOIN_KEYWORDS) if idx < len_ else True, f"Error condition: unit not ending properly idx: {idx}, tok: {tokens[idx]}"

        return idx

    def parse_python(self, tokens, idx):
        len_ = len(tokens)

        if tokens[idx] == 'not_':
            self.not_op = True
            idx += 1
            assert tokens[idx] == '('
            idx += 1
        
        idx = self.val_unit.parse_python(tokens, idx)
        
        assert idx < len_ and (tokens[idx] in OP_MAP_PY or tokens[idx] in FUNC_MAP_PY), "Error condition: incorrect operation idx: {}, tok: {}".format(idx, tokens[idx])
        if tokens[idx] in OP_MAP_PY:
            self.op = OP_MAP_PY[tokens[idx]]
            idx += 1
        else:
            self.op = FUNC_MAP_PY[tokens[idx]]
            idx += 1
            assert tokens[idx] == '('
            idx += 1

        self.val1 = Val()
        idx = self.val1.parse_python(tokens, idx)
        if self.op == "between":  # between..and... special case: dual values
            assert tokens[idx] == ','
            idx += 1
            self.val2 = Val()
            idx = self.val2.parse_python(tokens, idx)

        if self.op in FUNC_MAP:
            assert tokens[idx] == ')'
            idx += 1

        if self.not_op:
            assert tokens[idx] == ')'
            idx += 1
        
        return idx

    def print_sql(self):
        s = self.val_unit.print_sql()
        if self.not_op:
            s += " not"
        s += " " + self.op
        s += " " + self.val1.print_sql()

        if self.op == "between":
            s += " and"
            s += " " + self.val2.print_sql()
        
        return s

    def print_sql_dict(self, subqs):
        s = self.val_unit.print_sql()
        if self.not_op:
            s += " not"
        s += " " + self.op
        s += " " + self.val1.print_sql_dict(subqs)

        if self.op == "between":
            s += " and"
            s += " " + self.val2.print_sql_dict(subqs)

        return s

    def print_python(self):
        s = self.val_unit.print_python() 

        if self.op in OP_MAP:
            s = s  + " " + OP_MAP[self.op] + " " + self.val1.print_python()
        else:
            if self.op == "between":
                s = s + ".between({}, {})".format(
                    self.val1.print_python(),
                    self.val2.print_python()
                )
            else:
                s = s + "." + FUNC_MAP[self.op] + "({})".format(self.val1.print_python())

        if self.not_op:
            s = "not_({})".format(s)
        
        return s


class Val(ASTNode):
    def __init__(self):
        self.is_block = False
        self.val = None

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Val):
            return False

        return self.val == other.val

    def parse_sql(self, tokens, idx):
        start_idx = idx
        len_ = len(tokens)

        if tokens[idx] == '(':
            self.is_block = True
            idx += 1

        if tokens[idx] == 'select':
            import src.scfg.sql as sql
            self.val = sql.Sql()
            idx= self.val.parse_sql(tokens, idx)
        elif "\"" in tokens[idx]:  # token is a string value
            self.val = tokens[idx]
            idx += 1
        else:
            try:
                self.val = float(tokens[idx])
                idx += 1
            except:
                end_idx = idx
                while end_idx < len_ and tokens[end_idx] != ',' and tokens[end_idx] != ')'\
                    and tokens[end_idx] != 'and' and tokens[end_idx] not in CLAUSE_KEYWORDS and tokens[end_idx] not in JOIN_KEYWORDS:
                        end_idx += 1

                self.val = ColUnit()
                idx = self.val.parse_sql(tokens[start_idx: end_idx], 0)
                idx = end_idx

        if self.is_block:
            assert tokens[idx] == ')'
            idx += 1

        return idx


    def parse_python(self, tokens, idx):
        start_idx = idx
        len_ = len(tokens)

        if tokens[idx] == 'select':
            import src.scfg.sql as sql
            self.val = sql.Sql()
            self.val.is_block = True
            idx= self.val.parse_python(tokens, idx)
        elif "\"" in tokens[idx]:  # token is a string value
            self.val = tokens[idx]
            idx += 1
        else:
            try:
                self.val = float(tokens[idx])
                idx += 1
            except:
                end_idx = idx
                while end_idx < len_ and tokens[end_idx] != ',' and tokens[end_idx] != ')':
                    end_idx += 1

                self.val = ColUnit()
                idx = self.val.parse_python(tokens[start_idx: end_idx], 0)
                idx = end_idx

        return idx

    def print_sql(self):
        s = ""
        if isinstance(self.val, str):
            s = self.val
        elif isinstance(self.val, float):
            if self.val.is_integer():
                s = str(int(self.val))
            else:
                s = str(self.val)
        else:
            s = self.val.print_sql()

        if self.is_block:
            s = "(" + s + ")"

        return s

    def print_sql_dict(self, subqs):
        import src.scfg.sql as sql
        s = ""
        if isinstance(self.val, str):
            s = self.val
        elif isinstance(self.val, float):
            if self.val.is_integer():
                s = str(int(self.val))
            else:
                s = str(self.val)
        elif isinstance(self.val, sql.Sql):
            s = f"subquery{len(subqs)}"
            subqs.append(self.val.print_sql_dict())
        else:
            s = self.val.print_sql()
        
        if self.is_block:
            s = "(" + s + ")"

        return s

    def print_python(self):
        s = ""
        if isinstance(self.val, str):
            s = self.val
        elif isinstance(self.val, float):
            if self.val.is_integer():
                s = str(int(self.val))
            else:
                s = str(self.val)
        else:
            s = self.val.print_python()

        return s