import dgl
import pytest
import torch
from dgl import graphbolt as gb
from torch.testing import assert_close


@pytest.mark.parametrize("batch_size", [1, 4])
@pytest.mark.parametrize("shuffle", [True, False])
@pytest.mark.parametrize("drop_last", [True, False])
def test_ItemSet_node_edge_ids(batch_size, shuffle, drop_last):
    # Node or edge IDs.
    num_ids = 103
    item_set = gb.ItemSet(torch.arange(0, num_ids))
    minibatch_sampler = gb.MinibatchSampler(
        item_set, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last
    )
    minibatch_ids = []
    for i, minibatch in enumerate(minibatch_sampler):
        is_last = (i + 1) * batch_size >= num_ids
        if not is_last or num_ids % batch_size == 0:
            assert len(minibatch) == batch_size
        else:
            if not drop_last:
                assert len(minibatch) == num_ids % batch_size
            else:
                assert False
        minibatch_ids.append(minibatch)
    minibatch_ids = torch.cat(minibatch_ids)
    assert torch.all(minibatch_ids[:-1] <= minibatch_ids[1:]) is not shuffle


@pytest.mark.parametrize("batch_size", [1, 4])
@pytest.mark.parametrize("shuffle", [True, False])
@pytest.mark.parametrize("drop_last", [True, False])
def test_ItemSet_graphs(batch_size, shuffle, drop_last):
    # Graphs.
    num_graphs = 103
    num_nodes = 10
    num_edges = 20
    graphs = [
        dgl.rand_graph(num_nodes * (i + 1), num_edges * (i + 1))
        for i in range(num_graphs)
    ]
    item_set = gb.ItemSet(graphs)
    minibatch_sampler = gb.MinibatchSampler(
        item_set, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last
    )
    minibatch_num_nodes = []
    minibatch_num_edges = []
    for i, minibatch in enumerate(minibatch_sampler):
        is_last = (i + 1) * batch_size >= num_graphs
        if not is_last or num_graphs % batch_size == 0:
            assert minibatch.batch_size == batch_size
        else:
            if not drop_last:
                assert minibatch.batch_size == num_graphs % batch_size
            else:
                assert False
        minibatch_num_nodes.append(minibatch.batch_num_nodes())
        minibatch_num_edges.append(minibatch.batch_num_edges())
    minibatch_num_nodes = torch.cat(minibatch_num_nodes)
    minibatch_num_edges = torch.cat(minibatch_num_edges)
    assert (
        torch.all(minibatch_num_nodes[:-1] <= minibatch_num_nodes[1:])
        is not shuffle
    )
    assert (
        torch.all(minibatch_num_edges[:-1] <= minibatch_num_edges[1:])
        is not shuffle
    )


@pytest.mark.parametrize("batch_size", [1, 4])
@pytest.mark.parametrize("shuffle", [True, False])
@pytest.mark.parametrize("drop_last", [True, False])
def test_ItemSet_node_pairs(batch_size, shuffle, drop_last):
    # Node pairs.
    num_ids = 103
    node_pairs = (torch.arange(0, num_ids), torch.arange(num_ids, num_ids * 2))
    item_set = gb.ItemSet(node_pairs)
    minibatch_sampler = gb.MinibatchSampler(
        item_set, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last
    )
    src_ids = []
    dst_ids = []
    for i, (src, dst) in enumerate(minibatch_sampler):
        is_last = (i + 1) * batch_size >= num_ids
        if not is_last or num_ids % batch_size == 0:
            expected_batch_size = batch_size
        else:
            if not drop_last:
                expected_batch_size = num_ids % batch_size
            else:
                assert False
        assert len(src) == expected_batch_size
        assert len(dst) == expected_batch_size
        # Verify src and dst IDs match.
        assert torch.equal(src + num_ids, dst)
        # Archive batch.
        src_ids.append(src)
        dst_ids.append(dst)
    src_ids = torch.cat(src_ids)
    dst_ids = torch.cat(dst_ids)
    assert torch.all(src_ids[:-1] <= src_ids[1:]) is not shuffle
    assert torch.all(dst_ids[:-1] <= dst_ids[1:]) is not shuffle


