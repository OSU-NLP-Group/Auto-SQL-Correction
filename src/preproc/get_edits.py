from src.preproc.utils import empty_clause, empty_sql_label, SQL_DICT_KEYS
from src.utils.spider_eval.process_sql import get_sql


def rebuild_sql(sql_dict):
    s = ""
    for k in SQL_DICT_KEYS:
        if k in sql_dict:
            if (
                k in ["from", "where", "having", "intersect", "union", "except"] and
                isinstance(sql_dict[k], dict)
            ):
                c = sql_dict[k]["clause"]
                for i in range(len(sql_dict[k]) - 1):
                    subq = f"subquery{i}"
                    subq_str = rebuild_sql(sql_dict[k][subq])
                    c = c.replace(subq, subq_str)
                s += c + " "
            else:
                s += sql_dict[k] + " "

    return s.rstrip()


def get_edits(sql_clauses, gold_sql_clauses, sql_label, gold_sql_label, schema):
    actions = []
    for k in SQL_DICT_KEYS:
        if sql_label[k] != gold_sql_label[k]:
            if k == 'limit':
                if sql_label[k] is None or sql_label[k] == 0:
                    actions.append(['insert', k, gold_sql_clauses[k]])
                elif gold_sql_label[k] is None or gold_sql_label[k] == 0:
                    actions.append(['delete', k])
                else:
                    actions.append(['replace', k, gold_sql_clauses[k]])
            
            elif k in ["intersect", "union", "except"]:
                if sql_label[k] is None or len(sql_label[k]) == 0:
                    actions.append(['insert', k, {"clause": gold_sql_clauses[k]["clause"], "subquery0": {}}])
                    subquery_edits = get_edits(
                        empty_clause, 
                        gold_sql_clauses[k]["subquery0"], 
                        empty_sql_label, 
                        gold_sql_label[k],
                        schema
                    )
                    for e in subquery_edits:
                        if isinstance(e[1], list):
                            e[1] = [k, "subquery0"] + e[1]
                        else:
                            e[1] = [k, "subquery0", e[1]]
                        actions.append(e)
                elif gold_sql_label[k] is None or len(gold_sql_label[k]) == 0:
                    actions.append(['delete', k])
                else:
                    subquery_edits = get_edits(
                        sql_clauses[k]["subquery0"], 
                        gold_sql_clauses[k]["subquery0"], 
                        sql_label[k], 
                        gold_sql_label[k],
                        schema
                    )
                    for e in subquery_edits:
                        if isinstance(e[1], list):
                            e[1] = [k, "subquery0"] + e[1]
                        else:
                            e[1] = [k, "subquery0", e[1]]
                        actions.append(e)

            elif k in ["from", "where", "having"]:
                if sql_label[k] is None or len(sql_label[k]) == 0:
                    if isinstance(gold_sql_clauses[k], dict):
                        val = {"clause": gold_sql_clauses[k]["clause"]} 
                        for i in range(len(gold_sql_clauses[k]) - 1):
                            val[f"subquery{i}"] = {}
                        actions.append(['insert', k, val])

                        for i in range(len(gold_sql_clauses[k]) - 1):
                            subquery_edits = get_edits(
                                empty_clause, 
                                gold_sql_clauses[k][f"subquery{i}"], 
                                empty_sql_label, 
                                get_sql(schema, rebuild_sql(gold_sql_clauses[k][f"subquery{i}"])),
                                schema
                            )
                            for e in subquery_edits:
                                if isinstance(e[1], list):
                                    e[1] = [k, f"subquery{i}"] + e[1]
                                else:
                                    e[1] = [k, f"subquery{i}", e[1]]
                                actions.append(e)
                    else:
                        actions.append(['insert', k, gold_sql_clauses[k]])
                elif gold_sql_label[k] is None or len(gold_sql_label[k]) == 0:
                    actions.append(['delete', k])
                
                else:
                    if isinstance(sql_clauses[k], dict) and isinstance(gold_sql_clauses[k], dict):
                        if sql_clauses[k]["clause"] != gold_sql_clauses[k]["clause"]:
                            actions.append(['replace', [k, "clause"], gold_sql_clauses[k]["clause"]])

                        for i in range(len(gold_sql_clauses[k]) - 1):
                            subquery_edits = get_edits(
                                sql_clauses[k][f"subquery{i}"], 
                                gold_sql_clauses[k][f"subquery{i}"], 
                                get_sql(schema, rebuild_sql(sql_clauses[k][f"subquery{i}"])),
                                get_sql(schema, rebuild_sql(gold_sql_clauses[k][f"subquery{i}"])),
                                schema
                            )
                            for e in subquery_edits:
                                if isinstance(e[1], list):
                                    e[1] = [k, f"subquery{i}"] + e[1]
                                else:
                                    e[1] = [k, f"subquery{i}", e[1]]
                                actions.append(e)
                    elif isinstance(gold_sql_clauses[k], dict):
                        val = {"clause": gold_sql_clauses[k]["clause"]} 
                        for i in range(len(gold_sql_clauses[k]) - 1):
                            val[f"subquery{i}"] = {}
                        actions.append(['replace', k, val])

                        for i in range(len(gold_sql_clauses[k]) - 1):
                            subquery_edits = get_edits(
                                empty_clause, 
                                gold_sql_clauses[k][f"subquery{i}"], 
                                empty_sql_label, 
                                get_sql(schema, rebuild_sql(gold_sql_clauses[k][f"subquery{i}"])),
                                schema
                            )
                            for e in subquery_edits:
                                if isinstance(e[1], list):
                                    e[1] = [k, f"subquery{i}"] + e[1]
                                else:
                                    e[1] = [k, f"subquery{i}", e[1]]
                                actions.append(e)
                    else:
                        actions.append(['replace', k, gold_sql_clauses[k]])
            
            else:
                if sql_label[k] is None or len(sql_label[k]) == 0:
                    actions.append(['insert', k, gold_sql_clauses[k]])
                elif gold_sql_label[k] is None or len(gold_sql_label[k]) == 0:
                    actions.append(['delete', k])
                else:
                    actions.append(['replace', k, gold_sql_clauses[k]])
    
    return actions