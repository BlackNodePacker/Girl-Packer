# GameMediaTool/ai/cnn/cnn_model.py (النسخة النهائية الكاملة والمصححة)

import os
import json
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from PIL import Image
from tools.logger import get_logger

logger = get_logger("CNN_Model (PyTorch)")


def is_valid_image_file(filename: str):
    """Checks if a file has a common image extension."""
    valid_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
    return filename.lower().endswith(valid_extensions)


def build_class_map(train_dir: str, map_save_path: str) -> dict:
    """
    Builds a class-to-index map from the training directory subfolders.
    """
    if not os.path.isdir(train_dir):
        logger.error(f"Training data directory not found: {train_dir}")
        return None

    class_names = sorted([d.name for d in os.scandir(train_dir) if d.is_dir()])

    if not class_names:
        logger.error(f"No class sub-folders found in {train_dir}. Training cannot proceed.")
        return None

    class_map = {name: i for i, name in enumerate(class_names)}

    try:
        with open(map_save_path, "w") as f:
            json.dump(class_map, f, indent=4)
        logger.info(f"Class map created with {len(class_names)} classes.")
        logger.info(f"Class map saved to {map_save_path}")
        return class_map
    except Exception as e:
        logger.error(f"Could not save class map to {map_save_path}: {e}")
        return None


def create_pytorch_model(num_classes: int):
    """
    Creates a ResNet-18 model with a modified final layer for transfer learning.
    """
    model = models.resnet18(weights="IMAGENET1K_V1")

    for param in model.parameters():
        param.requires_grad = False

    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)

    logger.info(f"Created PyTorch model with {num_classes} output classes.")
    return model


def train_pytorch_model(
    data_dir: str, model_save_path: str, map_save_path: str, num_epochs=25, batch_size=4
):
    """
    The main training function. Handles train/val splitting, data loading,
    the training loop, and the validation loop.
    """
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    class_map = build_class_map(train_dir, map_save_path)
    if not class_map:
        return

    num_classes = len(class_map)

    data_transforms = {
        "train": transforms.Compose(
            [
                transforms.RandomResizedCrop(224),
                transforms.RandomHorizontalFlip(),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        ),
        "val": transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        ),
    }

    try:
        image_datasets = {
            "train": datasets.ImageFolder(
                train_dir, data_transforms["train"], is_valid_file=is_valid_image_file
            ),
            "val": datasets.ImageFolder(
                val_dir, data_transforms["val"], is_valid_file=is_valid_image_file
            ),
        }
        dataloaders = {
            "train": DataLoader(
                image_datasets["train"], batch_size=batch_size, shuffle=True, num_workers=2
            ),
            "val": DataLoader(
                image_datasets["val"], batch_size=batch_size, shuffle=False, num_workers=2
            ),
        }
        dataset_sizes = {x: len(image_datasets[x]) for x in ["train", "val"]}
        logger.info(
            f"Datasets created. Training images: {dataset_sizes['train']}, Validation images: {dataset_sizes['val']}"
        )
    except Exception as e:
        logger.error(
            f"Failed to create datasets. Check data paths and folder structure. Error: {e}"
        )
        return

    model = create_pytorch_model(num_classes)
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.SGD(model.fc.parameters(), lr=0.001, momentum=0.9)

    logger.info(f"Starting training for {num_epochs} epochs on device: {device}")

    for epoch in range(num_epochs):
        logger.info(f"Epoch {epoch+1}/{num_epochs}")

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            epoch_loss = running_loss / dataset_sizes[phase]
            epoch_acc = running_corrects.double() / dataset_sizes[phase]

            logger.info(f"{phase.capitalize():<5} Loss: {epoch_loss:.4f} Acc: {epoch_acc:.4f}")

    torch.save(model.state_dict(), model_save_path)
    logger.info(f"Training complete. Model saved to {model_save_path}")


def classify_image_pytorch(model, image, class_map: dict, device):
    """
    Classifies a single image (PIL Image) using a trained PyTorch model.
    """
    transform = transforms.Compose(
        [
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )

    try:
        # We now expect a PIL image directly
        image_tensor = transform(image).unsqueeze(0).to(device)
        model.to(device)

        model.eval()
        with torch.no_grad():
            outputs = model(image_tensor)
            _, preds = torch.max(outputs, 1)

        idx_to_class = {v: k for k, v in class_map.items()}
        class_name = idx_to_class.get(preds.item(), "unknown")
        return class_name

    except Exception as e:
        logger.error(f"Error during PyTorch classification: {e}")
        return "unknown"
