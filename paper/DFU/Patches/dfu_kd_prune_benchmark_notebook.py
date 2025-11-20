# DFU Knowledge Distillation + HBFP-style Pruning Benchmark Notebook
# ---------------------------------------------------------------
# This notebook implements the pipeline described in the script I gave you earlier,
# adapted for interactive use in a Jupyter environment.
#
# Cells are separated by '# %%' markers so you can run them cell-by-cell in Jupyter
# or VSCode. The notebook covers:
#  - Install / imports
#  - Utilities (seed, metrics, counting params, flops, timing)
#  - Data loaders (ImageFolder layout expected)
#  - Train teacher (ResNet-50)
#  - Train student with Knowledge Distillation (MobileNetV2)
#  - Record filter L1 history for HBFP selection
#  - HBFP-style selection + optimization + structured pruning (zeroing channels)
#  - Fine-tune rounds and benchmarking (accuracy, F1, params, nonzero params, FLOPs, timings)
#  - Save outputs to work directory
#
# Notes:
#  - This file is plain Python (code cell markers used). Paste it into a .py file and
#    open it as a notebook in Jupyter/VSCode, or run cells in a Python REPL.
#  - Adjust the 'DATA_DIR' variable to point to your dataset with train/val/test subfolders.
#  - For a true smallest on-disk model after pruning, additional model surgery is required
#    to remove zeroed channels. This notebook includes a placeholder for that step.
#
# Author: Generated for you. Tweak hyperparameters as needed.

# %%
# Install dependencies (uncomment and run once in the notebook environment)
# !pip install torch torchvision timm ptflops scikit-learn pandas tqdm

# %%
# Imports
import os
import time
import json
import copy
import numpy as np
from collections import defaultdict

import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms, models
import timm
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from ptflops import get_model_complexity_info
import pandas as pd
from tqdm import tqdm

# %%
# User-editable config
DATA_DIR = '/path/to/dfu_dataset'  # <-- set this to your dataset root with train/val/test
WORK_DIR = './dfu_bench_notebook'
IMAGE_SIZE = 224
BATCH_SIZE = 32
NUM_WORKERS = 4
SEED = 42
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Training hyperparams (quick defaults for interactive runs)
TEACHER_EPOCHS = 6
STUDENT_EPOCHS = 6
TEACHER_LR = 1e-3
STUDENT_LR = 5e-3
KD_TEMPERATURE = 10.0
KD_ALPHA = 0.7

# Pruning hyperparams
PRUNE_ROUNDS = 3
PRUNE_FRACTION = 0.2  # fraction per layer each round
REG_LAMBDA = 0.8
REG_OPT_EPOCHS = 2
REG_LR = 1e-4
FT_EPOCHS = 3
FT_LR = 1e-3

os.makedirs(WORK_DIR, exist_ok=True)

# %%
# Utilities

def set_seed(seed=42):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(SEED)


def count_nonzero_params(model: torch.nn.Module):
    total = 0
    nonzero = 0
    for p in model.parameters():
        num = p.numel()
        total += num
        nonzero += (p.abs() > 1e-8).sum().item()
    return total, nonzero


def measure_inference_time(model, device, input_size=(3,224,224), n_runs=50, batch_size=1):
    model.eval()
    dummy = torch.randn((batch_size,)+input_size).to(device)
    with torch.no_grad():
        for _ in range(5):
            _ = model(dummy)
    times = []
    with torch.no_grad():
        for _ in range(n_runs):
            t0 = time.time()
            _ = model(dummy)
            t1 = time.time()
            times.append(t1 - t0)
    mean_ms = 1000.0 * np.mean(times)
    std_ms = 1000.0 * np.std(times)
    return mean_ms, std_ms


def compute_flops(model, input_res=(3,224,224)):
    try:
        macs, params = get_model_complexity_info(model, input_res[1:], as_strings=False, print_per_layer_stat=False)
        gflops = macs / 1e9
        return gflops, params
    except Exception as e:
        print('ptflops error:', e)
        return None, None

# %%
# Dataset loaders (ImageFolder layout expected)

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

# %%
# Training / evaluation helpers

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
    acc = accuracy_score(trues, preds)
    f1 = f1_score(trues, preds, average='macro')
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
    acc = accuracy_score(trues, preds)
    f1 = f1_score(trues, preds, average='macro')
    prec = precision_score(trues, preds, average='macro')
    rec = recall_score(trues, preds, average='macro')
    return {'acc': acc, 'f1': f1, 'prec': prec, 'rec': rec}

# %%
# Knowledge Distillation loss
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

# %%
# HBFP bookkeeping and selection functions

def get_conv_filters(module):
    convs = []
    for name, m in module.named_modules():
        if isinstance(m, nn.Conv2d):
            convs.append((m, name))
    return convs


