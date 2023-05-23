from src.scfg.ast_node import ASTNode, CLAUSE_KEYWORDS
from src.scfg.cond import Cond

class From(ASTNode):
    def __init__(self):
        self.table_units = []

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, From):
            return False

        self_tables = []
        self_conds = []
        for u in self.table_units:
            if isinstance(u[0], Join):
                self_tables.append(u[0].table)
                self_conds.append(u[0].cond)
            else:
                self_tables.append(u[0])

        other_tables = []
        other_conds = []
        for u in other.table_units:
            if isinstance(u[0], Join):
                other_tables.append(u[0].table)
                other_conds.append(u[0].cond)
            else:
                other_tables.append(u[0])

        for t in self_tables:
            if t in other_tables:
                other_tables.remove(t)
            else:
                return False

        for c in self_conds:
            if c in other_conds:
                other_conds.remove(c)
            else:
                return False

        return (len(other_tables) == 0 and len(other_conds) == 0)

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'from', "'from' not found"
        idx += 1

        len_ = len(tokens)
        while idx < len_:
            isBlock = False
            if tokens[idx] == '(':
                isBlock = True
                idx += 1

            if tokens[idx] == 'select':
                import src.scfg.sql as sql
                new_table = sql.Sql()
                idx = new_table.parse_sql(tokens, idx)
                self.table_units.append((new_table, isBlock))
            else:
                if idx < len_ and tokens[idx] == 'join':
                    new_join = Join()
                    idx = new_join.parse_sql(tokens, idx)
                    self.table_units.append((new_join, isBlock))
                else:
                    self.table_units.append((tokens[idx], isBlock))
                    idx += 1

            if isBlock:
                assert tokens[idx] == ')'
                idx += 1
            
            if idx < len_ and (tokens[idx] in CLAUSE_KEYWORDS or tokens[idx] in (")", ";")):
                break

        return idx

    def parse_python(self, tokens, idx):
        assert tokens[idx] == '.select_from', "'.select_from' not found"
        idx += 1
        assert tokens[idx] == '('
        idx += 1

        len_ = len(tokens)
        while idx < len_ and tokens[idx] != ')':
            if tokens[idx] == 'select':
                import src.scfg.sql as sql
                new_table = sql.Sql()
                idx = new_table.parse_python(tokens, idx)
                self.table_units.append((new_table, True))
            else:
                if idx < len_ and tokens[idx] == '.join':
                    new_join = Join()
                    idx = new_join.parse_python(tokens, idx)
                    self.table_units.append((new_join, False))
                else:
                    self.table_units.append((tokens[idx], False))
                    idx += 1

        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        s = "from"
        for u, isBlock in self.table_units:
            u_str = ""
            if isinstance(u, str):
                u_str = u
            else:
                u_str = u.print_sql()

            if isBlock:
                u_str = "(" + u_str + ")"
            
            s += " " + u_str
        
        return s.replace(" , ", ", ")

    def print_sql_dict(self):
        import src.scfg.sql as sql
        s = "from"
        subqs = []
        for u, isBlock in self.table_units:
            u_str = ""
            if isinstance(u, str):
                u_str = u
            elif isinstance(u, sql.Sql):
                u_str = f"subquery{len(subqs)}"
                subqs.append(u.print_sql_dict())
            else:
                u_str = u.print_sql()

            if isBlock:
                u_str = "(" + u_str + ")"
            
            s += " " + u_str
        
        if len(subqs) > 0:
            clause = {"clause": s.replace(" , ", ", ")}
            for i in range(len(subqs)):
                clause[f"subquery{i}"] = subqs[i]
            return clause
        else:
            return s.replace(" , ", ", ")

    def print_python(self):
        s = "select_from("
        for u, isBlock in self.table_units:
            u_str = ""
            if isinstance(u, str):
                u_str = u
            else:
                u_str = u.print_python()
            
            s += u_str

        s += ")"
        
        return s.replace(",", ", ")


class Join(ASTNode):
    def __init__(self):
        self.table = None
        self.cond = None

    def __eq__(self, other):
        if other is self:
            return True
        if other is None:
            return False
        if not isinstance(other, Join):
            return False
        
        if self.table != other.table:
            return False
        if self.cond != other.cond:
            return False
        
        return True

    def parse_sql(self, tokens, idx):
        assert tokens[idx] == 'join', "'join' not found"
        idx += 1  # skip join

        self.table = tokens[idx]
        idx += 1

        len_ = len(tokens)
        if idx < len_ and tokens[idx] == "on":
            idx += 1  # skip on
            new_cond = Cond()
            idx = new_cond.parse_sql(tokens, idx)
            self.cond = new_cond

        return idx

    def parse_python(self, tokens, idx):
        assert tokens[idx] == '.join', "'.join' not found"
        idx += 1  # skip join
        assert tokens[idx] == '('
        idx += 1

        self.table = tokens[idx]
        idx += 1

        len_ = len(tokens)
        if idx < len_ and tokens[idx] == ",":
            idx += 1
            new_cond = Cond()
            idx = new_cond.parse_python(tokens, idx)
            self.cond = new_cond

        assert tokens[idx] == ')'
        idx += 1

        return idx

    def print_sql(self):
        s = "join " + self.table
        if self.cond is not None:
            s += " on " + self.cond.print_sql()
        return s

    def print_python(self):
        s = ".join(" + self.table
        if self.cond is not None:
            s += "," + self.cond.print_python()
        s += ")"
        return s