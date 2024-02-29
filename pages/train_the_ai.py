import streamlit as st
from os import listdir
from pathlib import Path
from utils_for_models import *
from PIL import Image
from torchvision.transforms import v2
import random
import json
from torch import nn
import csv
from models_ import PageDecider, model_decide
import shutil

st.title("Train the model on your data")
st.error("currently under construction")

device = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 10
EPOCHS = 10
train_split = 0.8
model = PageDecider(3, 120, 2, 3, 3).to(device)
old_model = PageDecider(3, 120, 2, 3, 3).to(device)
PATH_TO_MODEL  = Path("models") / "new_page_decider.pth"
if PATH_TO_MODEL.exists():
    model = load_state_dict_2(model, "models/new_page_decider.pth")
else:
    model = load_state_dict_2(model, "models/page_decider_2.pth")


TRAINING_DATA_PATH = Path("training_data")
TRAINING_IMAGES_PATH = TRAINING_DATA_PATH / "Images"
TRAINING_LABELS_PATH = TRAINING_DATA_PATH / "labels.json"

PROCESSED_DATA = Path("processed_data")
PROCESSED_DATA_TRAIN_PATH = PROCESSED_DATA / "train_data"
PROCESSED_DATA_TEST_PATH = PROCESSED_DATA / "test_data"
PROCESSED_IMAGES_TRAIN_PATH =  PROCESSED_DATA_TRAIN_PATH / "images"
PROCESSED_IMAGES_TEST_PATH =  PROCESSED_DATA_TEST_PATH / "images"
PROCESSED_LABELS_TRAIN_PATH = PROCESSED_DATA_TRAIN_PATH / "labels.csv"
PROCESSED_LABELS_TEST_PATH = PROCESSED_DATA_TEST_PATH / "labels.csv"

if not PROCESSED_DATA.exists():
    PROCESSED_DATA.mkdir(parents=True)


transform = v2.Compose([
    v2.Resize(size=(64,64), antialias=True)
])


images = [Image.open(f"training_data/Images/{i}") for i in listdir(TRAINING_IMAGES_PATH)]

with open(TRAINING_LABELS_PATH, "r") as f:
    labels = json.load(f)


def wrangle_data(images, labels):
    delta_yes_no = sum(labels.values()) - len(labels) / 2
    new_data = []
    new_labels = {}
    transform = v2.RandomApply([
        v2.ColorJitter(0.5, 0.2, 0.5),
        v2.RandomGrayscale(0.2)
    ])
    num_of_images = len(images)
    if delta_yes_no < 0: # more 'No' labels than 'Yes'
        while len(new_data) < abs(delta_yes_no):
            for i, decision in enumerate(labels.values()):
                if decision is True:
                    new_data.append(transform(images[i]))
                    new_labels.update({f"Image_{num_of_images}.png": True})
                    num_of_images += 1
                elif decision is False:
                    if random.random() < abs(delta_yes_no) / len(labels) * 2:
                        images[i] = transform(images[i])
                if len(new_data) == abs(delta_yes_no):
                    break
        images.append(new_data)
        labels.update(new_labels)

    elif delta_yes_no > 0:  # more 'Yes' labels than 'No'
        while len(new_data) < abs(delta_yes_no):
            for i, decision in enumerate(labels.values()):
                if decision is False:
                    new_data.append(transform(images[i]))
                    new_labels.update({f"Image_{num_of_images}.png": False})
                    num_of_images += 1
                elif decision is True:
                    if random.random() < abs(delta_yes_no) / len(labels) * 2:
                        images[i] = transform(images[i])
                if len(new_data) == delta_yes_no:
                    break
        images += new_data
        labels.update(new_labels)

    random_indices = torch.randperm(len(images))
    images = [images[i] for i in random_indices]
    fleeting_list = list(map(lambda x: [x[0], int(x[1])], list(labels.items())))
    fleeting_list = [fleeting_list[i] for i in random_indices]
    labels = dict(fleeting_list)

    return  images, labels

