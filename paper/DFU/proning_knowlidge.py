#!/usr/bin/env python3
"""
train_kd_prune_fixed.py

This is the KD + iterative pruning pipeline with your dataset path set as the default.
Save as train_kd_prune_fixed.py and run:

# Train teacher
python train_kd_prune_fixed.py --mode teacher

# Then run student prune+KD (provide teacher checkpoint location if different):
python train_kd_prune_fixed.py --mode student_prune --teacher-checkpoint ./outputs/teacher/best.pth

If you prefer to pass a different dataset path, use --data-root <path>.
"""
import argparse, os, random, json
from pathlib import Path
from tqdm import tqdm

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import transforms, datasets, models
from torch.nn.utils import prune

# -------------------------
# DEFAULT DATA PATH (your path)
DEFAULT_DATA_ROOT = "/home/lakshya/jupyter/paper/DFU/Patches/data"

# -------------------------
def seed_everything(seed=42):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

def get_device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")

# -------------------------
def make_dataloaders(data_root, batch_size=64, img_size=224, num_workers=4, labels_csv=None):
    transform_train = transforms.Compose([
        transforms.RandomResizedCrop(img_size),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor()
    ])
    transform_val = transforms.Compose([
        transforms.Resize(int(img_size*1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor()
    ])

    root = Path(data_root)
    if (root / "train").exists():
        train_dir = root / "train"
        val_dir = root / "val" if (root / "val").exists() else None
        train_ds = datasets.ImageFolder(str(train_dir), transform=transform_train)
        if val_dir:
            val_ds = datasets.ImageFolder(str(val_dir), transform=transform_val)
        else:
            n = len(train_ds)
            val_size = int(0.2 * n)
            train_size = n - val_size
            train_ds, val_ds = torch.utils.data.random_split(train_ds, [train_size, val_size])
    else:
        dataset = datasets.ImageFolder(str(root), transform=transform_train)
        n = len(dataset)
        val_size = int(0.2 * n)
        train_size = n - val_size
        train_ds, val_ds = torch.utils.data.random_split(dataset, [train_size, val_size])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    # try to infer num_classes robustly
    try:
        if hasattr(train_loader.dataset, 'dataset') and hasattr(train_loader.dataset.dataset, 'classes'):
            num_classes = len(train_loader.dataset.dataset.classes)
        elif 'dataset' in locals() and hasattr(dataset, 'classes'):
            num_classes = len(dataset.classes)
        else:
            # fallback: folder names
            classes = [p.name for p in root.iterdir() if p.is_dir()]
            num_classes = len(classes)
    except Exception:
        num_classes = 2
    return train_loader, val_loader, num_classes

# -------------------------
def get_model(name="resnet18", num_classes=2, pretrained=True):
    if name == "resnet18":
        model = models.resnet18(pretrained=pretrained)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif name == "mobilenet_v2":
        model = models.mobilenet_v2(pretrained=pretrained)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    else:
        raise ValueError("unsupported model")
    return model

# KD loss
def kd_loss_fn(student_logits, teacher_logits, labels, T=4.0, alpha=0.1):
    kd = F.kl_div(
        F.log_softmax(student_logits / T, dim=1),
        F.softmax(teacher_logits / T, dim=1),
        reduction='batchmean'
    ) * (T * T)
    ce = F.cross_entropy(student_logits, labels)
    return alpha * ce + (1.0 - alpha) * kd

# training / evaluation loops
def evaluate(model, loader, device):
    model.eval()
    correct = 0
    total = 0
    loss_sum = 0.0
    with torch.no_grad():
        for x,y in loader:
            x = x.to(device); y = y.to(device)
            logits = model(x)
            loss = F.cross_entropy(logits, y)
            loss_sum += loss.item() * x.size(0)
            preds = logits.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += x.size(0)
    return correct/total, (loss_sum/total)

def train_one_epoch_teacher(model, loader, optimizer, device):
    model.train()
    total_loss = 0.0
    for x,y in loader:
        x = x.to(device); y = y.to(device)
        logits = model(x)
        loss = F.cross_entropy(logits, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset)

def train_one_epoch_student_kd(student, teacher, loader, optimizer, device, T=4.0, alpha=0.1):
    student.train()
    teacher.eval()
    total_loss = 0.0
    for x,y in loader:
        x = x.to(device); y = y.to(device)
        with torch.no_grad():
            t_logits = teacher(x)
        s_logits = student(x)
        loss = kd_loss_fn(s_logits, t_logits, y, T=T, alpha=alpha)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * x.size(0)
    return total_loss / len(loader.dataset)

# pruning helpers
def collect_prunable_parameters(model):
    params = []
    for module in model.modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            params.append((module, 'weight'))
    return params

def apply_global_unstructured_prune(model, amount):
    params = collect_prunable_parameters(model)
    prune.global_unstructured(params, pruning_method=prune.L1Unstructured, amount=amount)

def remove_pruning_reparametrization(model):
    for module in model.modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            try:
                prune.remove(module, 'weight')
            except Exception:
                pass

def compute_sparsity(model):
    total = 0
    zero = 0
    for p in model.parameters():
        num = p.numel()
        total += num
        zero += (p == 0).sum().item()
    return zero / total

# main workflows
def train_teacher(args):
    device = get_device()
    train_loader, val_loader, num_classes = make_dataloaders(args.data_root, args.batch_size, img_size=args.img_size, num_workers=args.num_workers)
    model = get_model(args.teacher_arch, num_classes=num_classes, pretrained=args.pretrained).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-4)
    best_acc = 0.0
    os.makedirs(args.save_dir, exist_ok=True)
    for ep in range(args.epochs):
        loss = train_one_epoch_teacher(model, train_loader, optimizer, device)
        val_acc, val_loss = evaluate(model, val_loader, device)
        print(f"[Teacher] Epoch {ep+1}/{args.epochs} loss={loss:.4f} val_acc={val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({'model_state': model.state_dict(), 'ep': ep, 'acc': val_acc}, os.path.join(args.save_dir, 'best.pth'))
    print(f"[Teacher] Best val acc: {best_acc:.4f}")

def student_prune_workflow(args):
    device = get_device()
    train_loader, val_loader, num_classes = make_dataloaders(args.data_root, args.batch_size, img_size=args.img_size, num_workers=args.num_workers)
    teacher_ckpt = torch.load(args.teacher_checkpoint, map_location='cpu')
    teacher = get_model(args.teacher_arch, num_classes=num_classes, pretrained=False)
    teacher.load_state_dict(teacher_ckpt['model_state'])
    teacher = teacher.to(device).eval()

    student = get_model(args.student_arch, num_classes=num_classes, pretrained=False).to(device)
    optimizer = torch.optim.SGD(student.parameters(), lr=args.lr, momentum=0.9, weight_decay=1e-4)

    os.makedirs(args.save_dir, exist_ok=True)
    if args.pretrain_student_kd_epochs > 0:
        for ep in range(args.pretrain_student_kd_epochs):
            loss = train_one_epoch_student_kd(student, teacher, train_loader, optimizer, device, T=args.T, alpha=args.alpha)
            acc, _ = evaluate(student, val_loader, device)
            print(f"[Student pre-KD] ep {ep+1}/{args.pretrain_student_kd_epochs} loss={loss:.4f} val_acc={acc:.4f}")

    prune_steps = args.prune_steps
    per_step = args.target_sparsity / prune_steps
    metrics = []
    best_acc = 0.0

    for step in range(prune_steps+1):
        # distill / fine-tune at current sparsity
        for ep in range(args.distill_epochs_per_step):
            train_one_epoch_student_kd(student, teacher, train_loader, optimizer, device, T=args.T, alpha=args.alpha)
        val_acc, _ = evaluate(student, val_loader, device)
        s = compute_sparsity(student)
        metrics.append({'step': step, 'sparsity': s, 'val_acc': val_acc})
        print(f"[After step {step}] sparsity={s:.4f} val_acc={val_acc:.4f}")
        if val_acc > best_acc:
            best_acc = val_acc
            torch.save({'model_state': student.state_dict(), 'ep': step, 'acc': val_acc, 'sparsity': s}, os.path.join(args.save_dir, 'best_student.pth'))
        if step == prune_steps:
            break
        apply_global_unstructured_prune(student, amount=per_step)
        remove_pruning_reparametrization(student)
        print(f"[Prune] Applied additional {per_step:.3f} -> approx total sparsity {compute_sparsity(student):.4f}")

    val_acc, _ = evaluate(student, val_loader, device)
    print(f"[Student] Final val acc: {val_acc:.4f}")
    torch.save({'model_state': student.state_dict(), 'acc': val_acc}, os.path.join(args.save_dir, 'final_student.pth'))
    with open(os.path.join(args.save_dir, 'metrics.json'), 'w') as f:
        json.dump(metrics, f, indent=2)

# -------------------------
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-root", type=str, default=DEFAULT_DATA_ROOT,
                   help=f"Dataset root. Default is pre-set to {DEFAULT_DATA_ROOT}")
    p.add_argument("--mode", choices=["teacher","student_prune"], default="teacher")
    p.add_argument("--teacher-arch", type=str, default="resnet18")
    p.add_argument("--student-arch", type=str, default="resnet18")
    p.add_argument("--teacher-checkpoint", type=str, default="./outputs/teacher/best.pth")
    p.add_argument("--epochs", type=int, default=30)
    p.add_argument("--pretrained", action='store_true')
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--img-size", type=int, default=224)
    p.add_argument("--lr", type=float, default=0.01)
    p.add_argument("--save-dir", type=str, default="./outputs")
    p.add_argument("--T", type=float, default=4.0)
    p.add_argument("--alpha", type=float, default=0.1)
    p.add_argument("--target-sparsity", type=float, default=0.9)
    p.add_argument("--prune-steps", type=int, default=9)
    p.add_argument("--distill-epochs-per-step", type=int, default=2)
    p.add_argument("--pretrain-student-kd-epochs", type=int, default=5)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--num-workers", type=int, default=4)
    return p.parse_args()

def main():
    args = parse_args()
    seed_everything(args.seed)
    if args.mode == "teacher":
        train_teacher(args)
    elif args.mode == "student_prune":
        if not args.teacher_checkpoint or not os.path.exists(args.teacher_checkpoint):
            raise ValueError("Provide valid --teacher-checkpoint for student_prune mode (path to teacher best.pth)")
        student_prune_workflow(args)

if __name__ == "__main__":
    main()
