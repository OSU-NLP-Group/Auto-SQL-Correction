from src.preproc.get_edits import get_edits
from src.preproc.utils import schemas, tables, Schema, empty_clause, empty_sql_label
from src.utils.tokenize_py import tokenize_py
from src.utils.spider_eval.process_sql import get_sql, tokenize

from difflib import SequenceMatcher
from nltk import word_tokenize
import json

SP_TOK_TEMPLATE = {
    "replace": "<REPLACE_OLD> {} <REPLACE_NEW> {} <REPLACE_END>",
    "insert": "<INSERT> {} <INSERT_END>",
    "delete": "<DELETE> {} <DELETE_END>"
}


def get_codit_in_out(processed_data, query_type, is_train=True):
    final_data = []
    for ex in processed_data:
        inp = ex["question"]
        if len(word_tokenize(inp + ex["schema_text"])) <= 512:
            inp += ex["schema_text"]

        if query_type == "pydict":
            inp += " </s> " + ex["init_query_py"]

            a = tokenize_py(ex["init_query_py"])
            b = tokenize_py(ex["query_py"])
            s = SequenceMatcher(None, a, b)
            codit = [[tag, " ".join(a[i1:i2]), " ".join(b[j1:j2])] for tag, i1, i2, j1, j2 in s.get_opcodes()]
            edit_plan = []
            for e in codit:
                if e[0] == "replace":
                    edit_plan.append(SP_TOK_TEMPLATE[e[0]].format(e[1], e[2]))
                elif e[0] == "insert":
                    edit_plan.append(SP_TOK_TEMPLATE[e[0]].format(e[2]))
                elif e[0] == "delete":
                    edit_plan.append(SP_TOK_TEMPLATE[e[0]].format(e[1]))

            out = " ".join(edit_plan) + " <s> " + ex["query_py"]
        else:
            inp += " </s> " + ex["init_query_sql"]

            a = tokenize(ex["init_query_sql"])
            b = tokenize(ex["query_sql"])
            s = SequenceMatcher(None, a, b)
            codit = [[tag, " ".join(a[i1:i2]), " ".join(b[j1:j2])] for tag, i1, i2, j1, j2 in s.get_opcodes()]
            edit_plan = []
            for e in codit:
                if e[0] == "replace":
                    edit_plan.append(f"<REPLACE_OLD> {e[1]} <REPLACE_NEW> {e[2]} <REPLACE_END>")
                elif e[0] == "insert":
                    edit_plan.append(f"<INSERT> {e[2]} <INSERT_END>")
                elif e[0] == "delete":
                    edit_plan.append(f"<DELETE> {e[1]} <DELETE_END>")

            out = " ".join(edit_plan) + " <s> " + ex["query_sql"]

        final_data.append({
            "inp": inp,
            "out": out
        })
    return final_data


def format_program(edits):
    program = []
    for e in edits:
        if e[0] == "delete":
            if isinstance(e[1], str):
                program.append("sql.pop(\"{}\")".format(
                    e[1]
                ))
            else:
                p = (
                    "sql" +
                    "".join(["[\"{}\"]".format(k) for k in e[1][:-1]]) + 
                    ".pop(\"{}\")".format(e[1][-1])
                )
                program.append(p)
        else:
            val = (
                json.dumps(e[2]) 
                if isinstance(e[2], dict) 
                else "\"" + e[2].replace(" , ", ", ").replace(" ;", "") + "\""
            )
            if isinstance(e[1], str):
                program.append("sql[\"{}\"] = {}".format(e[1], val))
            else:
                p = (
                    "sql" +
                    "".join(["[\"{}\"]".format(k) for k in e[1]]) + 
                    " = {}".format(val)
                )
                program.append(p)

    return program


def get_program_in_out(processed_data, is_train=True):
    final_data = []
    track_inp = set()

    for ex in processed_data:
        db_id = ex['db_id']
        init_query_clauses = ex["init_query_dict"]
        gold_query_clauses = ex["query_dict"]

        inp = ex["question"]
        if len(word_tokenize(inp + ex["schema_text"])) <= 512:
            inp += ex["schema_text"]
        inp += " </s> sql = " + json.dumps(init_query_clauses)

        schema = schemas[db_id]
        table = tables[db_id]
        schema = Schema(schema, table)

        edits = []
        if is_train or ex["label"] == 0:
            gold_sql = empty_sql_label
            try:
                gold_sql = get_sql(schema, ex["query_sql"])
            except:
                # Shouldn't happen
                continue

            try:
                init_sql = get_sql(schema, ex["init_query_sql"])
                gold_sql = get_sql(schema, ex["query_sql"])
                edits = get_edits(init_query_clauses, gold_query_clauses, init_sql, gold_sql, schema)
            except:
                if ex["init_query_sql"]:
                    inp = inp.split(" </s> sql = ")[0] + " </s> sql = {}"
                
                if inp not in track_inp:
                    edits = get_edits(
                        empty_clause, 
                        gold_query_clauses, 
                        empty_sql_label, 
                        gold_sql,
                        schema
                    )
                    track_inp.add(inp)
                elif is_train:
                    continue

        out = "{} <s> sql = {}".format(
            "\n".join(format_program(edits)),
            json.dumps(gold_query_clauses)
        )

        final_data.append({
            "db_id": ex['db_id'],
            "inp": inp,
            "out": out
        })

    return final_data

def get_in_out(sqledit, query_type, edit_type, is_train=True):
    if edit_type == "program":
        return get_program_in_out(sqledit, is_train)
    else:
        return get_codit_in_out(sqledit, query_type, is_train)