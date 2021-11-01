import pandas as pd
import torch
import typing as _typing


class _HeterogeneousNodesContainer:
    @property
    def node_types(self) -> _typing.AbstractSet[str]:
        raise NotImplementedError

    def remove_nodes(self, node_t: _typing.Optional[str]) -> '_HeterogeneousNodesContainer':
        raise NotImplementedError

    def reset_nodes(
            self, node_t: _typing.Optional[str],
            nodes_data: _typing.Mapping[str, torch.Tensor]
    ) -> '_HeterogeneousNodesContainer':
        raise NotImplementedError

    def set_data(
            self, node_t: _typing.Optional[str], data_key: str, data: torch.Tensor
    ) -> '_HeterogeneousNodesContainer':
        raise NotImplementedError

    def get_data(
            self, node_t: _typing.Optional[str] = ...,
            data_key: _typing.Optional[str] = ...
    ) -> _typing.Union[torch.Tensor, _typing.Mapping[str, torch.Tensor]]:
        raise NotImplementedError

    def delete_data(
            self, node_t: _typing.Optional[str], data_key: str
    ) -> '_HeterogeneousNodesContainer':
        raise TypeError

    def remove_data(
            self, node_t: _typing.Optional[str], data_key: str
    ) -> '_HeterogeneousNodesContainer':
        return self.delete_data(node_t, data_key)