@pytest.mark.parametrize("batch_size", [1, 4])
@pytest.mark.parametrize("shuffle", [True, False])
@pytest.mark.parametrize("drop_last", [True, False])
def test_ItemSet_node_pairs_labels(batch_size, shuffle, drop_last):
    # Node pairs and labels
    num_ids = 103
    node_pairs = (torch.arange(0, num_ids), torch.arange(num_ids, num_ids * 2))
    labels = torch.arange(0, num_ids)
    item_set = gb.ItemSet((node_pairs[0], node_pairs[1], labels))
    minibatch_sampler = gb.MinibatchSampler(
        item_set, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last
    )
    src_ids = []
    dst_ids = []
    labels = []
    for i, (src, dst, label) in enumerate(minibatch_sampler):
        is_last = (i + 1) * batch_size >= num_ids
        if not is_last or num_ids % batch_size == 0:
            expected_batch_size = batch_size
        else:
            if not drop_last:
                expected_batch_size = num_ids % batch_size
            else:
                assert False
        assert len(src) == expected_batch_size
        assert len(dst) == expected_batch_size
        assert len(label) == expected_batch_size
        # Verify src/dst IDs and labels match.
        assert torch.equal(src + num_ids, dst)
        assert torch.equal(src, label)
        # Archive batch.
        src_ids.append(src)
        dst_ids.append(dst)
        labels.append(label)
    src_ids = torch.cat(src_ids)
    dst_ids = torch.cat(dst_ids)
    labels = torch.cat(labels)
    assert torch.all(src_ids[:-1] <= src_ids[1:]) is not shuffle
    assert torch.all(dst_ids[:-1] <= dst_ids[1:]) is not shuffle
    assert torch.all(labels[:-1] <= labels[1:]) is not shuffle


@pytest.mark.parametrize("batch_size", [1, 4])
@pytest.mark.parametrize("shuffle", [True, False])
@pytest.mark.parametrize("drop_last", [True, False])
def test_ItemSet_head_tail_neg_tails(batch_size, shuffle, drop_last):
    # Head, tail and negative tails.
    num_ids = 103
    num_negs = 2
    heads = torch.arange(0, num_ids)
    tails = torch.arange(num_ids, num_ids * 2)
    neg_tails = torch.stack((heads + 1, heads + 2), dim=-1)
    item_set = gb.ItemSet((heads, tails, neg_tails))
    for i, (head, tail, negs) in enumerate(item_set):
        assert heads[i] == head
        assert tails[i] == tail
        assert torch.equal(neg_tails[i], negs)
    minibatch_sampler = gb.MinibatchSampler(
        item_set, batch_size=batch_size, shuffle=shuffle, drop_last=drop_last
    )
    head_ids = []
    tail_ids = []
    negs_ids = []
    for i, (head, tail, negs) in enumerate(minibatch_sampler):
        is_last = (i + 1) * batch_size >= num_ids
        if not is_last or num_ids % batch_size == 0:
            expected_batch_size = batch_size
        else:
            if not drop_last:
                expected_batch_size = num_ids % batch_size
            else:
                assert False
        assert len(head) == expected_batch_size
        assert len(tail) == expected_batch_size
        assert negs.dim() == 2
        assert negs.shape[0] == expected_batch_size
        assert negs.shape[1] == num_negs
        # Verify head/tail and negatie tails match.
        assert torch.equal(head + num_ids, tail)
        assert torch.equal(head + 1, negs[:, 0])
        assert torch.equal(head + 2, negs[:, 1])
        # Archive batch.
        head_ids.append(head)
        tail_ids.append(tail)
        negs_ids.append(negs)
    head_ids = torch.cat(head_ids)
    tail_ids = torch.cat(tail_ids)
    negs_ids = torch.cat(negs_ids)
    assert torch.all(head_ids[:-1] <= head_ids[1:]) is not shuffle
    assert torch.all(tail_ids[:-1] <= tail_ids[1:]) is not shuffle
    assert torch.all(negs_ids[:-1, 0] <= negs_ids[1:, 0]) is not shuffle
    assert torch.all(negs_ids[:-1, 1] <= negs_ids[1:, 1]) is not shuffle


def test_append_with_other_datapipes():
    num_ids = 100
    batch_size = 4
    item_set = gb.ItemSet(torch.arange(0, num_ids))
    data_pipe = gb.MinibatchSampler(item_set, batch_size)
    # torchdata.datapipes.iter.Enumerator
    data_pipe = data_pipe.enumerate()
    for i, (idx, data) in enumerate(data_pipe):
        assert i == idx
        assert len(data) == batch_size