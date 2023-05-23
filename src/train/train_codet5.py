from transformers import Adafactor, get_scheduler
from src.models.codet5 import CodeT5
from src.eval.eval_codet5 import eval_codet5_edit
from src.utils.helpers import get_device

import json
import os
import random
import torch


def train_codet5(args):
    # Init training device ("cpu" or "cuda:x" where x is the gpu number)
    device = get_device(args)

    # Load training and development set
    train = json.load(open(args.sqledit_train_fname))
    dev = json.load(open(args.sqledit_dev_fname))

    # Set training constants
    batch_size = args.batch_size
    num_train = len(train)
    num_epochs = args.epochs
    num_batches = (
        num_train // batch_size + 1 
        if num_train % batch_size > 0 
        else num_train // batch_size
    )
    num_steps = num_epochs * (
        num_batches // args.grad_accum + 1 
        if num_batches % args.grad_accum > 0 
        else num_batches // args.grad_accum
    )

    # Load model, optimizer, and scheduler
    codet5 = CodeT5(args.load_checkpoint, args.edit_type)
    codet5.model.to(device)
    optimizer = Adafactor(
        codet5.model.parameters(), 
        lr=args.lr, 
        scale_parameter=False, 
        relative_step=False
    )
    lr_scheduler = get_scheduler(
        name="linear", 
        optimizer=optimizer, 
        num_warmup_steps=num_steps // 10, 
        num_training_steps=num_steps
    )

    # Training loop
    step = 0
    best_dev_em = -1.0
    best_dev_ex = -1.0
    for i in range(num_epochs):
        random.shuffle(train)
        codet5.model.train()
        for j in range(num_batches):
            # Load batch
            batch = train[j * batch_size : (j + 1) * batch_size]

            # Tokenize input and output
            inp_tokens = codet5.tokenizer(
                [ex["inp"] for ex in batch], 
                padding=True, 
                return_tensors="pt"
            ).to(device)
            out_tokens = codet5.tokenizer(
                [ex["out"] for ex in batch], 
                padding=True, 
                return_tensors="pt"
            ).to(device)
            
            # Shift output tokens for decoder training
            labels = out_tokens["input_ids"].clone().detach()
            labels = torch.where(
                labels == codet5.tokenizer.pad_token_id,
                -100, 
                labels
            )
            labels = labels[:, 1:].contiguous()

            # Model call and compute loss
            outputs = codet5.model(
                input_ids=inp_tokens["input_ids"],
                attention_mask=inp_tokens["attention_mask"],
                labels=labels,
                decoder_attention_mask=out_tokens["attention_mask"][:, 1:]
            )
            loss = outputs.loss / args.grad_accum
            loss.backward()

            # Back prop with gradient accumulation
            if (j + 1) % args.grad_accum == 0 or (j + 1) == num_batches:
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()
                step += 1
            
                # Logging
                if step % 100 == 0:
                    print("Epoch {} Step {} Loss {:.6f}".format(i, step, loss))

                # Skip validation for the first epoch
                if i > 0 and step % 500 == 0:
                    scores = eval_codet5_edit(codet5, dev, device, args)
                    exact_match = scores['all']['exact']
                    exec_match = scores['all']['exec']

                    # Checkpoint selection
                    if (
                        exact_match > best_dev_em or
                        (exact_match == best_dev_em and exec_match > best_dev_ex)
                    ):
                        best_dev_em = exact_match
                        best_dev_ex = exec_match
                        if not os.path.exists(args.save_checkpoint):
                            os.mkdir(args.save_checkpoint)
                        codet5.tokenizer.save_pretrained(args.save_checkpoint)
                        codet5.model.save_pretrained(args.save_checkpoint)

    # End of training validation
    scores = eval_codet5_edit(codet5, dev, device, args)
    exact_match = scores['all']['exact']
    exec_match = scores['all']['exec']

    # Checkpoint selection
    if (
        exact_match > best_dev_em or
        (exact_match == best_dev_em and exec_match > best_dev_ex)
    ):
        best_dev_em = exact_match
        best_dev_ex = exec_match
        if not os.path.exists(args.save_checkpoint):
            os.mkdir(args.save_checkpoint)
        codet5.tokenizer.save_pretrained(args.save_checkpoint)
        codet5.model.save_pretrained(args.save_checkpoint)