#!/usr/bin/env python3
"""
benchmark_kd_prune_patched.py

Patched version of the user's script with the following fixes/improvements applied:
 - Use --teacher-lr for teacher optimizer
 - Fixed dummy_loader construction (removed invalid generator expression)
 - Vectorized pairwise summed-diff computation
 - Device-aware regularizer and tensor initialization
 - Proper CUDA synchronization when measuring inference time
 - Correct ptflops input shape handling
 - Minor robustness improvements and comments

Behavior and pipeline are unchanged otherwise.
"""

import argparse
import copy
import os
import time
import json
from collections import defaultdict
from typing import Dict, List, Tuple

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.utils.prune as prune
from torchvision import transforms, datasets, models
import timm
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from ptflops import get_model_complexity_info
import pandas as pd
from tqdm import tqdm

# --------------------------
# Utilities
# --------------------------

def set_seed(seed=42):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def count_nonzero_params(model: torch.nn.Module) -> Tuple[int, int]:
    total = 0
    nonzero = 0
    for p in model.parameters():
        num = p.numel()
        total += num
        nonzero += (p.abs() > 1e-8).sum().item()
    return total, nonzero


def measure_inference_time(model, device, input_size=(3,224,224), n_runs=100, batch_size=1):
    model.eval()
    dummy = torch.randn((batch_size,)+input_size).to(device)
    # warmup
    with torch.no_grad():
        for _ in range(10):
            _ = model(dummy)
    times = []
    with torch.no_grad():
        for _ in range(n_runs):
            if device.type == 'cuda':
                torch.cuda.synchronize()
            t0 = time.time()
            _ = model(dummy)
            if device.type == 'cuda':
                torch.cuda.synchronize()
            t1 = time.time()
            times.append(t1 - t0)
    mean_ms = 1000.0 * float(np.mean(times))
    std_ms = 1000.0 * float(np.std(times))
    return mean_ms, std_ms


def compute_flops(model, input_res=(3,224,224)):
    # ptflops expects (C, H, W) tuple for input
    try:
        macs, params = get_model_complexity_info(model, (input_res[0], input_res[1], input_res[2]),
                                                as_strings=False, print_per_layer_stat=False)
        gflops = macs / 1e9
        return gflops, params
    except Exception as e:
        print("ptflops failed:", e)
        return None, None

# --------------------------
# Dataset loaders
# --------------------------

def make_dataloaders(data_dir, image_size=224, batch_size=32, num_workers=4):
    transform_train = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])
    transform_eval = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485,0.456,0.406], std=[0.229,0.224,0.225]),
    ])
    train_dir = os.path.join(data_dir, "train")
    val_dir   = os.path.join(data_dir, "val")
    test_dir  = os.path.join(data_dir, "test")
    train_ds = datasets.ImageFolder(train_dir, transform=transform_train)
    val_ds = datasets.ImageFolder(val_dir, transform=transform_eval)
    test_ds = datasets.ImageFolder(test_dir, transform=transform_eval)
    train_loader = torch.utils.data.DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers)
    val_loader   = torch.utils.data.DataLoader(val_ds,   batch_size=batch_size, shuffle=False, num_workers=num_workers)
    test_loader  = torch.utils.data.DataLoader(test_ds,  batch_size=batch_size, shuffle=False, num_workers=num_workers)
    return train_loader, val_loader, test_loader, len(train_ds.classes)

# --------------------------
# Training / Evaluation
# --------------------------

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    preds = []
    trues = []
    for x,y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * x.size(0)
        preds += out.argmax(dim=1).detach().cpu().tolist()
        trues += y.detach().cpu().tolist()
    loss = running_loss / len(loader.dataset)
    acc = accuracy_score(trues, preds) if len(trues) > 0 else 0.0
    f1 = f1_score(trues, preds, average='macro') if len(trues) > 0 else 0.0
    return loss, acc, f1


def eval_model(model, loader, device):
    model.eval()
    preds = []
    trues = []
    with torch.no_grad():
        for x,y in loader:
            x,y = x.to(device), y.to(device)
            out = model(x)
            preds += out.argmax(dim=1).cpu().tolist()
            trues += y.cpu().tolist()
    acc = accuracy_score(trues, preds) if len(trues) > 0 else 0.0
    f1 = f1_score(trues, preds, average='macro') if len(trues) > 0 else 0.0
    prec = precision_score(trues, preds, average='macro') if len(trues) > 0 else 0.0
    rec = recall_score(trues, preds, average='macro') if len(trues) > 0 else 0.0
    return {'acc': acc, 'f1': f1, 'prec': prec, 'rec': rec}

