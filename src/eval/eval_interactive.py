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

            # query = ""
            # for k in NATURAL_SQL_ORDER:
            #     if k in query_dict:
            #         query += query_dict[k] + " "
            
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

            # query = ""
            # for k in NATURAL_SQL_ORDER:
            #     if k in current_sql:
            #         query += current_sql[k] + " "
            
            # if query == "":
            #     query = "INIT_PARSE_ERROR"
                    
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


def eval_codet5_edit(codet5, dev, device, args, gold="data/train_dev_gold.sql"):
    if args.task == "sql_iter_edit_t5":
        return eval_codet5_iter_edit(codet5, dev, device, args, gold)
    elif args.task == "sql_codit_t5":
        return eval_codit5(codet5, dev, device, args, gold)
    else:
        sql_queries = []
        sql_queries_exec = []
        predictions = []
        codet5.model.eval()
        for i, ex in enumerate(dev):
            if i % 50 == 0:
                print(i)
            #if ex["out"].startswith(" <s> correct_sql = "):
            if ex["out"].startswith(" <s> sql = ") or (args.program_only and len(ex["out"]) == 0):
                query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                query = rebuild_sql(query_dict)

                if query == "" or len(query) == 0:
                    query = "ERROR"
                # query = ""
                # for k in NATURAL_SQL_ORDER:
                #     if k in query_dict:
                #         query += query_dict[k] + " "
                
                sql_queries.append(query)
                if args.eval_both:
                    sql_queries_exec.append(query)
                
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

                step = 0
                max_step = 1
                history = []
                gold_program = ex["out"].split("sql = ")[0].split("\n")

                #program = beam_strs[0]
                query = ""
                query_exec = ""
                #if args.query_type == "py":
                if args.program_only:
                    while step < max_step:
                        #print(beam_strs)
                        programs = []
                        for program in beam_strs:
                            program = program.split("sql = ")[0]
                            lines = program.split("\n")
                            programs.append(lines)
                        max_step = max(max_step, max([len(p) for p in programs]))

                        choices = [p[step] for p in programs if step < len(p)]
                        picked_idx = choose(choices, gold_program)
                        #print(picked_idx)
                        if picked_idx >= 0:
                            history.append(choices[picked_idx])

                        dec_inp_tokens = (
                            [codet5.tokenizer.pad_token] + 
                            codet5.tokenizer.tokenize("\n".join(history))
                        )
                        dec_inp_token_ids = codet5.tokenizer.convert_tokens_to_ids(dec_inp_tokens)
                        dec_inp_token_ids = torch.tensor(dec_inp_token_ids)[None,:].to(device)
                        
                        beam = codet5.model.generate(
                            inp_tokens["input_ids"], 
                            decoder_input_ids=dec_inp_token_ids,
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

                        step += 1

                    query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                    # program = program.split("sql = ")[0]
                    # lines = program.split("\n")
                    #print(history)
                    for l in history:
                        query_dict, return_code = execute_edit(query_dict, l)

                    try:
                        query = rebuild_sql(query_dict)
                    except:
                        query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                        query = rebuild_sql(query_dict)
                    
                    # for k in NATURAL_SQL_ORDER:
                    #         if k in query_dict:
                    #             query += query_dict[k] + " "
                elif args.eval_both:
                    init_query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                    program_exec = program.split("sql = ")[0]
                    lines = program_exec.split("\n")
                    for l in lines:
                        init_query_dict, return_code = execute_edit(init_query_dict, l)
                    query_exec = rebuild_sql(init_query_dict)

                    if query_exec == "" or len(query_exec) == 0:
                        query_exec = "ERROR" 
                    sql_queries_exec.append(query_exec)

                    try:
                        query_dict = json.loads(program.split("sql = ")[1])
                        query = rebuild_sql(query_dict)
                    except:
                        query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                        query = rebuild_sql(query_dict)
                else:
                    try:
                        #query_dict = json.loads(program.split("correct_sql = ")[1])
                        query_dict = json.loads(program.split("sql = ")[1])
                        query = rebuild_sql(query_dict)
                        # for k in NATURAL_SQL_ORDER:
                        #     if k in query_dict:
                        #         query += query_dict[k] + " "
                    except:
                        query_dict = json.loads(ex["inp"].split(" </s> sql = ")[1])
                        query = rebuild_sql(query_dict)
                        # if len(query_dict) > 0:
                        #     for k in NATURAL_SQL_ORDER:
                        #         if k in query_dict:
                        #             query += query_dict[k] + " "

                if query == "" or len(query) == 0:
                    query = "ERROR"     
                sql_queries.append(query)

                predictions.append({
                    "inp": ex["inp"],
                    "pred": beam_strs,
                    "pred_scores": torch.exp(beam.sequences_scores).tolist(),
                    "final_query": query,
                    "final_query_exec": query_exec,
                    "gold": ex["out"]
                })

        out_predictions_record = open("log/exp/eval_codet5.json", "w+")
        json.dump(predictions, out_predictions_record, indent=2)

        out_predictions_eval = open("data/dev_pred.sql", "w+")
        out_predictions_eval.write("\n".join(sql_queries))
        out_predictions_eval.close()
        if args.eval_both:
            out_predictions_eval = open("data/dev_pred_exec.sql", "w+")
            out_predictions_eval.write("\n".join(sql_queries_exec))
            out_predictions_eval.close()

        # gold = "data/spider/dev_gold.sql"
        # gold = "data/spider/train_dev_gold.sql"
        pred = "data/dev_pred.sql"
        db_dir = "data/spider/database"
        table = "data/spider/tables.json"
        etype = args.etype
        kmaps = build_foreign_key_map_from_json(table)

        if args.eval_both:
            pred_exec = "data/dev_pred_exec.sql"
            evaluate(gold, pred_exec, db_dir, etype, kmaps)

        return evaluate(gold, pred, db_dir, etype, kmaps)


def eval_codet5(args):
    device = get_device(args)
    codet5 = CodeT5(args.checkpoint, args.task)
    dev = json.load(open(args.test_data))
    codet5.model.to(device)
    eval_codet5_edit(codet5, dev, device, args, gold="data/spider/dev_gold.sql")