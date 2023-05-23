import torch

def get_device(args):
    if args.gpu >= 0:
        device = torch.device("cuda:{}".format(args.gpu)) if torch.cuda.is_available() else torch.device("cpu")
    else:
        device = torch.device("cpu")

    return device