# --------------------------
# Knowledge Distillation loss
# --------------------------
class KDLoss(nn.Module):
    def __init__(self, temperature=10.0, alpha=0.7):
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha
        self.kl = nn.KLDivLoss(reduction='batchmean')
        self.ce = nn.CrossEntropyLoss()

    def forward(self, student_logits, teacher_logits, targets):
        T = self.temperature
        p_s = nn.functional.log_softmax(student_logits / T, dim=1)
        p_t = nn.functional.softmax(teacher_logits / T, dim=1)
        loss_soft = self.kl(p_s, p_t) * (T * T)
        loss_hard = self.ce(student_logits, targets)
        return self.alpha * loss_soft + (1.0 - self.alpha) * loss_hard


def train_kd_epoch(student, teacher, loader, kd_loss_fn, optimizer, device):
    student.train()
    teacher.eval()
    running_loss = 0.0
    preds, trues = [], []
    for x,y in loader:
        x,y = x.to(device), y.to(device)
        optimizer.zero_grad()
        s_logits = student(x)
        with torch.no_grad():
            t_logits = teacher(x)
        loss = kd_loss_fn(s_logits, t_logits, y)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * x.size(0)
        preds += s_logits.argmax(dim=1).cpu().tolist()
        trues += y.cpu().tolist()
    loss = running_loss / len(loader.dataset)
    acc = accuracy_score(trues, preds) if len(trues) > 0 else 0.0
    f1 = f1_score(trues, preds, average='macro') if len(trues) > 0 else 0.0
    return loss, acc, f1

# --------------------------
# HBFP-style bookkeeping: record per-filter L1 norms during training
# --------------------------

def get_conv_filters(module):
    # returns list of (module, name) for Conv2d modules
    convs = []
    for name, m in module.named_modules():
        if isinstance(m, nn.Conv2d):
            convs.append((m, name))
    return convs


def record_filter_l1_history(model, conv_hist: Dict[str, List[np.ndarray]]):
    # conv_hist: mapping layer_name -> list of per-epoch L1 arrays (num_filters,)
    for module, name in get_conv_filters(model):
        w = module.weight.detach().cpu().numpy()  # shape (out_ch, in_ch, k,k)
        l1_per_filter = np.sum(np.abs(w), axis=(1,2,3))
        if name not in conv_hist:
            conv_hist[name] = []
        conv_hist[name].append(l1_per_filter.copy())


def compute_pairwise_summed_diff_vec(conv_hist: Dict[str, List[np.ndarray]]):
    """
    Vectorized computation of D_{i,j} = sum_t |l1_i(t) - l1_j(t)|
    Returns selection dict: layer_name -> list of tuples (i,j,diff)
    """
    selection = {}
    for name, history in conv_hist.items():
        if len(history) == 0:
            continue
        arr = np.stack(history, axis=0)  # (epochs, num_filters)
        A = arr.T  # (num_filters, epochs)
        # compute pairwise L1 distances between rows of A
        # diffs[i,j] = sum_t |A[i,t] - A[j,t]|
        diffs = np.abs(A[:, None, :] - A[None, :, :]).sum(axis=2)  # (n, n)
        n = diffs.shape[0]
        pairs = []
        for i in range(n):
            for j in range(i+1, n):
                pairs.append((i, j, float(diffs[i, j])))
        selection[name] = pairs
    return selection

# --------------------------
# Pruning helpers
# --------------------------