class _HeterogeneousNodesContainerImplementation(_HeterogeneousNodesContainer):
    def __init__(self, data: _typing.Optional[_typing.Mapping[str, _typing.Mapping[str, torch.Tensor]]] = ...):
        self.__nodes_data: _typing.MutableMapping[str, _typing.MutableMapping[str, torch.Tensor]] = {}
        if data not in (None, Ellipsis) and isinstance(data, _typing.Mapping):
            for node_t, nodes_data in data.items():
                self.reset_nodes(node_t, nodes_data)

    @property
    def node_types(self) -> _typing.AbstractSet[str]:
        return self.__nodes_data.keys()

    def remove_nodes(self, node_t: _typing.Optional[str]) -> _HeterogeneousNodesContainer:
        if not (node_t in (Ellipsis, None) or isinstance(node_t, str)):
            raise TypeError
        elif node_t in (Ellipsis, None):
            if len(self.node_types) == 0:
                return self
            elif len(self.node_types) == 1:
                del self.__nodes_data[tuple(self.node_types)[0]]
            else:
                _error_message: str = ' '.join((
                    "Unable to determine node type automatically,",
                    "possible cause is that the graph contains heterogeneous nodes,",
                    "node type must be specified for graph containing heterogeneous nodes."
                ))
                raise TypeError(_error_message)
        elif isinstance(node_t, str):
            try:
                del self.__nodes_data[node_t]
            except Exception:
                raise ValueError(f"nodes with type [{node_t}] NOT exists")
        return self

    def reset_nodes(
            self, node_t: _typing.Optional[str],
            nodes_data: _typing.Mapping[str, torch.Tensor]
    ) -> _HeterogeneousNodesContainer:
        if not (node_t in (Ellipsis, None) or isinstance(node_t, str)):
            raise TypeError
        elif node_t in (Ellipsis, None) and len(self.node_types) > 1:
            _error_message: str = ' '.join((
                "Unable to determine node type automatically,",
                "possible cause is that the graph contains heterogeneous nodes,",
                "node type must be specified for graph containing heterogeneous nodes."
            ))
            raise TypeError(_error_message)
        elif isinstance(node_t, str) and ' ' in node_t:
            raise ValueError("node type must NOT contain space character (\' \').")
        __node_t: str = "" if node_t is Ellipsis else node_t

        num_nodes: int = ...
        for data_key, data_item in nodes_data.items():
            if not isinstance(data_key, str):
                raise TypeError
            if ' ' in data_key:
                raise ValueError("data key must NOT contain space character (\' \').")
            if not isinstance(data_item, torch.Tensor):
                raise TypeError
            if not data_item.dim() > 0:
                raise ValueError(
                    "data item MUST have at least one dimension, "
                    "and the first dimension corresponds to data for diverse nodes."
                )
            if not isinstance(num_nodes, int):
                num_nodes: int = data_item.size(0)
            if data_item.size(0) != num_nodes:
                raise ValueError
            self.__nodes_data[__node_t] = dict(nodes_data)
        return self

    def set_data(
            self, node_t: _typing.Optional[str], data_key: str, data: torch.Tensor
    ) -> _HeterogeneousNodesContainer:
        if node_t in (Ellipsis, None):
            if len(self.node_types) == 0:
                __node_t: str = ""  # Default node type for homogeneous graph
            elif len(self.node_types) == 1:
                __node_t: str = list(self.node_types)[0]
            else:
                _error_message: str = ' '.join((
                    "Unable to determine node type automatically,",
                    "possible cause is that the graph contains heterogeneous nodes,",
                    "node type must be specified for graph containing heterogeneous nodes."
                ))
                raise TypeError(_error_message)
        elif isinstance(node_t, str):
            __node_t: str = node_t
        else:
            raise TypeError
        if not isinstance(data_key, str):
            raise TypeError
        if not isinstance(data, torch.Tensor):
            raise TypeError
        if ' ' in __node_t:
            raise ValueError
        if ' ' in data_key:
            raise ValueError
        if not data.dim() > 0:
            raise ValueError(
                "data item MUST have at least one dimension, "
                "and the first dimension corresponds to data for diverse nodes."
            )
        if __node_t not in self.node_types:
            self.__nodes_data[__node_t] = dict([(data_key, data)])
        else:
            obsolete_data: _typing.Optional[torch.Tensor] = self.__nodes_data[__node_t].get(data_key)
            if obsolete_data is not None and isinstance(obsolete_data, torch.Tensor):
                if data.size(0) != obsolete_data.size(0):
                    raise ValueError
            elif len(self.__nodes_data.get(__node_t)) > 0:
                num_nodes: int = self.__nodes_data.get(__node_t).get(list(self.node_types)[0]).size(0)
                if data.size(0) != num_nodes:
                    raise ValueError
            self.__nodes_data[__node_t][data_key] = data
        return self

    def __get_data_for_specific_node_type(
            self, node_t: str, data_key: _typing.Optional[str] = ...
    ) -> _typing.Union[torch.Tensor, _typing.Mapping[str, torch.Tensor]]:
        if not isinstance(node_t, str):
            raise TypeError
        elif ' ' in node_t:
            raise ValueError
        if not (data_key in (Ellipsis, None) or isinstance(data_key, str)):
            raise TypeError
        elif isinstance(data_key, str) and ' ' in data_key:
            raise ValueError
        if node_t not in self.node_types:
            raise ValueError("Node type NOT exists")
        elif isinstance(data_key, str):
            data: _typing.Optional[torch.Tensor] = self.__nodes_data[node_t].get(data_key)
            if data is not None:
                return data
            else:
                raise KeyError(
                    f"Data with key [{data_key}] NOT exists "
                    f"for nodes with specific type [{node_t}]"
                )
        else:
            return self.__nodes_data[node_t]

    def __get_data_for_specific_data_key(
            self, data_key: str, node_t: _typing.Optional[str] = ...
    ) -> _typing.Union[torch.Tensor, _typing.Mapping[str, torch.Tensor]]:
        if not isinstance(data_key, str):
            raise TypeError
        elif ' ' in data_key:
            raise ValueError
        if not (node_t in (Ellipsis, None) or isinstance(node_t, str)):
            raise TypeError
        elif isinstance(node_t, str) and ' ' in node_t:
            raise ValueError
        if isinstance(node_t, str):
            if node_t not in self.node_types:
                raise ValueError("Node type NOT exists")
            else:
                data: _typing.Optional[torch.Tensor] = (
                    self.__nodes_data[node_t].get(data_key)
                )
                if data is not None:
                    return data
                else:
                    raise KeyError(
                        f"Data with key [{data_key}] NOT exists "
                        f"for nodes with specific type [{node_t}]"
                    )
        else:
            if len(self.node_types) == 0:
                raise RuntimeError("Unable to get data from empty graph")
            elif len(self.node_types) == 1:
                __node_t: str = tuple(self.node_types)[0]
                __optional_data: _typing.Optional[torch.Tensor] = (
                    self.__nodes_data[__node_t].get(data_key)
                )
                if __optional_data is not None:
                    return __optional_data
                else:
                    raise KeyError(f"Data with key [{data_key}] NOT exists")
            else:
                __result: _typing.Dict[str, torch.Tensor] = {}
                for __node_t, __nodes_data in self.__nodes_data.items():
                    __optional_data: _typing.Optional[torch.Tensor] = (
                        __nodes_data.get(data_key)
                    )
                    if (
                            __optional_data is not None and
                            isinstance(__optional_data, torch.Tensor)
                    ):
                        __result[__node_t] = __optional_data
                if len(__result):
                    return __result
                else:
                    raise KeyError(f"Data with key [{data_key}] NOT exists")

    def get_data(
            self, node_t: _typing.Optional[str] = ...,
            data_key: _typing.Optional[str] = ...
    ) -> _typing.Union[torch.Tensor, _typing.Mapping[str, torch.Tensor]]:
        if not (node_t in (Ellipsis, None) or isinstance(node_t, str)):
            raise TypeError
        elif isinstance(node_t, str) and ' ' in node_t:
            raise ValueError
        if not (data_key in (Ellipsis, None) or isinstance(data_key, str)):
            raise TypeError
        elif isinstance(data_key, str) and ' ' in data_key:
            raise ValueError
        if isinstance(node_t, str):
            return self.__get_data_for_specific_node_type(node_t, data_key)
        elif node_t in (Ellipsis, None) and isinstance(data_key, str):
            return self.__get_data_for_specific_data_key(data_key)
        elif node_t in (Ellipsis, None) and data_key in (Ellipsis, None):
            if len(self.node_types) == 1:
                __node_t: str = tuple(self.node_types)[0]
                return self.__get_data_for_specific_node_type(__node_t)
            else:
                raise TypeError(
                    "Unable to determine node type automatically, "
                    "possible cause is that the graph contains heterogeneous nodes or is empty, "
                    "node type must be specified for graph containing heterogeneous nodes."
                )

    def delete_data(
            self, node_t: _typing.Optional[str], data_key: str
    ) -> _HeterogeneousNodesContainer:
        if not (node_t in (Ellipsis, None) or isinstance(node_t, str)):
            raise TypeError
        elif node_t in (Ellipsis, None):
            if len(self.node_types) == 1:
                __node_t: str = tuple(self.node_types)[0]
            else:
                raise TypeError(
                    "Unable to determine node type automatically, "
                    "possible cause is that the graph contains heterogeneous nodes or is empty, "
                    "node type must be specified for graph containing heterogeneous nodes."
                )
        elif isinstance(node_t, str):
            if node_t in self.node_types:
                __node_t: str = node_t
            else:
                raise ValueError("node type NOT exists")
        else:
            raise TypeError
        if not isinstance(data_key, str):
            raise TypeError
        elif data_key not in self.__nodes_data.get(__node_t):
            raise KeyError(
                f"Data with key [{data_key}] NOT exists for nodes with type [{__node_t}]"
            )
        else:
            self.__nodes_data[__node_t].__delitem__(data_key)
            if len(self.__nodes_data.get(__node_t)) == 0:
                del self.__nodes_data[__node_t]
        return self


