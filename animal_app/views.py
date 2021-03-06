# djangoで扱うものをインポート
import csv

# 前処理や推論で必要なものをインポート
import numpy as np
# PyTorchで必要なモジュール
import torch
import torch.nn.functional as F
import torchvision
from django.http import request
from django.shortcuts import redirect, render
from model import predict
from PIL import Image
from torchvision import transforms

from .forms import FormAnimal
from .models import ModelAnimal, ModelFile


def classify(request):
    animals_info = list(ModelAnimal.objects.all())
    # もしanimals_info が空ならば animal_data2.csv をモデルに保存
    if not animals_info:
        with open('static/data/animal_data.csv', encoding='utf-8') as f:
            csv_data = csv.reader(f)
            # csvデータをdataリストに保存
            data = []
            # 要素番号を動物ラベルとし、アニマル豆知識データをモデルに保存
            for i, data in enumerate(csv_data):
                name, title, disc = data
                animal_info = ModelAnimal(
                    animal_label=i,
                    animal_name=name,
                    animal_title=title,
                    animal_disc=disc)
                animal_info.save()

    # もしリクエストがPOSTじゃなかったらindex.htmlを返す
    if not request.method == 'POST':
        form = FormAnimal()
        return render(request, 'index.html', {'form': form})
    # もしリクエストがPOSTであればフォーム内容を保存
    else:
        form = FormAnimal(request.POST, request.FILES)
        if form.is_valid():
            form.save()

        # リクエストのファイル名を保存し、PATHを取得
        img_name = request.FILES['image']
        img_url = 'media/documents/{}'.format(img_name)
        image = Image.open(img_url)
        x = predict.transform(image)
        x = x.unsqueeze(0)

        # モデルのインスタンス化（モジュール名.クラス名）
        net = predict.Net()

        # パラメーターの読み込み
        net.load_state_dict(torch.load('model/animal_model.pt'))
        net.eval()

        # 推論、予測値の計算
        y = net(x)
        # 予測ラベル
        y_arg = y.argmax()
        # detach()はTensor型から勾配情報を抜いたものを取得する.これでndarrayに変換
        y_arg = y_arg.detach().clone().numpy()
        # 確率に変換
        y_proba = F.softmax(y, dim=1)
        # .max()で最大値を取得
        y_proba = y_proba.max() * 100
        # tensor=>numpy型に変換
        y_proba = y_proba.detach().clone().numpy()
        # 小数点第2位まで切り捨て
        y_proba = np.round(y_proba, 2)
        animal_info = ModelAnimal.objects.filter(animal_label=y_arg)
        # Queryset~となっているものの先頭を取得
    return render(request,
                  'classify.html',
                  {'img_url': img_url,
                   'animal_info': animal_info[0],
                   'y_proba': y_proba})