def hbfp_select_pairs_and_prune(model, conv_hist, prune_fraction_per_layer=0.2, device='cpu', regularizer_lambda=1.0, optimize_epochs=3, lr=1e-4, dummy_loader=None):
    """
    HBFP-style selection + structured zeroing
    Returns (pruned_count, mapping)
    """
    selection = compute_pairwise_summed_diff_vec(conv_hist)
    to_prune = {}
    for module, name in get_conv_filters(model):
        if name not in selection:
            continue
        pairs = selection[name]
        if not pairs:
            continue
        pairs_sorted = sorted(pairs, key=lambda x: x[2])
        num_filters = module.weight.shape[0]
        prune_k = int(np.round(prune_fraction_per_layer * num_filters))
        selected_pairs = pairs_sorted[:max(0, prune_k)]
        last_epoch_arr = np.array(conv_hist[name][-1]) if len(conv_hist[name])>0 else np.zeros(num_filters)
        pr_indices = []
        for (i,j,d) in selected_pairs:
            if last_epoch_arr[i] < last_epoch_arr[j]:
                pr = i
            else:
                pr = j
            pr_indices.append(pr)
        to_prune[name] = sorted(list(set(pr_indices)))

    # Build selected_pairs_map for regularizer (keep both indices)
    selected_pairs_map = {}
    if regularizer_lambda > 0 and dummy_loader is not None:
        for module, name in get_conv_filters(model):
            if name not in selection:
                continue
            pairs_sorted = sorted(selection[name], key=lambda x: x[2])
            num_filters = module.weight.shape[0]
            prune_k = int(np.round(prune_fraction_per_layer * num_filters))
            sel_pairs = [(i,j) for (i,j,_) in pairs_sorted[:max(0, prune_k)]]
            if sel_pairs:
                selected_pairs_map[name] = sel_pairs

    # Optimization regularizer loop (device-aware)
    if selected_pairs_map:
        opt = optim.SGD(model.parameters(), lr=lr, momentum=0.9, weight_decay=1e-4)
        ce = nn.CrossEntropyLoss()
        model.train()
        for e in range(optimize_epochs):
            for xb, yb in dummy_loader:
                xb, yb = xb.to(device), yb.to(device)
                opt.zero_grad()
                logits = model(xb)
                loss = ce(logits, yb)
                reg = torch.tensor(0.0, device=device)
                for module, name in get_conv_filters(model):
                    if name not in selected_pairs_map:
                        continue
                    w = module.weight
                    l1 = w.abs().view(w.size(0), -1).sum(dim=1)
                    for (i,j) in selected_pairs_map[name]:
                        # ensure indices valid
                        if i < l1.size(0) and j < l1.size(0):
                            reg = reg + torch.abs(l1[i] - l1[j])
                loss = loss + regularizer_lambda * reg
                loss.backward()
                opt.step()

    # Apply structured zeroing
    pruned_count = 0
    for module, name in get_conv_filters(model):
        if name not in to_prune:
            continue
        idxs = to_prune[name]
        if len(idxs) == 0:
            continue
        with torch.no_grad():
            w = module.weight.data
            mask = torch.ones_like(w)
            for idx in idxs:
                if idx < mask.size(0):
                    mask[idx].zero_()
            module.weight.data.mul_(mask)
            if module.bias is not None:
                bmask = torch.ones_like(module.bias.data)
                for idx in idxs:
                    if idx < bmask.numel():
                        bmask[idx] = 0.0
                module.bias.data.mul_(bmask)
        pruned_count += len(idxs)
    return pruned_count, to_prune

# --------------------------
# Full pipeline orchestrator
# --------------------------