def record_filter_l1_history(model, conv_hist: dict):
    for module, name in get_conv_filters(model):
        w = module.weight.detach().cpu().numpy()
        l1_per_filter = np.sum(np.abs(w), axis=(1,2,3))
        if name not in conv_hist:
            conv_hist[name] = []
        conv_hist[name].append(l1_per_filter.copy())


def compute_pairwise_summed_diff(conv_hist: dict):
    selection = {}
    for name, history in conv_hist.items():
        arr = np.stack(history, axis=0)
        num_filters = arr.shape[1]
        pair_list = []
        for i in range(num_filters):
            for j in range(i+1, num_filters):
                diff = np.sum(np.abs(arr[:, i] - arr[:, j]))
                pair_list.append((i, j, diff))
        selection[name] = pair_list
    return selection

# %%
# HBFP select + prune function (structured channel zeroing) - same logic as in script

def hbfp_select_pairs_and_prune(model, conv_hist, prune_fraction_per_layer=0.2, device='cpu', regularizer_lambda=1.0, optimize_epochs=3, lr=1e-4, dummy_loader=None):
    selection = compute_pairwise_summed_diff(conv_hist)
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
        last_epoch_arr = np.array(conv_hist[name][-1])
        pr_indices = []
        for (i,j,d) in selected_pairs:
            pr = i if last_epoch_arr[i] < last_epoch_arr[j] else j
            pr_indices.append(pr)
        to_prune[name] = sorted(list(set(pr_indices)))
    # optimization regularizer
    if regularizer_lambda > 0 and dummy_loader is not None:
        selected_pairs_map = {}
        for module, name in get_conv_filters(model):
            if name not in selection:
                continue
            pairs_sorted = sorted(selection[name], key=lambda x: x[2])
            num_filters = module.weight.shape[0]
            prune_k = int(np.round(prune_fraction_per_layer * num_filters))
            sel_pairs = [(i,j) for (i,j,_) in pairs_sorted[:max(0, prune_k)]]
            if sel_pairs:
                selected_pairs_map[name] = sel_pairs
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
                    reg = 0.0
                    for module, name in get_conv_filters(model):
                        if name not in selected_pairs_map:
                            continue
                        w = module.weight
                        l1 = w.abs().view(w.size(0), -1).sum(dim=1)
                        for (i,j) in selected_pairs_map[name]:
                            reg = reg + torch.abs(l1[i] - l1[j])
                    loss = loss + regularizer_lambda * reg
                    loss.backward()
                    opt.step()
    # apply structured zeroing
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
                mask[idx].zero_()
            module.weight.data.mul_(mask)
            if module.bias is not None:
                bmask = torch.ones_like(module.bias.data)
                for idx in idxs:
                    bmask[idx] = 0.0
                module.bias.data.mul_(bmask)
        pruned_count += len(idxs)
    return pruned_count, to_prune

# %%
# Pipeline run function (interactive-friendly)

