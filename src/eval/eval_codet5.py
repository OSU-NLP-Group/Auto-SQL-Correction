from src.scfg.sql import Sql
from src.models.codet5 import CodeT5
from src.preproc.preproc import execute_edit
from src.preproc.get_edits import rebuild_sql
from src.preproc.utils import SQL_DICT_KEYS
from src.utils.helpers import get_device
from src.utils.tokenize_py import tokenize_py
from src.utils.spider_eval.evaluation import build_foreign_key_map_from_json, evaluate

import json
import torch

def eval_codit5(codet5, dev, device, args, gold):
    predictions = []
    codet5.model.eval()
    for ex in dev:
        query = ""
        if ex["out"].startswith(" <s> "):
            query = ex["inp"].split(" </s> ")[1]
        else:
            inp_tokens = codet5.tokenizer(
                ex["inp"], 
                return_tensors="pt"
            ).to(device)

            beam = codet5.model.generate(
                inp_tokens["input_ids"], 
                max_length=codet5.max_length,
                num_beams=args.beam_size, 
                num_return_sequences=1
            )
            
            beam_strs = codet5.tokenizer.batch_decode(
                beam, 
                #skip_special_tokens=True
            )

            try:
                query = beam_strs[0].split(" <s> ")[1].replace("</s>", "")
            except:
                print(beam_strs[0])
                
        if query == "":    
            query = "ERROR"
        elif args.query_type == "py":
            try:
                abs_t = Sql()
                _ = abs_t.parse_python(tokenize_py(query), 0)
                query = abs_t.print_sql()
            except:
                query = "ERROR"

        predictions.append({
            "inp": ex["inp"],
            "pred": query,
            "gold": ex["out"]
        })

    out_predictions_eval = open("data/dev_pred.sql", "w+")
    out_predictions_eval.write("\n".join([ex["pred"] for ex in predictions]))
    out_predictions_eval.close()

    out_predictions_record = open("log/exp/eval_codet5.json", "w+")
    json.dump(predictions, out_predictions_record, indent=2)

    #gold = "data/spider/dev_gold.sql"
    pred = "data/dev_pred.sql"
    db_dir = "data/spider/database"
    table = "data/spider/tables.json"
    etype = args.etype

    kmaps = build_foreign_key_map_from_json(table)
    return evaluate(gold, pred, db_dir, etype, kmaps)


def eval_codet5_edit(codet5, dev, device, args, gold="data/sqledit_dev_gold.sql"):
    sql_queries = []
    predictions = []

    step = 0
    codet5.model.eval()
    for ex in dev:
        if ex["out"].startswith(" <s> sql = "):
            query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
            query = rebuild_sql(query_dict)

            if query == "" or len(query) == 0:
                query = "ERROR"
            
            sql_queries.append(query)
            
            predictions.append({
                "inp": ex["inp"],
                "pred": query,
                "gold": ex["out"]
            })
        else:
            inp_tokens = codet5.tokenizer(
                ex["inp"], 
                return_tensors="pt"
            ).to(device)

            beam = codet5.model.generate(
                inp_tokens["input_ids"], 
                max_length=codet5.max_length,
                num_beams=args.beam_size, 
                num_return_sequences=args.beam_size,
                output_scores=True,
                return_dict_in_generate=True
            )
            
            beam_strs = codet5.tokenizer.batch_decode(
                beam.sequences, 
                skip_special_tokens=True
            )

            program = beam_strs[0]
            query = ""
            query_exec = ""
            if args.program_only:
                query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                program = program.split("sql = ")[0]
                lines = program.split("\n")
                for l in lines:
                    query_dict, return_code = execute_edit(query_dict, l)
                query = rebuild_sql(query_dict)
            else:
                try:
                    query_dict = json.loads(program.split("sql = ")[1])
                    query = rebuild_sql(query_dict)
                except:
                    query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                    query = rebuild_sql(query_dict)

            if query == "" or len(query) == 0:
                query = "ERROR"     
            sql_queries.append(query)

            predictions.append({
                "inp": ex["inp"],
                "pred": beam_strs,
                "final_query": query,
                "gold": ex["out"]
            })

        step += 1
        if step % 100 == 0:
            print("Eval Step {} / {}".format(step, len(dev)))

    out_predictions_record = open("eval_codet5.json", "w+")
    json.dump(predictions, out_predictions_record, indent=2)

    out_predictions_eval = open("data/dev_pred.sql", "w+")
    out_predictions_eval.write("\n".join(sql_queries))
    out_predictions_eval.close()

    pred = "data/dev_pred.sql"
    db_dir = "data/spider/database"
    table = "data/spider/tables.json"
    etype = args.etype
    kmaps = build_foreign_key_map_from_json(table)

    return evaluate(gold, pred, db_dir, etype, kmaps)


def eval_codet5(args):
    device = get_device(args)
    codet5 = CodeT5(args.load_checkpoint, args.edit_type)
    dev = json.load(open(args.sqledit_test_fname))
    codet5.model.to(device)
    eval_codet5_edit(codet5, dev, device, args, gold="data/spider/dev_gold.sql")