def run_pipeline(args):
    device = torch.device('cuda' if torch.cuda.is_available() and not args.force_cpu else 'cpu')
    set_seed(args.seed)
    train_loader, val_loader, test_loader, n_classes = make_dataloaders(args.data_dir, image_size=args.image_size,
                                                                         batch_size=args.batch_size, num_workers=args.num_workers)

    # 1) Teacher (ResNet50)
    print("Loading teacher: ResNet-50")
    teacher = models.resnet50(pretrained=True)
    teacher.fc = nn.Linear(teacher.fc.in_features, n_classes)
    teacher = teacher.to(device)
    opt_t = optim.SGD(teacher.parameters(), lr=args.teacher_lr, momentum=0.9, weight_decay=1e-4)
    ce = nn.CrossEntropyLoss()

    best_val = 0.0
    for ep in range(args.teacher_epochs):
        loss, acc, f1 = train_epoch(teacher, train_loader, ce, opt_t, device)
        metrics = eval_model(teacher, val_loader, device)
        print(f"Teacher Epoch {ep+1}/{args.teacher_epochs} - train_loss {loss:.4f} train_acc {acc:.4f} | val_acc {metrics['acc']:.4f}")
        if metrics['acc'] > best_val:
            best_val = metrics['acc']
            torch.save(teacher.state_dict(), os.path.join(args.work_dir, "teacher_best.pth"))

    teacher.load_state_dict(torch.load(os.path.join(args.work_dir, "teacher_best.pth")))
    teacher.eval()

    # compute teacher baseline metrics
    print("Benchmarking teacher baseline...")
    teacher_metrics = eval_model(teacher, test_loader, device)
    t_total_params, t_nonzero = count_nonzero_params(teacher)
    t_gflops, t_params_pt = compute_flops(teacher, input_res=(3,args.image_size,args.image_size))
    t_inf_gpu = None
    t_inf_cpu = None
    if device.type == 'cuda':
        t_inf_gpu = measure_inference_time(teacher, device, input_size=(3,args.image_size,args.image_size), n_runs=50)
    cpu = torch.device('cpu')
    teacher_cpu = copy.deepcopy(teacher).to(cpu)
    t_inf_cpu = measure_inference_time(teacher_cpu, cpu, input_size=(3,args.image_size,args.image_size), n_runs=50)

    baseline = {
        'teacher': {
            'metrics': teacher_metrics,
            'total_params': t_total_params,
            'nonzero_params': t_nonzero,
            'gflops': t_gflops,
            'pt_params_est': t_params_pt,
            'inf_gpu_ms': t_inf_gpu,
            'inf_cpu_ms': t_inf_cpu
        }
    }

    # 2) Student training with KD (MobileNetV2 default)
    print("Loading student:", args.student_arch)
    if args.student_arch == 'mobilenet_v2':
        student = models.mobilenet_v2(pretrained=True)
        in_features = student.classifier[1].in_features
        student.classifier[1] = nn.Linear(in_features, n_classes)
    else:
        student = timm.create_model(args.student_arch, pretrained=True, num_classes=n_classes)
    student = student.to(device)

    kd_loss_fn = KDLoss(temperature=args.kd_temp, alpha=args.kd_alpha)
    opt_s = optim.SGD(student.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-4)

    # record conv filter L1 history during KD training
    conv_hist = defaultdict(list)
    best_val_s = 0.0
    for ep in range(args.student_epochs):
        loss_s, acc_s, f1_s = train_kd_epoch(student, teacher, train_loader, kd_loss_fn, opt_s, device)
        record_filter_l1_history(student, conv_hist)
        metrics_s = eval_model(student, val_loader, device)
        print(f"Student KD Epoch {ep+1}/{args.student_epochs} - train_loss {loss_s:.4f} val_acc {metrics_s['acc']:.4f}")
        if metrics_s['acc'] > best_val_s:
            best_val_s = metrics_s['acc']
            torch.save(student.state_dict(), os.path.join(args.work_dir, "student_kd_best.pth"))

    student.load_state_dict(torch.load(os.path.join(args.work_dir, "student_kd_best.pth")))

    # benchmark before pruning
    s_total_params, s_nonzero = count_nonzero_params(student)
    s_gflops, s_params_pt = compute_flops(student, input_res=(3,args.image_size,args.image_size))
    s_inf_gpu = None
    if device.type == 'cuda':
        s_inf_gpu = measure_inference_time(student, device, input_size=(3,args.image_size,args.image_size), n_runs=50)
    student_cpu = copy.deepcopy(student).to(torch.device('cpu'))
    s_inf_cpu = measure_inference_time(student_cpu, torch.device('cpu'), input_size=(3,args.image_size,args.image_size), n_runs=50)

    baseline['student_kd'] = {
        'metrics': eval_model(student, test_loader, device),
        'total_params': s_total_params,
        'nonzero_params': s_nonzero,
        'gflops': s_gflops,
        'pt_params_est': s_params_pt,
        'inf_gpu_ms': s_inf_gpu,
        'inf_cpu_ms': s_inf_cpu
    }

    # -------------------------
    # HBFP-style pruning rounds
    # -------------------------
    print("Starting HBFP-style pruning rounds")

    # create a small subset dataloader (up to 256 samples) for regularizer optimization
    subset_size = min(256, len(train_loader.dataset))
    small_subset = torch.utils.data.Subset(train_loader.dataset, list(range(subset_size)))
    dummy_loader = torch.utils.data.DataLoader(small_subset, batch_size=min(args.batch_size, 32),
                                               shuffle=True, num_workers=0)

    prune_round_results = []
    current_student = student
    for round_idx in range(args.prune_rounds):
        print(f"Prune round {round_idx+1}/{args.prune_rounds}: fraction_per_layer={args.prune_fraction}")
        pruned_num, pr_map = hbfp_select_pairs_and_prune(current_student, conv_hist,
                                                         prune_fraction_per_layer=args.prune_fraction,
                                                         device=device, regularizer_lambda=args.reg_lambda,
                                                         optimize_epochs=args.reg_opt_epochs, lr=args.reg_lr,
                                                         dummy_loader=dummy_loader)
        print(f"Applied structured zeroing for {pruned_num} filters (channels) across layers.")
        # fine-tune after pruning
        opt_ft = optim.SGD(current_student.parameters(), lr=args.ft_lr, momentum=0.9, weight_decay=1e-4)
        for e in range(args.ft_epochs):
            loss_ft, acc_ft, f1_ft = train_epoch(current_student, train_loader, ce, opt_ft, device)
        # evaluate and log
        s_total_params, s_nonzero = count_nonzero_params(current_student)
        s_gflops, s_params_pt = compute_flops(current_student, input_res=(3,args.image_size,args.image_size))
        s_metrics = eval_model(current_student, test_loader, device)
        prune_round_results.append({
            'round': round_idx+1,
            'pruned_filters': pruned_num,
            'nonzero_params': s_nonzero,
            'total_params': s_total_params,
            'gflops': s_gflops,
            'metrics': s_metrics
        })
        # update conv_hist: append snapshot after fine-tune so subsequent selection sees updated history
        record_filter_l1_history(current_student, conv_hist)

    # Save results
    out = {
        'baseline': baseline,
        'prune_rounds': prune_round_results
    }
    os.makedirs(args.work_dir, exist_ok=True)
    with open(os.path.join(args.work_dir, "benchmarks_summary.json"), "w") as fh:
        json.dump(out, fh, indent=2, default=lambda o: "<non-serializable>")

    # also write a CSV table for pruning rounds
    rows = []
    for r in prune_round_results:
        row = {
            'round': r['round'],
            'pruned_filters': r['pruned_filters'],
            'nonzero_params': r['nonzero_params'],
            'total_params': r['total_params'],
            'gflops': r['gflops'] if r['gflops'] is not None else -1,
            'acc': r['metrics']['acc'],
            'f1': r['metrics']['f1']
        }
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(args.work_dir, "prune_rounds.csv"), index=False)
    print("Benchmarking finished. Results saved to", args.work_dir)
    return out