class _TypedNodeDataView(_typing.MutableMapping[str, torch.Tensor]):
    def __init__(
            self, heterogeneous_nodes_container: _HeterogeneousNodesContainer,
            node_type: _typing.Optional[str]
    ):
        if not isinstance(heterogeneous_nodes_container, _HeterogeneousNodesContainer):
            raise TypeError
        else:
            self._heterogeneous_nodes_container: _HeterogeneousNodesContainer = (
                heterogeneous_nodes_container
            )
        if not (isinstance(node_type, str) or node_type in (Ellipsis, None)):
            raise TypeError
        elif isinstance(node_type, str):
            if node_type not in self._heterogeneous_nodes_container.node_types:
                raise ValueError("Invalid node type")
        self.__node_t: _typing.Optional[str] = node_type

    def __getitem__(self, data_key: str) -> torch.Tensor:
        return self._heterogeneous_nodes_container.get_data(self.__node_t, data_key)

    def __setitem__(self, data_key: str, value: torch.Tensor):
        self._heterogeneous_nodes_container.set_data(self.__node_t, data_key, value)

    def __delitem__(self, data_key: str) -> None:
        self._heterogeneous_nodes_container.delete_data(self.__node_t, data_key)

    def __len__(self) -> int:
        return len(self._heterogeneous_nodes_container.get_data(self.__node_t))

    def __iter__(self) -> _typing.Iterator[str]:
        return iter(self._heterogeneous_nodes_container.get_data(self.__node_t))


class _TypedNodeView:
    def __init__(
            self, nodes_container: _HeterogeneousNodesContainer,
            node_t: _typing.Optional[str]
    ):
        self._heterogeneous_nodes_container: _HeterogeneousNodesContainer = nodes_container
        self.__node_t: _typing.Optional[str] = node_t

    @property
    def data(self) -> _TypedNodeDataView:
        return _TypedNodeDataView(self._heterogeneous_nodes_container, self.__node_t)

    @data.setter
    def data(self, nodes_data: _typing.Mapping[str, torch.Tensor]):
        self._heterogeneous_nodes_container.reset_nodes(self.__node_t, nodes_data)


class _IntegralNodeView(_TypedNodeView, _typing.Iterable[str]):
    def __init__(self, nodes_container: _HeterogeneousNodesContainer):
        super(_IntegralNodeView, self).__init__(nodes_container, ...)

    def __getitem__(self, node_type: _typing.Optional[str]) -> _TypedNodeView:
        return _TypedNodeView(self._heterogeneous_nodes_container, node_type)

    def __setitem__(
            self, node_t: _typing.Optional[str],
            nodes_data: _typing.Mapping[str, torch.Tensor]
    ) -> None:
        self._heterogeneous_nodes_container.reset_nodes(node_t, nodes_data)

    def __delitem__(self, node_t: _typing.Optional[str]):
        self._heterogeneous_nodes_container.remove_nodes(node_t)

    def __iter__(self) -> _typing.Iterator[str]:
        return iter(self._heterogeneous_nodes_container.node_types)

    @property
    def is_homogeneous(self) -> bool:
        return len(self._heterogeneous_nodes_container.node_types) <= 1