def run_pipeline_interactive(data_dir=DATA_DIR, work_dir=WORK_DIR):
    train_loader, val_loader, test_loader, n_classes = make_dataloaders(data_dir, IMAGE_SIZE, BATCH_SIZE, NUM_WORKERS)

    # Teacher
    teacher = models.resnet50(pretrained=True)
    teacher.fc = nn.Linear(teacher.fc.in_features, n_classes)
    teacher = teacher.to(DEVICE)
    opt_t = optim.SGD(teacher.parameters(), lr=TEACHER_LR, momentum=0.9, weight_decay=1e-4)
    ce = nn.CrossEntropyLoss()

    best_val = 0.0
    for ep in range(TEACHER_EPOCHS):
        loss, acc, f1 = train_epoch(teacher, train_loader, ce, opt_t, DEVICE)
        metrics = eval_model(teacher, val_loader, DEVICE)
        print(f"Teacher Epoch {ep+1}/{TEACHER_EPOCHS} - train_acc {acc:.4f} val_acc {metrics['acc']:.4f}")
        if metrics['acc'] > best_val:
            best_val = metrics['acc']
            torch.save(teacher.state_dict(), os.path.join(work_dir, 'teacher_best.pth'))

    teacher.load_state_dict(torch.load(os.path.join(work_dir, 'teacher_best.pth')))
    teacher.eval()

    # benchmark teacher
    teacher_metrics = eval_model(teacher, test_loader, DEVICE)
    t_total, t_nonzero = count_nonzero_params(teacher)
    t_gflops, _ = compute_flops(teacher, input_res=(3,IMAGE_SIZE,IMAGE_SIZE))
    teacher_cpu = copy.deepcopy(teacher).to(torch.device('cpu'))
    t_inf_cpu = measure_inference_time(teacher_cpu, torch.device('cpu'), input_size=(3,IMAGE_SIZE,IMAGE_SIZE), n_runs=30)

    baseline = {'teacher': {'metrics': teacher_metrics, 'total_params': t_total, 'nonzero_params': t_nonzero, 'gflops': t_gflops, 'inf_cpu_ms': t_inf_cpu}}

    # Student KD
    student = models.mobilenet_v2(pretrained=True)
    in_features = student.classifier[1].in_features
    student.classifier[1] = nn.Linear(in_features, n_classes)
    student = student.to(DEVICE)
    kd_loss_fn = KDLoss(temperature=KD_TEMPERATURE, alpha=KD_ALPHA)
    opt_s = optim.SGD(student.parameters(), lr=STUDENT_LR, momentum=0.9, weight_decay=1e-4)

    conv_hist = defaultdict(list)
    best_val_s = 0.0
    for ep in range(STUDENT_EPOCHS):
        loss_s, acc_s, f1_s = train_kd_epoch(student, teacher, train_loader, kd_loss_fn, opt_s, DEVICE)
        record_filter_l1_history(student, conv_hist)
        metrics_s = eval_model(student, val_loader, DEVICE)
        print(f"Student KD Epoch {ep+1}/{STUDENT_EPOCHS} - train_acc {acc_s:.4f} val_acc {metrics_s['acc']:.4f}")
        if metrics_s['acc'] > best_val_s:
            best_val_s = metrics_s['acc']
            torch.save(student.state_dict(), os.path.join(work_dir, 'student_kd_best.pth'))

    student.load_state_dict(torch.load(os.path.join(work_dir, 'student_kd_best.pth')))

    s_total, s_nonzero = count_nonzero_params(student)
    s_gflops, _ = compute_flops(student, input_res=(3,IMAGE_SIZE,IMAGE_SIZE))
    student_cpu = copy.deepcopy(student).to(torch.device('cpu'))
    s_inf_cpu = measure_inference_time(student_cpu, torch.device('cpu'), input_size=(3,IMAGE_SIZE,IMAGE_SIZE), n_runs=30)

    baseline['student_kd'] = {'metrics': eval_model(student, test_loader, DEVICE), 'total_params': s_total, 'nonzero_params': s_nonzero, 'gflops': s_gflops, 'inf_cpu_ms': s_inf_cpu}

    # pruning rounds
    small_subset = torch.utils.data.Subset(train_loader.dataset, list(range(min(256, len(train_loader.dataset)))))
    dummy_loader = torch.utils.data.DataLoader(small_subset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0)

    prune_round_results = []
    current_student = student
    for round_idx in range(PRUNE_ROUNDS):
        print(f"Prune round {round_idx+1}/{PRUNE_ROUNDS}")
        pruned_num, pr_map = hbfp_select_pairs_and_prune(current_student, conv_hist, prune_fraction_per_layer=PRUNE_FRACTION, device=DEVICE, regularizer_lambda=REG_LAMBDA, optimize_epochs=REG_OPT_EPOCHS, lr=REG_LR, dummy_loader=dummy_loader)
        print(f"Zeroed {pruned_num} channels")
        # fine-tune
        opt_ft = optim.SGD(current_student.parameters(), lr=FT_LR, momentum=0.9, weight_decay=1e-4)
        for e in range(FT_EPOCHS):
            loss_ft, acc_ft, f1_ft = train_epoch(current_student, train_loader, ce, opt_ft, DEVICE)
        s_total, s_nonzero = count_nonzero_params(current_student)
        s_gflops, _ = compute_flops(current_student, input_res=(3,IMAGE_SIZE,IMAGE_SIZE))
        s_metrics = eval_model(current_student, test_loader, DEVICE)
        prune_round_results.append({'round': round_idx+1, 'pruned_filters': pruned_num, 'nonzero_params': s_nonzero, 'total_params': s_total, 'gflops': s_gflops, 'metrics': s_metrics})
        record_filter_l1_history(current_student, conv_hist)

    out = {'baseline': baseline, 'prune_rounds': prune_round_results}
    with open(os.path.join(work_dir, 'benchmarks_summary.json'), 'w') as fh:
        json.dump(out, fh, indent=2, default=lambda o: '<non-serializable>')
    rows = []
    for r in prune_round_results:
        rows.append({'round': r['round'], 'pruned_filters': r['pruned_filters'], 'nonzero_params': r['nonzero_params'], 'total_params': r['total_params'], 'gflops': r['gflops'] if r['gflops'] is not None else -1, 'acc': r['metrics']['acc'], 'f1': r['metrics']['f1']})
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(work_dir, 'prune_rounds.csv'), index=False)

    print('Done. Results saved to', work_dir)
    return out

# %%
# Run pipeline (uncomment to execute here)
# results = run_pipeline_interactive(DATA_DIR, WORK_DIR)
# display(results)

# %%
# Placeholder: function to rebuild a compact model from zeroed channels (advanced)
# Implementing a full channel-prune --> architecture-surgery flow is possible but
# non-trivial. If you want this, I can add a helper that inspects pruned masks,
# reconstructs new convolutional layers with fewer output channels and copies weights.
# For now this notebook leaves the student with zeroed channels and reports nonzero params.

# End of notebook
