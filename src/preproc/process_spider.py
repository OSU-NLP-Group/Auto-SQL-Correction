from src.preproc.utils import db_path, table_file, schemas, tables, Schema, DEV_DB
from src.utils.get_schema_unifiedskg import serialize_schema
from src.utils.disamb_sql_smbop import disambiguate_items
from src.utils.spider_eval.process_sql import tokenize
from src.scfg.sql import Sql

from tqdm import tqdm


def remove_alias(toks):
	as_idxs = [idx for idx, tok in enumerate(toks) if tok == 'as']
	alias = {}
	for idx in as_idxs:
		alias[toks[idx+1]] = toks[idx-1]

	clean_toks = []
	counter = 0
	while counter < len(toks):
		tok = toks[counter]

		for a in alias:
			if tok.startswith(a + "."):
				tok = tok.replace(a + ".", alias[a] + ".")

		if counter in as_idxs:
			counter += 1
		else:
			clean_toks.append(tok)
		counter += 1

	return clean_toks


def get_query_sql_rep(db_id, raw_sql, is_gold=True):
    query_sql = ""

    try:
        toks = disambiguate_items(
            db_id, 
            tokenize(raw_sql), 
            table_file, 
            allow_aliases=False
        )
        query_sql = ' '.join(toks)
    except:
        if is_gold:
            toks = tokenize(raw_sql)
            clean_toks = remove_alias(toks)
            query_sql = ' '.join(clean_toks)

    return query_sql.replace(" , ", ", ").replace(" ;", "")


def get_query_pydict_rep(query_sql):
    abs_t = Sql()
    _ = abs_t.parse_sql(tokenize(query_sql), 0)

    return abs_t.print_sql_dict()


def process_spider(spider, spider_preds, args, is_train=True):
    data = []
    for ex, ex_w_pred in tqdm(zip(spider, spider_preds)):
        # Examples are shuffled for cross validation
        if is_train:
            db_id = ex_w_pred["db_id"]
            gold_sql = ex_w_pred["gold_query"]
        else:
            db_id = ex["db_id"]
            gold_sql = ex["query"]

        # Construct schema and linearize
        schema = schemas[db_id]
        table = tables[db_id]
        schema = Schema(schema, table)
        schema_text = serialize_schema(
            question=ex_w_pred["question"] if is_train else ex["question"],
            db_path=db_path,
            db_id=db_id,
            db_schema=schema.schema,
            schema_serialization_with_db_id=False,
            schema_serialization_with_db_content=args.use_content,
        )

        # Get SQL and PyDict representation
        query_sql = get_query_sql_rep(db_id, gold_sql)
        query_pydict = get_query_pydict_rep(query_sql)

        if is_train:
            if len(ex_w_pred["wrong_init_query"]) > 0:
                # Iterate through all synthesized errors and keep valid ones
                for sql_str in ex_w_pred["wrong_init_query"]:
                    init_q = sql_str.replace(" , ", ", ").replace(" ;", "")                
                    init_query_dict = {}
                    try:
                        init_query_dict = get_query_pydict_rep(init_q)
                    except:
                        if db_id not in DEV_DB:
                            continue

                    data.append(
                        {
                            'db_id': db_id,
                            'schema_text': schema_text,
                            'question': ex_w_pred['question'],
                            'init_query_sql': init_q,
                            'init_query_dict': init_query_dict,
                            'query_sql': query_sql,
                            'query_dict': query_pydict,
                            'label': 0
                        }
                    )

                    # Only collect the top1 confidence error for development set examples
                    if db_id in DEV_DB:
                        break
            
            else:
                # If an example doesn't have synthesized error, 
                # train model to generate gold from scratch like editing an empty string
                data.append(
                    {
                        'db_id': db_id,
                        'schema_text': schema_text,
                        'question': ex_w_pred['question'],
                        'init_query_sql': "",
                        'init_query_dict': {},
                        'query_sql': query_sql,
                        'query_dict': query_pydict,
                        'label': 0
                    }
                )
        else:
            init_q = ""
            # Our codet5 was trained on the disambiguated SQL rep
            if args.base_parser == "codet5":
                init_q = ex_w_pred["predictSQL"]
            else:
                p_str = ex_w_pred["predictSQL"]
                init_q = get_query_sql_rep(db_id, p_str, is_gold=False)
            
            init_query_dict = {}
            if init_q:
                try:
                    init_query_dict = get_query_pydict_rep(init_q)
                except:
                    print(init_q)

            data.append(
                {
                    'db_id': db_id,
                    'schema_text': schema_text,
                    'question': ex['question'],
                    'init_query_sql': init_q,
                    'init_query_dict': init_query_dict,
                    'query_sql': query_sql,
                    'query_dict': query_pydict,
                    'label': ex_w_pred["label"]
                }
            )
    
    return data
