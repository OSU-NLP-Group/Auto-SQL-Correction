from src.scfg.select_clause import Select
from src.scfg.from_clause import From
from src.scfg.where import Where
from src.scfg.group_by import GroupBy
from src.scfg.having import Having
from src.scfg.order_by import OrderBy
from src.scfg.limit import Limit
from src.utils.spider_eval.process_sql import tokenize

import re

def choose(choices, gold_program):
    for i, program in enumerate(choices):
        if re.match(r".*\.pop\(\"(.*)\"\)", program):
            if program in gold_program:
                return i
        else:
            parts = program.split(" = ")
            part1 = parts[0]
            part2 = " = ".join(parts[1:]).rstrip()

            if part2.startswith('"') and part2.endswith('"'):
                clause = part2[1:-1]
                for gp in gold_program:
                    if not re.match(r".*\.pop\(\"(.*)\"\)", gp):
                        gparts = gp.split(" = ")
                        gpart1 = gparts[0]
                        gpart2 = " = ".join(gparts[1:]).rstrip()
                        gclause = gpart2[1:-1]

                        try:
                            if part1 == gpart1 and clause_match(clause, gclause):
                                return i
                        except:
                            print(clause)
                            print(gclause)
                            continue
            else:
                for gp in gold_program:
                    if program == gp:
                        return i

    return -1

def clause_match(c1, c2):
    c1 = tokenize(c1)
    c2 = tokenize(c2)

    if c1[0] != c2[0]:
        return False

    if c1[0] == "select":
        t1 = Select()
        t2 = Select()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    elif c1[0] == "from":
        t1 = From()
        t2 = From()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    elif c1[0] == "where":
        t1 = Where()
        t2 = Where()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    elif c1[0] == "group":
        t1 = GroupBy()
        t2 = GroupBy()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    elif c1[0] == "having":
        t1 = Having()
        t2 = Having()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    elif c1[0] == "order":
        t1 = OrderBy()
        t2 = OrderBy()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    elif c1[0] == "limit":
        t1 = Limit()
        t2 = Limit()
        _ = t1.parse_sql(c1, 0)
        _ = t2.parse_sql(c2, 0)
        return t1 == t2
    else:
        return False
