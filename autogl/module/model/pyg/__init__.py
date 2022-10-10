from ._model_registry import MODEL_DICT, ModelUniversalRegistry, register_model
from .base import BaseAutoModel
from .topkpool import AutoTopkpool

# from .graph_sage import AutoSAGE
from .graphsage import AutoSAGE
from .graph_saint import GraphSAINTAggregationModel
from .gcn import AutoGCN
from .gat import AutoGAT
from .gin import AutoGIN

from .robust.gcn_svd import AutoGCNSVD
from .robust.gnnguard import AutoGNNGuard, GCN4GNNGuard

__all__ = [
    "ModelUniversalRegistry",
    "register_model",
    "BaseAutoModel",
    "AutoTopkpool",
    "AutoSAGE",
    "GraphSAINTAggregationModel",
    "AutoGCN",
    "AutoGAT",
    "AutoGIN",
    "AutoGCNSVD",
    "AutoGNNGuard",
    "GCN4GNNGuard",
]
