from src.preproc.process_spider import process_spider
from src.preproc.get_in_out import get_in_out
from src.preproc.utils import SQL_DICT_KEYS, DEV_DB

import json
import re


def execute_edit(sql, program):
    if program == "return sql":
        return sql, 0
    elif re.match(r".*\.pop\(\"(.*)\"\)", program):
        try:
            exec(program)
            return sql, 0
        except:
            print(program)
            return sql, 1
    else:
        parts = program.split(" = ")
        part1 = parts[0]
        part2 = " = ".join(parts[1:]).rstrip()

        if part2:
            if part2.startswith('"') and part2.endswith('"'):
                program = part1 + " = '" + part2[1:-1] + "'" #convert to apos to avoid compile errors
            else:
                try:
                    program = part1 + " = " + str(json.loads(part2))
                except:
                    print(part1, part2)
                    print(part2[0], part2[-1])
                    return sql, 1

            try:
                exec(program)
                return sql, 0
            except:
                print(program)
                return sql, 1
        else:
            print(part1 + " = " + part2)
            return sql, 1


def split_train_dev(processed_spider_train_all):
    # Split the held-out development set
    sqledit_train = []
    sqledit_dev = []
    dev_temp = {}

    for ex in processed_spider_train_all:
        if ex["db_id"] in DEV_DB:
            if ex["db_id"] in dev_temp:
                dev_temp[ex["db_id"]].append(ex)
            else:
                dev_temp[ex["db_id"]] = [ex]
        else:
            sqledit_train.append(ex)
    
    for db_id in DEV_DB:
        sqledit_dev += dev_temp[db_id]

    return sqledit_train, sqledit_dev


def preproc(args):
    spider_train = json.load(open(args.spider_train_fname))
    spider_train_preds = json.load(open(f"data/spider-train-{args.base_parser}.json"))
    processed_spider_train_all = process_spider(spider_train, spider_train_preds, args)
    sqledit_train, sqledit_dev = split_train_dev(processed_spider_train_all)

    train_data = get_in_out(
        sqledit_train,
        query_type=args.query_type, 
        edit_type=args.edit_type
    )
    print("Train data size {}".format(len(train_data)))

    out = open(args.sqledit_train_fname, "w+")
    json.dump(train_data, out, indent=2)
    out.close()

    dev_data = get_in_out(
        sqledit_dev, 
        query_type=args.query_type, 
        edit_type=args.edit_type,
        is_train=False
    )
    print("Dev data size {}".format(len(dev_data)))

    out = open(args.sqledit_dev_fname, "w+")
    json.dump(dev_data, out, indent=2)
    out.close()

    spider_dev = json.load(open("data/spider/dev.json"))
    spider_dev_preds = json.load(open(f"data/spider-dev-{args.base_parser}.json"))
    sqledit_test = process_spider(spider_dev, spider_dev_preds, args, is_train=False)

    test_data = get_in_out(
        sqledit_test, 
        query_type=args.query_type, 
        edit_type=args.edit_type,
        is_train=False
    )
    print("Test data size {}".format(len(test_data)))

    out = open(args.sqledit_test_fname, "w+")
    json.dump(test_data, out, indent=2)
    out.close()