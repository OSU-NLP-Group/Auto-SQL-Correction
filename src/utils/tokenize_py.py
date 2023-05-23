from nltk import word_tokenize

def tokenize_py(string):
    string = str(string)
    string = string.replace("\'", "\"")  # ensures all string values wrapped by "" problem??
    quote_idxs = [idx for idx, char in enumerate(string) if char == '"']
    assert len(quote_idxs) % 2 == 0, "Unexpected quote"

    # keep string value as token
    vals = {}
    for i in range(len(quote_idxs)-1, -1, -2):
        qidx1 = quote_idxs[i-1]
        qidx2 = quote_idxs[i]
        val = string[qidx1: qidx2+1]
        key = "__val_{}_{}__".format(qidx1, qidx2)
        string = string[:qidx1] + key + string[qidx2+1:]
        vals[key] = val

    toks = [word.lower() for word in word_tokenize(string)]
    tmp = []
    remove_op = [".distinct", ".between", ".in_", ".like", ".is_", ".exists", ".asc", ".desc"]
    # clean column tokens
    for i in range(len(toks)):
        if ".c." in toks[i] or toks[i].startswith("__val_"): 
            flag = False
            for op in remove_op:
                if toks[i].endswith(op):
                    flag = True
                    t1 = toks[i][:-len(op)]
                    t2 = op
                    tmp.append(t1)
                    tmp.append(t2)
                    break
            
            if not flag:
                tmp.append(toks[i])
        elif toks[i].endswith(".join"):
            t1 = toks[i][:-len(".join")]
            t2 = ".join"
            tmp.append(t1)
            tmp.append(t2)
        else:
            tmp.append(toks[i])
    toks = tmp
    # replace with string value token
    for i in range(len(toks)):
        if toks[i] in vals:
            toks[i] = vals[toks[i]]

    # find if there exists !=, >=, <=
    eq_idxs = [idx for idx, tok in enumerate(toks) if tok == "="]
    eq_idxs.reverse()
    prefix = ('!', '>', '<')
    for eq_idx in eq_idxs:
        pre_tok = toks[eq_idx-1]
        if pre_tok in prefix:
            toks = toks[:eq_idx-1] + [pre_tok + "="] + toks[eq_idx+1: ]

    return toks