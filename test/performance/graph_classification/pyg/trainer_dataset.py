"""
Performance check of AutGL Trainer + Dataset
"""

import os

os.environ["AUTOGL_BACKEND"] = "pyg"

import random
import numpy as np

from autogl.datasets import build_dataset_from_name, utils
from autogl.module.train import GraphClassificationFullTrainer
from autogl.solver.utils import set_seed
import logging

logging.basicConfig(level=logging.ERROR)

def fixed(**kwargs):
    return [{
        'parameterName': k,
        "type": "FIXED",
        "value": v
    } for k, v in kwargs.items()]

if __name__ == '__main__':

    import argparse
    parser = argparse.ArgumentParser('pyg trainer')
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--dataset', type=str, choices=[x.lower() for x in ['MUTAG', 'COLLAB', 'IMDBBINARY', 'IMDBMULTI', 'NCI1', 'PROTEINS', 'PTC', 'REDDITBINARY', 'REDDITMULTI5K']], default='mutag')
    parser.add_argument('--dataset_seed', type=int, default=2021)
    parser.add_argument('--batch_size', type=int, default=32)
    parser.add_argument('--repeat', type=int, default=50)
    parser.add_argument('--model', type=str, choices=['gin', 'gat', 'gcn', 'sage'], default='gin')
    parser.add_argument('--lr', type=float, default=0.0001)
    parser.add_argument('--epoch', type=int, default=100)

    args = parser.parse_args()

    # seed = 100
    dataset = build_dataset_from_name(args.dataset)
    
    # 1. split dataset [fix split]
    dataids = list(range(len(dataset)))
    random.seed(args.dataset_seed)
    random.shuffle(dataids)
    
    fold = int(len(dataset) * 0.1)
    train_index = dataids[:fold * 8]
    val_index = dataids[fold * 8: fold * 9]
    test_index = dataids[fold * 9: ]
    dataset.train_index = train_index
    dataset.val_index = val_index
    dataset.test_index = test_index

    labels = np.array([data.data['y'].item() for data in dataset.test_split])

    dataset = utils.conversion.general_static_graphs_to_pyg_dataset(dataset)

    accs = []

    if args.model == 'gin':
        model_hp = {
            # hp from model
            "num_layers": 5,
            "hidden": [64,64,64,64],
            "dropout": 0.5,
            "act": "relu",
            "eps": "False",
            "mlp_layers": 2,
            "neighbor_pooling_type": "sum",
            "graph_pooling_type": "sum"
        }
    elif args.model == 'topkpool':
        model_hp = {
            "ratio": 0.8,
            "dropout": 0.5,
            "act": "relu"
        }

    from tqdm import tqdm
    for seed in tqdm(range(args.repeat)):
        set_seed(seed)

        trainer = GraphClassificationFullTrainer(
            model=args.model,
            device=args.device,
            init=False,
            num_features=dataset[0].x.size(1),
            num_classes=max([data.y.item() for data in dataset]) + 1,
            loss='nll_loss',
            feval=('acc')
        ).duplicate_from_hyper_parameter(
            {
                "trainer": {
                    # hp from trainer
                    "max_epoch": args.epoch,
                    "batch_size": args.batch_size, 
                    "early_stopping_round": args.epoch + 1, 
                    "lr": args.lr, 
                    "weight_decay": 0,
                },
                "encoder": model_hp
            }
        )

        trainer.train(dataset, False)
        out = trainer.predict(dataset, 'test').detach().cpu().numpy()
        acc = (out == labels).astype('float').mean()
        accs.append(acc)
    print('{:.4f} ~ {:.4f}'.format(np.mean(accs), np.std(accs)))