class _HomogeneousEdgesContainer:
    @property
    def connections(self) -> torch.Tensor:
        raise NotImplementedError

    @property
    def data_keys(self) -> _typing.Iterable[str]:
        raise NotImplementedError

    def get_data(
            self, data_key: _typing.Optional[str] = ...
    ) -> _typing.Union[torch.Tensor, _typing.Mapping[str, torch.Tensor]]:
        raise NotImplementedError

    def set_data(self, data_key: str, data: torch.Tensor):
        raise NotImplementedError

    def delete_data(self, data_key: str):
        raise NotImplementedError


class _HomogeneousEdgesContainerImplementation(_HomogeneousEdgesContainer):
    def __init__(
            self, edge_connections: torch.Tensor,
            data: _typing.Optional[_typing.Mapping[str, torch.Tensor]] = ...
    ):
        if not isinstance(edge_connections, torch.Tensor):
            raise TypeError
        if not (data in (Ellipsis, None) or isinstance(data, _typing.Mapping)):
            raise TypeError
        if not (
                edge_connections.dtype == torch.int64 and
                edge_connections.dim() == edge_connections.size(0) == 2
        ):
            raise ValueError
        self.__connections: torch.Tensor = edge_connections
        if not isinstance(data, _typing.Mapping):
            self.__data: _typing.MutableMapping[str, torch.Tensor] = {}
        else:
            for data_key, data_item in data.items():
                if not isinstance(data_key, str):
                    raise TypeError
                if not isinstance(data_item, torch.Tensor):
                    raise TypeError
                if ' ' in data_key:
                    raise ValueError
                if not data_item.dim() > 0:
                    raise ValueError
                if data_item.size(0) != self.__connections.size(1):
                    raise ValueError
            self.__data: _typing.MutableMapping[str, torch.Tensor] = dict(data)

    @property
    def connections(self) -> torch.Tensor:
        return self.__connections

    @property
    def data_keys(self) -> _typing.Iterable[str]:
        return self.__data.keys()

    def set_data(self, data_key: str, data: torch.Tensor) -> _HomogeneousEdgesContainer:
        if not isinstance(data_key, str):
            raise TypeError
        if not isinstance(data, torch.Tensor):
            raise TypeError
        if ' ' in data_key:
            raise ValueError
        if data.dim() == 0 or data.size(0) != self.__connections.size(1):
            raise ValueError
        self.__data[data_key] = data
        return self

    def get_data(
            self, data_key: _typing.Optional[str] = ...
    ) -> _typing.Union[torch.Tensor, _typing.Mapping[str, torch.Tensor]]:
        if not (data_key in (Ellipsis, None) or isinstance(data_key, str)):
            raise TypeError
        if isinstance(data_key, str):
            if ' ' in data_key:
                raise ValueError
            temp: _typing.Optional[torch.Tensor] = self.__data.get(data_key)
            if temp is None:
                raise KeyError(f"Data with key [{data_key}] NOT exists")
            else:
                return temp
        else:
            return dict(self.__data)

    def delete_data(self, data_key: str) -> _HomogeneousEdgesContainer:
        if not isinstance(data_key, str):
            raise TypeError
        if ' ' in data_key:
            raise ValueError
        try:
            del self.__data[data_key]
        finally:
            return self


class _CanonicalEdgeType:
    def __init__(self, source_node_type: str, relation_type: str, target_node_type: str):
        if not isinstance(source_node_type, str):
            raise TypeError
        elif ' ' in source_node_type:
            raise ValueError
        if not isinstance(relation_type, str):
            raise TypeError
        elif ' ' in relation_type:
            raise ValueError
        if not isinstance(target_node_type, str):
            raise TypeError
        elif ' ' in target_node_type:
            raise ValueError
        self.__source_node_type: str = source_node_type
        self.__relation_type: str = relation_type
        self.__destination_node_type: str = target_node_type

    @property
    def source_node_type(self) -> str:
        return self.__source_node_type

    @property
    def relation_type(self) -> str:
        return self.__relation_type

    @property
    def target_node_type(self) -> str:
        return self.__destination_node_type

    def __eq__(self, other):
        if not (isinstance(other, _CanonicalEdgeType) or isinstance(other, _typing.Tuple)):
            return False
        elif isinstance(other, _typing.Tuple):
            if not (
                    len(other) == 3 and all([(isinstance(t, str) and ' ' not in t) for t in other])
            ):
                raise TypeError
            return (
                    other[0] == self.source_node_type and
                    other[1] == self.relation_type and
                    other[2] == self.target_node_type
            )
        elif isinstance(other, _CanonicalEdgeType):
            return (
                    other.source_node_type == self.source_node_type and
                    other.relation_type == self.relation_type and
                    other.target_node_type == self.target_node_type
            )


