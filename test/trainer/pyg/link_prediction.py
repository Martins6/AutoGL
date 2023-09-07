from autogl.module.train import LinkPredictionTrainer
from autogl.datasets import build_dataset_from_name
from torch_geometric.utils import train_test_split_edges

def test_lp_trainer():

    dataset = build_dataset_from_name("cora")
    data = dataset[0]
    data = train_test_split_edges(data, 0.1, 0.1)
    dataset = [data]

    lp_trainer = LinkPredictionTrainer(model='gcn', init=False)

    lp_trainer.num_features = data.x.size(1)
    lp_trainer.initialize()
    print(lp_trainer.encoder.encoder)
    print(lp_trainer.decoder.decoder)

    lp_trainer.train(dataset, True)
    result = lp_trainer.evaluate(dataset, "test", "auc")
    print(result)

test_lp_trainer()