# --------------------------
# CLI
# --------------------------

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--data-dir', type=str, required=True, help="Root dataset dir with train/val/test ImageFolder structure")
    p.add_argument('--work-dir', type=str, default='work', help='Where to save models and logs')
    p.add_argument('--student-arch', type=str, default='mobilenet_v2', help='student architecture (mobilenet_v2 or timm name)')
    p.add_argument('--image-size', type=int, default=224)
    p.add_argument('--batch-size', type=int, default=32)
    p.add_argument('--num-workers', type=int, default=4)
    p.add_argument('--teacher-epochs', type=int, default=10)
    p.add_argument('--student-epochs', type=int, default=8)
    p.add_argument('--teacher-lr', type=float, default=1e-3)
    p.add_argument('--lr', type=float, default=0.005)
    p.add_argument('--kd-temp', type=float, default=10.0)
    p.add_argument('--kd-alpha', type=float, default=0.7)
    p.add_argument('--prune-rounds', type=int, default=3)
    p.add_argument('--prune-fraction', type=float, default=0.2, help='fraction of filters per layer to prune each round (0-1)')
    p.add_argument('--ft-epochs', type=int, default=3)
    p.add_argument('--ft-lr', type=float, default=1e-3)
    p.add_argument('--reg-lambda', type=float, default=0.8, help='regularizer lambda for HBFP-style optimization step')
    p.add_argument('--reg-opt-epochs', type=int, default=2)
    p.add_argument('--reg-lr', type=float, default=1e-4)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--force-cpu', action='store_true')
    return p.parse_args()

if __name__ == '__main__':
    args = parse_args()
    os.makedirs(args.work_dir, exist_ok=True)
    run_pipeline(args)