class _HeterogeneousEdgesAggregation(
    _typing.MutableMapping[
        _typing.Union[str, _typing.Tuple[str, str, str], _CanonicalEdgeType],
        _HomogeneousEdgesContainer
    ]
):
    def __setitem__(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType],
            edges: _typing.Union[_HomogeneousEdgesContainer, torch.LongTensor]
    ) -> None:
        self._set_edges(edge_t, edges)

    def __delitem__(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType]
    ) -> None:
        self._delete_edges(edge_t)

    def __getitem__(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType] = ...
    ) -> _HomogeneousEdgesContainer:
        return self._get_edges(edge_t)

    def __len__(self) -> int:
        return len(list(self._edge_types))

    def __iter__(self) -> _typing.Iterator[_CanonicalEdgeType]:
        return iter(self._edge_types)

    @property
    def _edge_types(self) -> _typing.Iterable[_CanonicalEdgeType]:
        raise NotImplementedError

    def _get_edges(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType] = ...
    ) -> _HomogeneousEdgesContainer:
        raise NotImplementedError

    def _set_edges(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType],
            edges: _typing.Union[_HomogeneousEdgesContainer, torch.LongTensor]
    ):
        raise NotImplementedError

    def _delete_edges(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType]
    ) -> None:
        raise NotImplementedError


