from datautil.dependency import Dependency
from typing import List


# 计算F1值
def calc_f1(num_gold, num_pred, num_correct, eps=1e-10):
    f1 = (2. * num_correct) / (num_gold + num_pred + eps)
    return f1


# # 利用词性标签获取分词的边界bi（不考虑词性标签）
# # NR#b  NR#i  DEG#b VV#b  NN#b  NN#i  NN#i
# def cws_from_postag_bi(deps: List[Dependency]):
#     wds = []
#     one_wd = []
#     is_start = False
#     end_idx = len(deps) - 1
#     for i, dep in enumerate(deps):
#         if '#' not in dep.tag:
#             is_start = False
#             continue
#         tag_bound = dep.tag.split('#')[1]
#         one_wd.append(dep)
#         if tag_bound == 'b':
#             is_start = True
#             if i == end_idx or '#' not in deps[i+1].tag or deps[i+1].tag.split('#')[1] != 'i':
#                 wds.append(one_wd)
#                 one_wd = []
#                 is_start = False
#         elif tag_bound == 'i' and (i == end_idx or '#' not in deps[i+1].tag or deps[i+1].tag.split('#')[1] != 'i'):
#             if is_start:
#                 wds.append(one_wd)
#                 is_start = False
#             one_wd = []
#     return wds


def cws_from_tag(deps: List[Dependency]):
    wds = []
    one_wd = []
    is_start = False
    for i, dep in enumerate(deps):
        if '#' not in dep.tag and dep.tag not in 'bmes':
            is_start = False
            continue

        tag_bound = dep.tag.split('#')[1] if '#' in dep.tag else dep.tag
        if tag_bound == 's':
            wds.append([dep])
            is_start = False
        elif tag_bound == 'b':
            one_wd = [dep]
            is_start = True
        elif tag_bound == 'm':
            if is_start:
                one_wd.append(dep)
        elif tag_bound == 'e':
            if is_start:
                one_wd.append(dep)
                tags = ['#' in w.tag for w in one_wd]
                if all(tags) or not any(tags):
                    wds.append(one_wd)
                one_wd = []
            is_start = False
    return wds


def calc_seg_f1(gold_seg_lst: List, pred_seg_lst: List):
    start_idx = 1 if gold_seg_lst[0][0].id == 0 else 0

    num_gold = len(gold_seg_lst) - start_idx
    num_pred = len(pred_seg_lst) - start_idx  # 排除<root>

    gold_bounds, pred_bounds = [], []
    for gold_segs in gold_seg_lst[start_idx:]:
        if len(gold_segs) > 1:
            gold_bounds.append((gold_segs[0].id, gold_segs[-1].id))
        else:
            gold_bounds.append(gold_segs[0].id)

    for pred_segs in pred_seg_lst[start_idx:]:
        if len(pred_segs) > 1:
            pred_bounds.append((pred_segs[0].id, pred_segs[-1].id))
        else:
            pred_bounds.append(pred_segs[0].id)

    correct_pred = 0
    for gold in gold_bounds:
        if gold in pred_bounds:
            correct_pred += 1

    return num_gold, num_pred, correct_pred


def pos_tag_f1(gold_seg_lst: List, pred_seg_lst: List):
    start_idx = 1 if gold_seg_lst[0][0].id == 0 else 0
    num_gold, num_pred, correct_pred = 0, 0, 0

    num_gold = len(gold_seg_lst) - start_idx
    num_pred = len(pred_seg_lst) - start_idx

    for gold_seg in gold_seg_lst[start_idx:]:
        gold_span = (gold_seg[0].id, gold_seg[-1].id)
        for pred_seg in pred_seg_lst[start_idx:]:
            pred_span = (pred_seg[0].id, pred_seg[-1].id)
            if gold_span == pred_span:
                is_correct = True
                for pred_c, gold_c in zip(pred_seg, gold_seg):
                    if pred_c.tag != gold_c.tag:
                        is_correct = False
                        break
                if is_correct:
                    correct_pred += 1
                break

    return num_gold, num_pred, correct_pred


def parser_metric(gold_seg_lst: List, pred_seg_lst: List):
    # 不考虑标点符号
    ignore_tags = {'``', "''", ':', ',', '.', 'PU', 'PU#b', 'PU#i', 'PU#m', 'PU#e', 'PU#s'}

    start_idx = 1 if gold_seg_lst[0][0].id == 0 else 0

    nb_gold_arcs, nb_pred_arcs = 0, 0  # 实际的弧的数量，预测的弧的数量
    nb_arc_correct, nb_rel_correct = 0, 0

    for pred_seg in pred_seg_lst[start_idx:]:
        if pred_seg[0].tag in ignore_tags:
            continue
        nb_pred_arcs += 1

    for gold_seg in gold_seg_lst[start_idx:]:
        if gold_seg[0].tag in ignore_tags:
            continue
        nb_gold_arcs += 1

        head_idx = idx_head_in_wd(gold_seg)
        gold_span = (gold_seg[0].id, gold_seg[-1].id)
        for pred_seg in pred_seg_lst[start_idx:]:
            pred_span = (pred_seg[0].id, pred_seg[-1].id)
            if gold_span == pred_span:
                if gold_seg[head_idx].head == pred_seg[head_idx].head:
                    nb_arc_correct += 1
                    if gold_seg[head_idx].dep_rel == pred_seg[head_idx].dep_rel:
                        nb_rel_correct += 1
                break
    return nb_gold_arcs, nb_pred_arcs, nb_arc_correct, nb_rel_correct


def idx_head_in_wd(ch_deps: List[Dependency]):
    if len(ch_deps) == 1:
        return 0
    head_ch = -1
    b, e = ch_deps[0].id, ch_deps[-1].id
    for cd in ch_deps:
        if not (b <= cd.head <= e):
            head_ch = cd.id - b
            break
    return head_ch


from pprint import pprint
if __name__ == '__main__':
    # tag_lst = 'NR#b xxx NR#b xxx NR#m NR#m NR#e NR#m NR#m NR#e DEG#b NR#m NN#b NN#e tooy NR#s DEG#s NN#s NR#b NR#e NR#b'.split(' ')
    gold_tag_lst = 'NR#s PU#b PU#m PU#e NR#b NR#m NR#m NR#m NR#e NR#s DEG#s NR#b NR#m NR#e NR#e NR#s NR#s'.split(' ')
    pred_tag_lst = 'NR#s PU#b PU#e PU#e NR#b NR#m NR#m NR#m NR#e NR#s DEG#s NR#b NR#m NR#e NR#s NR#s NR#s'.split(' ')

    gold_deps = [Dependency(sid=i, form='OK', head=i, dep_rel='OK', tag=tag) for i, tag in enumerate(gold_tag_lst)]
    pred_deps = [Dependency(sid=i, form='OK', head=i, dep_rel='OK', tag=tag) for i, tag in enumerate(pred_tag_lst)]

    # wd_deps = cws_from_postag_bi(deps)
    gold_wd_deps = cws_from_tag(gold_deps)
    pred_wd_deps = cws_from_tag(pred_deps)
    print(gold_wd_deps)
    print(pred_wd_deps)
    a,b,c = pos_tag_f1(gold_wd_deps, pred_wd_deps)
    print(a, b, c)


