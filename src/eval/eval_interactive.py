from src.eval.user import choose
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

def eval_codet5_iter_edit(codet5, dev, device, args, gold):
    sql_queries = []
    predictions = []
    codet5.model.eval()
    for ex in dev:
        if ex["out"].startswith("# sql = "):
            query_dict = json.loads(ex["inp"].split(" # sql = ")[1])
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
            turn_inp = ex["inp"]
            current_sql = json.loads(turn_inp.split(" # sql = ")[1])
            for t in range(14):
                inp_tokens = codet5.tokenizer(
                    turn_inp, 
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
                    skip_special_tokens=True
                )

                program = beam_strs[0].split(" # sql = ")[0]
                current_sql, return_code = execute_edit(current_sql, program)

                if return_code == 1 or current_sql == json.loads(turn_inp.split(" # sql = ")[1]):
                    break
                else:
                    turn_inp = turn_inp.split(" # sql = ")[0] + " " + program + " # sql = {}".format(json.dumps(current_sql))

            query = rebuild_sql(current_sql)
            if query == "" or len(query) == 0:
                query = "ERROR"
                    
            sql_queries.append(query)
            predictions.append({
                "inp": ex["inp"],
                "pred": turn_inp.split("def edit(sql): ")[1],
                "gold": ex["out"]
            })

    out_predictions_eval = open("data/dev_pred.sql", "w+")
    out_predictions_eval.write("\n".join(sql_queries))
    out_predictions_eval.close()

    out_predictions_record = open("log/exp/eval_codet5_edit_iter.json", "w+")
    json.dump(predictions, out_predictions_record, indent=2)

    #gold = "data/spider/dev_gold.sql"
    pred = "data/dev_pred.sql"
    db_dir = "data/spider/database"
    table = "data/spider/tables.json"
    etype = args.etype

    kmaps = build_foreign_key_map_from_json(table)
    return evaluate(gold, pred, db_dir, etype, kmaps)

def eval_codet5(args):
    device = get_device(args)
    codet5 = CodeT5(args.checkpoint, args.task)
    dev = json.load(open(args.test_data))
    codet5.model.to(device)
    eval_codet5_iter_edit(codet5, dev, device, args, gold="data/spider/dev_gold.sql")