class _HeterogeneousEdgesAggregationImplementation(_HeterogeneousEdgesAggregation):
    def __init__(self):
        self.__heterogeneous_edges_data_frame: pd.DataFrame = pd.DataFrame(
            columns=('s', 'r', 't', 'edges'),
        )

    @property
    def _edge_types(self) -> _typing.Iterable[_CanonicalEdgeType]:
        return [
            _CanonicalEdgeType(getattr(row_tuple, 's'), getattr(row_tuple, 'r'), getattr(row_tuple, 't'))
            for row_tuple in self.__heterogeneous_edges_data_frame.itertuples(False, name="Edge")
        ]

    def _get_edges(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType] = ...
    ) -> _HomogeneousEdgesContainer:
        if edge_t in (Ellipsis, None):
            if len(self.__heterogeneous_edges_data_frame) == 1:
                return self.__heterogeneous_edges_data_frame.iloc[0]['edges']
            else:
                raise RuntimeError  # Undetermined
        elif isinstance(edge_t, str):
            if ' ' in edge_t:
                raise ValueError
            if len(
                    self.__heterogeneous_edges_data_frame.loc[
                        self.__heterogeneous_edges_data_frame['r'] == edge_t
                    ]
            ) != 1:
                raise ValueError  # Unable to determine
            else:
                temp: _HomogeneousEdgesContainer = self.__heterogeneous_edges_data_frame.loc[
                    self.__heterogeneous_edges_data_frame['r'] == edge_t, 'edges'
                ]
                if not isinstance(temp, _HomogeneousEdgesContainer):
                    raise RuntimeError
                else:
                    return temp
        elif isinstance(edge_t, _typing.Tuple) or isinstance(edge_t, _CanonicalEdgeType):
            if isinstance(edge_t, _typing.Tuple) and not (
                    len(edge_t) == 3 and
                    isinstance(edge_t[0], str) and
                    isinstance(edge_t[1], str) and
                    isinstance(edge_t[2], str) and
                    ' ' not in edge_t[0] and ' ' not in edge_t[1] and ' ' not in edge_t[2]
            ):
                raise TypeError("Illegal canonical edge type")
            __edge_t: _typing.Tuple[str, str, str] = (
                (edge_t.source_node_type, edge_t.relation_type, edge_t.target_node_type)
                if isinstance(edge_t, _CanonicalEdgeType) else edge_t
            )
            partial_data_frame: pd.DataFrame = self.__heterogeneous_edges_data_frame.loc[
                (self.__heterogeneous_edges_data_frame['s'] == __edge_t[0]) &
                (self.__heterogeneous_edges_data_frame['r'] == __edge_t[1]) &
                (self.__heterogeneous_edges_data_frame['t'] == __edge_t[2])
                ]
            if len(partial_data_frame) == 0:
                raise ValueError
            elif len(partial_data_frame) == 1:
                temp: _HomogeneousEdgesContainer = partial_data_frame.iloc[0]['edges']
                if not isinstance(temp, _HomogeneousEdgesContainer):
                    raise RuntimeError
                else:
                    return temp
            else:
                raise RuntimeError

    def _set_edges(
            self,
            edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType],
            edges: _typing.Union[_HomogeneousEdgesContainer, torch.LongTensor]
    ):
        if not (isinstance(edges, _HomogeneousEdgesContainer) or isinstance(edges, torch.Tensor)):
            raise TypeError
        if edge_t in (Ellipsis, None):
            if len(self.__heterogeneous_edges_data_frame) == 0:
                self.__heterogeneous_edges_data_frame: pd.DataFrame = (
                    self.__heterogeneous_edges_data_frame.append(
                        pd.DataFrame(
                            {
                                's': [''], 'r': [''], 't': [''],
                                'edges': [
                                    edges if isinstance(edges, _HomogeneousEdgesContainer)
                                    else _HomogeneousEdgesContainerImplementation(edges)
                                ]
                            }
                        )
                    )
                )
            elif len(self.__heterogeneous_edges_data_frame) == 1:
                self.__heterogeneous_edges_data_frame.iloc[0]['edges'] = (
                    edges if isinstance(edges, _HomogeneousEdgesContainer)
                    else _HomogeneousEdgesContainerImplementation(edges)
                )
            else:
                raise RuntimeError  # todo: Unable to determine error
        elif isinstance(edge_t, str):
            if ' ' in edge_t:
                raise ValueError
            if len(
                    self.__heterogeneous_edges_data_frame.loc[
                        self.__heterogeneous_edges_data_frame['r'] == edge_t
                    ]
            ) == 1:
                self.__heterogeneous_edges_data_frame.loc[
                    self.__heterogeneous_edges_data_frame['r'] == edge_t, 'edges'
                ] = (
                    edges if isinstance(edges, _HomogeneousEdgesContainer)
                    else _HomogeneousEdgesContainerImplementation(edges)
                )
            else:
                raise RuntimeError
        elif isinstance(edge_t, _typing.Tuple) or isinstance(edge_t, _CanonicalEdgeType):
            if isinstance(edge_t, _typing.Tuple) and not (
                    len(edge_t) == 3 and
                    isinstance(edge_t[0], str) and
                    isinstance(edge_t[1], str) and
                    isinstance(edge_t[2], str) and
                    ' ' not in edge_t[0] and ' ' not in edge_t[1] and ' ' not in edge_t[2]
            ):
                raise TypeError("Illegal canonical edge type")
            __edge_t: _typing.Tuple[str, str, str] = (
                (edge_t.source_node_type, edge_t.relation_type, edge_t.target_node_type)
                if isinstance(edge_t, _CanonicalEdgeType) else edge_t
            )
            if len(
                    self.__heterogeneous_edges_data_frame.loc[
                        (self.__heterogeneous_edges_data_frame['s'] == __edge_t[0]) &
                        (self.__heterogeneous_edges_data_frame['r'] == __edge_t[1]) &
                        (self.__heterogeneous_edges_data_frame['t'] == __edge_t[2])
                    ]
            ) == 0:
                self.__heterogeneous_edges_data_frame: pd.DataFrame = (
                    self.__heterogeneous_edges_data_frame.append(
                        pd.DataFrame(
                            {
                                's': [__edge_t[0]],
                                'r': [__edge_t[1]],
                                't': [__edge_t[2]],
                                'edges': [
                                    edges if isinstance(edges, _HomogeneousEdgesContainer)
                                    else _HomogeneousEdgesContainerImplementation(edges)
                                ]
                            }
                        )
                    )
                )
            elif len(
                    self.__heterogeneous_edges_data_frame.loc[
                        (self.__heterogeneous_edges_data_frame['s'] == __edge_t[0]) &
                        (self.__heterogeneous_edges_data_frame['r'] == __edge_t[1]) &
                        (self.__heterogeneous_edges_data_frame['t'] == __edge_t[2])
                    ]
            ) == 1:
                self.__heterogeneous_edges_data_frame.loc[
                    (self.__heterogeneous_edges_data_frame['s'] == __edge_t[0]) &
                    (self.__heterogeneous_edges_data_frame['r'] == __edge_t[1]) &
                    (self.__heterogeneous_edges_data_frame['t'] == __edge_t[2]),
                    'edges'
                ] = (
                    edges if isinstance(edges, _HomogeneousEdgesContainer)
                    else _HomogeneousEdgesContainerImplementation(edges)
                )
            else:
                raise RuntimeError  # todo: Unable to determine error
        else:
            raise RuntimeError

    def _delete_edges(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType] = ...
    ) -> None:
        if edge_t in (Ellipsis, None):
            if len(self.__heterogeneous_edges_data_frame) == 1:
                self.__heterogeneous_edges_data_frame.drop(
                    self.__heterogeneous_edges_data_frame.index[0], inplace=True
                )
            elif len(self.__heterogeneous_edges_data_frame) > 1:
                raise ValueError("Edge Type must be specified for graph containing heterogeneous edges")
        raise NotImplementedError  # todo: Complete this function


