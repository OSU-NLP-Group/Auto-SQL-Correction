from src.preproc.preproc import preproc
from src.train.train_codet5 import train_codet5
from src.eval.eval_codet5 import eval_codet5

import argparse
import numpy as np
import random
import torch


def add_general_args(parser):
    parser.add_argument(
        "--program_only", action="store_true"
    )
    parser.add_argument(
        "--seed", type=int, 
        default=42
    )
    parser.add_argument(
        "--gpu", type=int, 
        default=0
    )
    parser.add_argument(
        "--beam_size", type=int, 
        default=3
    )
    return parser


def add_file_args(parser):
    parser.add_argument(
        "--spider_train_fname", type=str, 
        default="data/spider/train_spider.json"
    )
    parser.add_argument(
        "--spider_dev_fname", type=str, 
        default="data/spider/dev.json"
    )
    parser.add_argument(
        "--sqledit_train_fname", type=str, 
        default="data/sqledit-train.json"
    )
    parser.add_argument(
        "--sqledit_dev_fname", type=str, 
        default="data/sqledit-dev.json"
    )
    parser.add_argument(
        "--sqledit_test_fname", type=str, 
        default="data/sqledit-test.json"
    )
    parser.add_argument(
        "--load_checkpoint", type=str, 
        default="Salesforce/codet5-base"
    )
    parser.add_argument(
        "--save_checkpoint", type=str, 
        default="model/"
    )
    return parser


def add_preproc_args(parser):
    parser.add_argument(
        "--preproc", action="store_true"
    )
    parser.add_argument(
        "--use_content", action="store_true"
    )
    parser.add_argument(
        "--query_type", type=str, 
        default="pydict"
    )
    parser.add_argument(
        "--edit_type", type=str, 
        default="program"
    )
    parser.add_argument(
        "--base_parser", type=str, 
        default="codet5"
    )
    return parser


def add_train_args(parser):
    parser.add_argument(
        "--train", action="store_true"
    )
    parser.add_argument(
        "--epochs", type=int, 
        default=10
    )
    parser.add_argument(
        "--lr", type=float, 
        default=3e-5
    )
    parser.add_argument(
        "--batch_size", type=int, 
        default=8
    )
    parser.add_argument(
        "--grad_accum", type=int, 
        default=2
    )
    return parser


def add_eval_args(parser):
    parser.add_argument(
        "--eval", action="store_true"
    )
    parser.add_argument(
        "--etype", type=str, 
        default="all" #all, exec, match
    )
    return parser


def get_args():
    parser = argparse.ArgumentParser()
    parser = add_general_args(parser)
    parser = add_file_args(parser)
    parser = add_preproc_args(parser)
    parser = add_train_args(parser)
    parser = add_eval_args(parser)
    return parser.parse_args()


def set_seed(seed):
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.cuda.manual_seed_all(seed)


if __name__ == "__main__":
    args = get_args()
    set_seed(args.seed)

    if args.preproc:
        preproc(args)
    elif args.train:
        train_codet5(args)
    elif args.eval:
        eval_codet5(args)
    else:
        print("Error: must specify preproc/train/eval in args")