def training_loop_3(epochs: int, model: torch.nn.Module, criterion: torch.nn.Module, optimizer: torch.nn.Module, train_data: torch.Tensor, test_data: torch.Tensor, device = "cpu", data_loader = DataLoader, batch_size: int = 1, shuffle = True, output = None, performance_tracker = None, tracked_performance: str = None, input_to_performance_tracker = None, y = lambda x: x, x = lambda x: x):
    progress_text = f"Training model for {epochs} epochs. Please wait..."
    progress_bar = st.progress(0, text = "training model")
    train_dataloader = data_loader(dataset=train_data, batch_size=batch_size, shuffle=shuffle)
    test_dataloader = data_loader(dataset=test_data, batch_size=batch_size, shuffle=shuffle)
    if output is None:
        output = lambda x: model(x)
    for epoch in range(epochs):
        train_loss = 0
        for batch, (x_train, y_train) in enumerate(train_dataloader): 
            x_train, y_train = x(x_train).to(device), y(y_train).to(device)
            model.train()
            y_pred = output(x_train)
            loss = criterion(y_pred, y_train)
            train_loss += loss
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        progress_bar.progress(epoch / epochs, text = progress_text)
        
    progress_bar.empty()


if st.button("generate and save training + testing data"):
    images, labels = wrangle_data(images, labels)

    train_cutoff = int(train_split * len(images))
    train_images = images[:train_cutoff]
    train_labels = dict(list(labels.items())[:train_cutoff])
    test_images = images[train_cutoff:]
    test_labels = dict(list(labels.items())[train_cutoff:])
    
    if PROCESSED_DATA.exists():
        for path_ in listdir(PROCESSED_DATA):
            path = PROCESSED_DATA / path_
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)  
            elif os.path.isdir(path):
                shutil.rmtree(path)  
            else:
                raise ValueError("{} is not a file or dir.".format(path))
    
    if not PROCESSED_DATA_TRAIN_PATH.exists():
        PROCESSED_DATA_TRAIN_PATH.mkdir(parents=True)

    if not PROCESSED_DATA_TEST_PATH.exists():
        PROCESSED_DATA_TEST_PATH.mkdir(parents=True)

    if not PROCESSED_IMAGES_TRAIN_PATH.exists():
        PROCESSED_IMAGES_TRAIN_PATH.mkdir(parents=True)

    if not PROCESSED_IMAGES_TEST_PATH.exists():
        PROCESSED_IMAGES_TEST_PATH.mkdir(parents=True)

    with open(PROCESSED_LABELS_TRAIN_PATH, "w") as f:
        write = csv.writer(f)
        write.writerows(train_labels.items())
    
    with open(PROCESSED_LABELS_TEST_PATH, "w") as f:
        write = csv.writer(f)
        write.writerows(test_labels.items())


    for i, image in enumerate(train_images):
        PROCESSED_IMAGE_SAVE_PATH_FOR_TRAINING = f"processed_data/train_data/images/{list(train_labels.keys())[i]}"
        image = image.save(fp = PROCESSED_IMAGE_SAVE_PATH_FOR_TRAINING, format = "PNG")
    
    for i, image in enumerate(train_images):
        PROCESSED_IMAGE_SAVE_PATH_FOR_TESTING = f"processed_data/test_data/images/{list(test_labels.keys())[i]}"
        image = image.save(fp = PROCESSED_IMAGE_SAVE_PATH_FOR_TESTING, format = "PNG")

if st.button("delete new model"):
    if PATH_TO_MODEL.exists():
        os.remove(PATH_TO_MODEL)


with st.form("parameters"):
    batch_size = st.slider("Batch Size", 1, 100, value = BATCH_SIZE )
    epochs = st.slider("Epochs", 5, 100, value = EPOCHS)
    learning_rate = st.slider("learning rate", 1, 5, value = 1) * 10 ** -4
    if st.form_submit_button("Submit"):
        pass

if st.button("train ai"):

    train_data = ppp_files("processed_data/train_data/labels.csv",
                    "processed_data/train_data/images",
                    transform)

    test_data = ppp_files("processed_data/test_data/labels.csv",
                    "processed_data/test_data/images",
                    transform)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    acc_pre_training = accuracy(model, test_data, device=device)

    training_loop_3(epochs, model, criterion, optimizer, train_data, test_data, device, batch_size=batch_size)

    acc_post_training = accuracy(model, test_data, device=device)

    try:
        old_model = load_state_dict_2(old_model, "models/new_page_decider.pth")
        old_model_acc = accuracy(old_model, test_data, device = device)
    except:
        old_model_acc = 0
    
    original_acc = accuracy(model_decide.to(device), test_data, device=device)

    st.write("acc pre training: ", acc_pre_training," | ", "acc post training: ", acc_post_training, " | ", "acc of old model: ", old_model_acc, " | ", "acc of original model: ", original_acc)

    if acc_post_training > acc_pre_training and acc_post_training > old_model_acc:
        save_function(model.state_dict(), "new_page_decider.pth")
        st.write("new model saved succesfully as new_page_decider.pth in models")
    else:
        st.write("model was not saved, due to bad performance")