class _HomogeneousEdgesDataView(_typing.MutableMapping[str, torch.Tensor]):
    def __init__(self, homogeneous_edges_container: _HomogeneousEdgesContainer):
        if not isinstance(homogeneous_edges_container, _HomogeneousEdgesContainer):
            raise TypeError
        self._homogeneous_edges_container: _HomogeneousEdgesContainer = homogeneous_edges_container

    def __getitem__(self, data_key: str) -> torch.Tensor:
        if not isinstance(data_key, str):
            raise TypeError
        if ' ' in data_key:
            raise ValueError
        return self._homogeneous_edges_container.get_data(data_key)

    def __setitem__(self, data_key: str, data: torch.Tensor):
        if not isinstance(data_key, str):
            raise TypeError
        elif ' ' in data_key:
            raise ValueError
        if not isinstance(data, torch.Tensor):
            raise TypeError
        elif not data.dim() > 0:
            raise ValueError
        self._homogeneous_edges_container.set_data(data_key, data)

    def __delitem__(self, data_key: str):
        if not isinstance(data_key, str):
            raise TypeError
        elif ' ' in data_key:
            raise ValueError
        self._homogeneous_edges_container.delete_data(data_key)

    def __len__(self):
        return len(list(self._homogeneous_edges_container.data_keys))

    def __iter__(self) -> _typing.Iterator[str]:
        return iter(self._homogeneous_edges_container.data_keys)


class _SpecificTypedHomogeneousEdgesView:
    def __init__(self, homogeneous_edges_container: _HomogeneousEdgesContainer):
        if not isinstance(homogeneous_edges_container, _HomogeneousEdgesContainer):
            raise TypeError
        self._homogeneous_edges_container: _HomogeneousEdgesContainer = homogeneous_edges_container

    @property
    def connections(self) -> torch.Tensor:
        return self._homogeneous_edges_container.connections

    @property
    def data(self) -> _HomogeneousEdgesDataView:
        return _HomogeneousEdgesDataView(self._homogeneous_edges_container)


class _HeterogeneousEdgesView(_typing.Collection[_CanonicalEdgeType]):
    def __init__(self, _heterogeneous_edges_aggregation: _HeterogeneousEdgesAggregation):
        if not isinstance(_heterogeneous_edges_aggregation, _HeterogeneousEdgesAggregation):
            raise TypeError
        self._heterogeneous_edges_aggregation: _HeterogeneousEdgesAggregation = (
            _heterogeneous_edges_aggregation
        )

    def __getitem__(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType]
    ) -> _SpecificTypedHomogeneousEdgesView:
        return _SpecificTypedHomogeneousEdgesView(self._heterogeneous_edges_aggregation[edge_t])

    def __setitem__(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType],
            edges: _typing.Union[_HomogeneousEdgesContainer, torch.LongTensor]
    ):
        self._heterogeneous_edges_aggregation[edge_t] = edges

    def __delitem__(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str], _CanonicalEdgeType]
    ):
        del self._heterogeneous_edges_aggregation[edge_t]

    def __len__(self) -> int:
        return len(self._heterogeneous_edges_aggregation)

    def __iter__(self) -> _typing.Iterator[_CanonicalEdgeType]:
        return iter(self._heterogeneous_edges_aggregation)

    def __contains__(self, edge_type: _typing.Union[str, _typing.Tuple[str, str, str], _CanonicalEdgeType]) -> bool:
        if isinstance(edge_type, str):
            if ' ' in edge_type:
                raise ValueError
            else:
                for existing_edge_type in self:
                    if existing_edge_type.relation_type == edge_type:
                        return True
                return False
        elif isinstance(edge_type, _typing.Tuple):
            if not (
                    len(edge_type) == 3 and
                    all([(isinstance(t, str) and ' ' not in t) for t in edge_type])
            ):
                raise TypeError
            else:
                for existing_edge_type in self:
                    if existing_edge_type.__eq__(edge_type):
                        return True
                return False
        elif isinstance(edge_type, _CanonicalEdgeType):
            for existing_edge_type in self:
                if existing_edge_type == edge_type:
                    return True
            return False
        else:
            raise TypeError

    @property
    def connections(self) -> torch.Tensor:
        return self[...].connections

    @property
    def data(self) -> _HomogeneousEdgesDataView:
        return self[...].data

    @property
    def is_homogeneous(self) -> bool:
        return len(self) <= 1

    def set(
            self, edge_t: _typing.Union[None, str, _typing.Tuple[str, str, str]],
            connections: torch.LongTensor, data: _typing.Optional[_typing.Mapping[str, torch.Tensor]] = ...
    ):
        self[edge_t] = _HomogeneousEdgesContainerImplementation(connections, data)


class _StaticGraphDataContainer(_typing.MutableMapping[str, torch.Tensor]):
    def __setitem__(self, data_key: str, data: torch.Tensor) -> None:
        raise NotImplementedError

    def __delitem__(self, data_key: str) -> None:
        raise NotImplementedError

    def __getitem__(self, data_key: str) -> torch.Tensor:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError

    def __iter__(self) -> _typing.Iterator[str]:
        raise NotImplementedError


class _StaticGraphDataAggregation(_StaticGraphDataContainer):
    def __init__(
            self, graph_data: _typing.Optional[_typing.Mapping[str, torch.Tensor]] = ...
    ):
        self.__data: _typing.MutableMapping[str, torch.Tensor] = (
            dict(graph_data) if isinstance(graph_data, _typing.Mapping)
            else {}
        )

    def __setitem__(self, data_key: str, data: torch.Tensor) -> None:
        self.__data[data_key] = data

    def __delitem__(self, data_key: str) -> None:
        del self.__data[data_key]

    def __getitem__(self, data_key: str) -> torch.Tensor:
        return self.__data[data_key]

    def __len__(self) -> int:
        return len(self.__data)

    def __iter__(self) -> _typing.Iterator[str]:
        return iter(self.__data)


class _StaticGraphDataView(_typing.MutableMapping[str, torch.Tensor]):
    def __init__(self, graph_data_container: _StaticGraphDataContainer):
        self.__graph_data_container: _StaticGraphDataContainer = (
            graph_data_container
        )

    def __setitem__(self, data_key: str, data: torch.Tensor) -> None:
        self.__graph_data_container[data_key] = data

    def __delitem__(self, data_key: str) -> None:
        del self.__graph_data_container[data_key]

    def __getitem__(self, data_key: str) -> torch.Tensor:
        return self.__graph_data_container[data_key]

    def __len__(self) -> int:
        return len(self.__graph_data_container)

    def __iter__(self) -> _typing.Iterator[str]:
        return iter(self.__graph_data_container)


class GeneralStaticGraph:
    @property
    def nodes(self) -> _IntegralNodeView:
        raise NotImplementedError

    @property
    def edges(self) -> _HeterogeneousEdgesView:
        raise NotImplementedError

    @property
    def data(self) -> _StaticGraphDataView:
        raise NotImplementedError


class GeneralStaticGraphImplementation(GeneralStaticGraph):
    def __init__(
            self, _heterogeneous_nodes_container: _typing.Optional[_HeterogeneousNodesContainer] = ...,
            _heterogeneous_edges_aggregation: _typing.Optional[_HeterogeneousEdgesAggregation] = ...,
            graph_data_container: _typing.Optional[_StaticGraphDataContainer] = ...
    ):
        self._static_graph_data_container: _StaticGraphDataContainer = (
            graph_data_container
            if isinstance(graph_data_container, _StaticGraphDataContainer)
            else _StaticGraphDataAggregation()
        )
        self._heterogeneous_nodes_container: _HeterogeneousNodesContainer = (
            _heterogeneous_nodes_container
            if isinstance(_heterogeneous_nodes_container, _HeterogeneousNodesContainer)
            else _HeterogeneousNodesContainerImplementation()
        )
        self._heterogeneous_edges_aggregation: _HeterogeneousEdgesAggregation = (
            _heterogeneous_edges_aggregation
            if isinstance(_heterogeneous_edges_aggregation, _HeterogeneousEdgesAggregation)
            else _HeterogeneousEdgesAggregationImplementation()
        )

    @property
    def nodes(self) -> _IntegralNodeView:
        return _IntegralNodeView(self._heterogeneous_nodes_container)

    @property
    def edges(self) -> _HeterogeneousEdgesView:
        return _HeterogeneousEdgesView(self._heterogeneous_edges_aggregation)

    @property
    def data(self) -> _StaticGraphDataView:
        return _StaticGraphDataView(self._static_graph_data_container)


class GeneralStaticGraphGenerator:
    @classmethod
    def create_homogeneous_static_graph(
            cls, nodes_data: _typing.Mapping[str, torch.Tensor],
            edges_connections: torch.Tensor,
            edges_data: _typing.Optional[_typing.Mapping[str, torch.Tensor]] = ...,
            graph_data: _typing.Optional[_typing.Mapping[str, torch.Tensor]] = ...
    ) -> GeneralStaticGraph:
        _heterogeneous_nodes_container: _HeterogeneousNodesContainer = (
            _HeterogeneousNodesContainerImplementation({'': nodes_data})
        )
        _heterogeneous_edges_aggregation: _HeterogeneousEdgesAggregation = (
            _HeterogeneousEdgesAggregationImplementation()
        )
        _heterogeneous_edges_aggregation[('', '', '')] = (
            _HomogeneousEdgesContainerImplementation(
                edges_connections, edges_data
            )
        )
        return GeneralStaticGraphImplementation(
            _heterogeneous_nodes_container,
            _heterogeneous_edges_aggregation,
            _StaticGraphDataAggregation(graph_data)
        )
