# K 近邻（K-Nearest Neighbors, KNN）算法系统学习指南

> 本文从核心思想、scikit-learn API、距离度量、特征预处理到超参数选择，系统梳理 KNN，并以手写数字识别作为综合案例。
>
> 环境：Python ≥ 3.9，scikit-learn ≥ 1.3，numpy，matplotlib，pandas（表格处理，可选）。

## 目录

1. 一、KNN 算法简介
2. 二、scikit-learn 中的 KNN API
3. 三、距离度量
4. 四、特征预处理
5. 五、超参数选择方法（含手写数字识别案例）
6. 附录：环境、速查表与常见问题

---

## 一、KNN 算法简介

### 1.1 核心思想

KNN 是一种**基于实例的学习（instance-based learning）**，也是典型的**懒惰学习（lazy learning）**：训练阶段不学习显式参数，只把训练样本保存起来；预测阶段才根据待预测样本与训练样本的距离，找出最近的 $k$ 个邻居，用邻居的标签做决策。

一句话概括：**相似的样本，输出也相似。**

它依赖两个基本假设：

1. 样本可以表示为特征空间中的点，且存在有意义的距离度量；
2. 局部邻域内的样本输出近似一致（局部平滑性假设）。

形式化地，设训练集为

$$
D=\{(x_i,y_i)\}_{i=1}^{n},\quad x_i\in\mathbb{R}^{d}
$$

对查询样本 $x$，按距离 $d(x,x_i)$ 升序排列，取前 $k$ 个样本构成近邻集合 $N_k(x)$。

**分类**采用投票：

$$
\hat{y}=\arg\max_{c\in\mathcal{Y}}\sum_{(x_i,y_i)\in N_k(x)} w_i\,\mathbb{I}(y_i=c)
$$

**回归**采用加权平均：

$$
\hat{y}=\frac{\sum_{(x_i,y_i)\in N_k(x)} w_i y_i}{\sum_{(x_i,y_i)\in N_k(x)} w_i}
$$

其中 $w_i=1$ 为等权投票，$w_i=1/d(x,x_i)$ 为距离加权。直观上，距离越近的邻居话语权越大。

KNN 的三个核心要素：

| 要素 | 作用 | 常见选择 |
|---|---|---|
| 距离度量 | 定义“相似” | 欧氏距离、曼哈顿距离、余弦距离 |
| $k$ 值 | 控制邻域大小与决策边界平滑程度 | 交叉验证选择，二分类常取奇数 |
| 决策规则 | 汇总邻居输出 | 多数投票、距离加权投票、均值 |

> 注意：KNN 是**非参数模型**，但并非“没有超参数”。$k$、距离度量、权重方式都需要人为设定或调优。

### 1.2 分类问题的处理流程

给定训练集 $D$ 和查询样本 $x$：

1. **预处理**：按训练集统计量对特征做缩放（KNN 对量纲敏感，详见第四章）。
2. **计算距离**：计算 $x$ 到所有训练样本的距离 $d(x,x_i)$，暴力计算复杂度为 $O(nd)$。
3. **选取近邻**：按距离升序排序，取前 $k$ 个；也可用堆、KD 树或 Ball 树加速。
4. **加权投票**：统计近邻中各类别的票数；使用距离权重时，按 $1/d$ 累加。
5. **输出类别**：取票数最高的类别。

流程示意：

```text
训练集（存储）────────────────────────────┐
                                          │
查询样本 x ──► 计算 d(x, x_i) ──► 排序取前 k 个 ──► 按类别加权投票 ──► 输出类别
```

伪代码：

```python
for x in X_query:
    distances = [d(x, xi) for xi in X_train]
    neighbors = argsort(distances)[:k]
    votes = aggregate(y_train[neighbors], weights=1 / (distances[neighbors] + eps))
    y_pred = argmax(votes)
```

复杂度：

- 训练：$O(1)$（仅存储；建树为 $O(n\log n)$ 量级）；
- 预测：暴力搜索 $O(nd)$，排序 $O(n\log n)$，空间 $O(nd)$；
- 因此 KNN 的瓶颈在**预测阶段**，而不是训练阶段。

### 1.3 回归问题的处理流程

前 3 步与分类完全一致，区别只在第 4 步：

- 等权回归：$\hat{y}=\frac{1}{k}\sum_{i\in N_k(x)} y_i$；
- 距离加权回归：$\hat{y}=\frac{\sum w_i y_i}{\sum w_i}$，$w_i=1/d(x,x_i)$。

需要特别注意：KNN 回归的预测值一定落在近邻标签的取值范围内，因此**无法外推**。如果训练标签在 0～100 之间，模型不可能预测出 150。数据边界处还会出现明显偏差，因为边界样本的邻居只分布在一侧。

适用场景：低维、局部平滑、样本量中等的连续值预测；不适用：需要趋势外推、特征维度很高或噪声很大的任务。

### 1.4 $k$ 值的影响

$k$ 是 KNN 最重要的超参数，直接控制偏差-方差权衡：

| $k$ 值 | 决策边界 | 偏差 | 方差 | 训练误差 | 主要风险 |
|---|---|---|---|---|---|
| $k=1$ | 最复杂，贴合每个训练样本 | 低 | 高 | 0 | 过拟合，对噪声和异常值极敏感 |
| $k$ 增大 | 逐渐平滑 | 升高 | 降低 | 升高 | 欠拟合；类别不平衡时偏向多数类 |
| $k=n$ | 常数（多数类或全局均值） | 最高 | 最低 | 高 | 完全欠拟合 |

经验做法：

- 二分类取奇数，降低平票概率；
- 从 3～15 或 $\sqrt{n}$ 附近开始粗搜，再用交叉验证细化；
- 类别不平衡时，大 $k$ 会淹没少数类，可改用距离加权、重采样或调整决策阈值；
- $k$ 与距离度量、特征缩放相互影响，建议联合调参（见第五章）。

### 1.5 优缺点与适用场景

**优点：**

- 无需显式训练，新增样本只需加入训练集；
- 天然支持多分类，无需一对多拆分；
- 决策边界非线性，能拟合复杂的局部结构；
- 非参数方法，不假设数据服从某种分布；
- 有一定可解释性：可以给出“最近的邻居是谁”，适合相似病例、相似用户等业务解释。

**缺点：**

- 预测成本随训练集规模线性增长，内存需常驻全量训练数据；
- 对特征尺度、无关特征、噪声和异常值高度敏感；
- 高维空间中距离区分度下降（维数灾难）；
- 类别不平衡时多数类主导投票；
- 回归无法外推；
- 需要选择 $k$ 与距离度量，且没有显式的特征重要性。

**适用场景：**

- 小到中等规模、低维、样本相似度有明确业务含义的任务；
- 相似商品/内容推荐、图像检索、文本分类（余弦距离 + TF-IDF）；
- 异常检测（远离大多数邻居的样本）；
- 缺失值填补（`KNNImputer`）；
- 作为复杂模型之前的强基线。

**不适用场景：**

- 千万级样本、高维稀疏特征、强实时低延迟预测；
- 需要外推的回归任务；
- 特征量纲不可比且无法统一缩放的数据。

### 1.6 从零实现 KNN（理解原理）

下面用 NumPy 实现一个极简分类器，支持等权与距离加权投票。它只用于理解算法，生产环境应使用 scikit-learn。

```python
import numpy as np


class KNNClassifier:
    """极简 KNN 分类器：支持 uniform / distance 加权投票。"""

    def __init__(self, n_neighbors=5, weights="uniform"):
        self.n_neighbors = n_neighbors
        self.weights = weights

    def fit(self, X, y):
        self.X_train_ = np.asarray(X, dtype=float)
        self.y_train_ = np.asarray(y)
        self.classes_ = np.unique(self.y_train_)
        return self

    def _predict_one(self, x):
        dist = np.linalg.norm(self.X_train_ - x, axis=1)
        idx = np.argsort(dist)[: self.n_neighbors]
        labels, d = self.y_train_[idx], dist[idx]
        if self.weights == "uniform":
            w = np.ones_like(d)
        else:
            w = 1.0 / (d + 1e-12)
        scores = np.array([w[labels == c].sum() for c in self.classes_])
        return self.classes_[np.argmax(scores)]

    def predict(self, X):
        X = np.asarray(X, dtype=float)
        return np.array([self._predict_one(x) for x in X])
```

在鸢尾花数据上验证，并与 scikit-learn 对照：

```python
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier as SklearnKNN
from sklearn.preprocessing import StandardScaler

X, y = load_iris(return_X_y=True)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=0
)

scaler = StandardScaler().fit(X_train)
X_train_s = scaler.transform(X_train)
X_test_s = scaler.transform(X_test)

mine = KNNClassifier(n_neighbors=5).fit(X_train_s, y_train)
sklearn_model = SklearnKNN(n_neighbors=5).fit(X_train_s, y_train)

print("自实现 :", accuracy_score(y_test, mine.predict(X_test_s)))
print("sklearn:", accuracy_score(y_test, sklearn_model.predict(X_test_s)))
```

两者结果应当非常接近。差异可能来自平票处理：`np.argmax` 与 scikit-learn 内部的平票规则未必完全一致。这也说明，**在二分类中取奇数 $k$** 是简单有效的工程习惯。

---

## 二、scikit-learn 中的 KNN API

### 2.1 相关类总览

| 类 / 函数 | 所在模块 | 用途 |
|---|---|---|
| `KNeighborsClassifier` | `sklearn.neighbors` | KNN 分类 |
| `KNeighborsRegressor` | `sklearn.neighbors` | KNN 回归 |
| `RadiusNeighborsClassifier` | `sklearn.neighbors` | 固定半径内的邻居投票分类 |
| `RadiusNeighborsRegressor` | `sklearn.neighbors` | 固定半径内的邻居均值回归 |
| `NearestNeighbors` | `sklearn.neighbors` | 无监督近邻检索，返回距离与索引 |
| `KDTree` / `BallTree` | `sklearn.neighbors` | 底层空间索引结构 |
| `KNeighborsTransformer` | `sklearn.neighbors` | 将“近邻关系”转换为特征，可接入 Pipeline |
| `DistanceMetric` | `sklearn.neighbors` | 距离度量的底层接口 |
| `KNNImputer` | `sklearn.impute` | 基于近邻的缺失值填补 |

日常使用最多的是 `KNeighborsClassifier` 与 `KNeighborsRegressor`，二者的参数几乎完全一致：

```python
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor

clf = KNeighborsClassifier(
    n_neighbors=5,
    weights="uniform",
    algorithm="auto",
    leaf_size=30,
    p=2,
    metric="minkowski",
    metric_params=None,
    n_jobs=None,
)
```

### 2.2 关键参数说明

| 参数 | 含义 | 常用取值 | 说明 |
|---|---|---|---|
| `n_neighbors` | 邻居数量 $k$ | 3～15，常取奇数 | 越大越平滑；不能超过训练样本数 |
| `weights` | 投票权重 | `"uniform"` / `"distance"` / 可调用对象 | `distance` 按 $1/d$ 加权，近邻影响更大 |
| `algorithm` | 近邻搜索算法 | `"auto"`（默认） | `"brute"`、`"kd_tree"`、`"ball_tree"` |
| `leaf_size` | 树的叶子大小 | 30 | 影响建树与查询速度、内存，不改变预测结果 |
| `p` | 闵可夫斯基距离指数 | 2 | $p=1$ 曼哈顿，$p=2$ 欧氏，仅当 `metric="minkowski"` 时生效 |
| `metric` | 距离度量 | `"minkowski"` | 也可取 `"euclidean"`、`"manhattan"`、`"cosine"` 等 |
| `metric_params` | 度量的额外参数 | `None` | 如马氏距离的 `VI`、闵可夫斯基的 `w` |
| `n_jobs` | 并行任务数 | `None` / `-1` | 主要加速暴力搜索；树结构构建不并行 |

`algorithm` 的选择原则：

- `"auto"`：让 scikit-learn 根据数据规模、维度和度量自动选择，通常够用；
- `"brute"`：暴力搜索，支持全部度量，适合高维、稀疏数据或自定义度量；
- `"kd_tree"`：低维（大致 $d<20$）稠密数据上查询快；
- `"ball_tree"`：维度稍高时通常优于 KD 树，但高维仍会退化。

> 余弦距离、马氏距离等不被树结构支持，`auto` 会自动退化为 `brute`；显式指定 `algorithm="brute"` 可以避免警告并让意图更清晰。

### 2.3 标准工作流与常用方法

```python
from sklearn.neighbors import KNeighborsClassifier

# 假设 X_train_s / X_test_s 已完成与训练集一致的缩放
knn = KNeighborsClassifier(n_neighbors=5, weights="distance")
knn.fit(X_train_s, y_train)              # 训练：存数据（或建索引）

y_pred = knn.predict(X_test_s)           # 预测类别
proba = knn.predict_proba(X_test_s)      # 各类别投票占比
dist, idx = knn.kneighbors(X_test_s[:1]) # 最近邻的距离与训练集索引
score = knn.score(X_test_s, y_test)      # 分类准确率
```

| 方法 | 作用 | 返回 |
|---|---|---|
| `fit(X, y)` | 训练，保存训练数据、构建索引 | `self` |
| `predict(X)` | 预测标签 | 形状 `(n_samples,)` |
| `predict_proba(X)` | 类别概率（邻居投票占比） | 形状 `(n_samples, n_classes)` |
| `kneighbors(X, n_neighbors=None)` | 查询最近邻 | `(distances, indices)` |
| `score(X, y)` | 分类为准确率，回归为 $R^2$ | `float` |

几点说明：

- `classes_` 会按标签排序，`predict_proba` 的列顺序与 `classes_` 一致；
- `predict_proba` 只是邻居票数占比，**不是经过校准的概率**；
- 当 `weights="distance"` 且存在距离为 0 的邻居时，scikit-learn 会给这些零距离邻居权重 1，其余邻居权重 0。

### 2.4 分类实现：鸢尾花

```python
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.datasets import load_iris
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

iris = load_iris()
X, y = iris.data, iris.target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5, weights="distance")),
])
pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)

print("accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred, target_names=iris.target_names))

print("前 3 个样本的类别概率:")
print(pipe.predict_proba(X_test[:3]).round(3))
print("第一个测试样本的 5 个邻居索引:", pipe.named_steps["knn"].kneighbors(
    pipe.named_steps["scaler"].transform(X_test[:1])
)[1])
```

参考输出（4 个特征，鸢尾花任务较简单）：

```text
accuracy: 1.0
              precision    recall  f1-score   support

      setosa       1.00      1.00      1.00        13
  versicolor       1.00      1.00      1.00        13
   virginica       1.00      1.00      1.00        12

    accuracy                           1.00        38
```

为了直观看到决策边界，下面只取前两个特征（萼片长度、萼片宽度）训练并绘制。注意：只用 2 个特征会损失信息，准确率通常低于 4 个特征的版本，这里的目的只是可视化。

```python
X2 = iris.data[:, :2]
X2_train, X2_test, y2_train, y2_test = train_test_split(
    X2, y, test_size=0.25, stratify=y, random_state=42
)

pipe2 = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=15)),
])
pipe2.fit(X2_train, y2_train)

x_min, x_max = X2[:, 0].min() - 0.5, X2[:, 0].max() + 0.5
y_min, y_max = X2[:, 1].min() - 0.5, X2[:, 1].max() + 0.5
xx, yy = np.meshgrid(
    np.arange(x_min, x_max, 0.02),
    np.arange(y_min, y_max, 0.02),
)
Z = pipe2.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)

cmap_light = ListedColormap(["#FFE0E0", "#E0FFE0", "#E0E0FF"])
cmap_bold = ListedColormap(["#FF4444", "#44AA44", "#4444FF"])

plt.figure(figsize=(7, 5))
plt.contourf(xx, yy, Z, cmap=cmap_light, alpha=0.8)
plt.scatter(X2[:, 0], X2[:, 1], c=y, cmap=cmap_bold, edgecolor="k", s=30)
plt.xlabel("sepal length")
plt.ylabel("sepal width")
plt.title("KNN decision boundary (k=15, 2 features)")
plt.show()
```

从图中可以直观看到：$k$ 越大，边界越平滑；$k$ 越小，边界越贴合局部样本。

### 2.5 回归实现：正弦曲线

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error
from sklearn.neighbors import KNeighborsRegressor

rng = np.random.RandomState(0)
X = np.sort(5 * rng.rand(80, 1), axis=0)
y = np.sin(X).ravel()
y[::5] += 0.5 * (0.5 - rng.rand(16))   # 人为加入噪声

X_plot = np.linspace(0, 5, 500)[:, np.newaxis]

plt.figure(figsize=(8, 5))
plt.scatter(X, y, s=20, edgecolor="k", label="training data")

for k, weights, style in [
    (1, "uniform", ":"),
    (5, "uniform", "--"),
    (5, "distance", "-"),
]:
    model = KNeighborsRegressor(n_neighbors=k, weights=weights).fit(X, y)
    y_plot = model.predict(X_plot)
    train_mae = mean_absolute_error(y, model.predict(X))
    plt.plot(X_plot, y_plot, style, label=f"k={k}, weights={weights}")
    print(f"k={k}, {weights:8s}: train MAE = {train_mae:.4f}")

plt.legend()
plt.xlabel("x")
plt.ylabel("y")
plt.title("KNN Regression")
plt.show()
```

观察要点：

- $k=1$ 时曲线穿过所有训练点，训练误差为 0，但被噪声拉扯得剧烈抖动，是典型过拟合；
- $k=5$ 时曲线平滑很多，距离加权在数据密集处更贴合；
- 在训练数据范围之外，所有模型都退化为常数，验证了 KNN 回归**不能外推**；
- 多特征回归必须先缩放，否则距离会被大量纲特征主导（见第四章）。

### 2.6 API 使用要点

- **必须缩放特征**：KNN 直接在原始特征空间算距离，量纲不一致会严重扭曲近邻关系。
- **优先使用 Pipeline**：把缩放器和 KNN 封装在一起，保证训练、验证、推理使用同一套变换。
- **注意 $k$ 的上限**：`n_neighbors` 不能超过训练样本数；交叉验证时不能超过最小训练折的样本数。
- **大数据预测慢**：训练集几十万条以上时，暴力搜索的延迟可能不可接受；可减少特征、使用树索引，或改用近似最近邻（faiss、hnswlib 等）。
- **稀疏数据**：树结构不支持稀疏输入；文本等高维稀疏场景通常使用 `algorithm="brute"` + `metric="cosine"`。
- **自定义距离**：可将可调用函数传给 `metric`，或用 `metric="precomputed"` 直接传入距离矩阵；前者更慢，且不利于并行。
- **模型持久化**：使用 `joblib.dump` / `joblib.load` 保存整个 Pipeline，避免推理时漏掉缩放步骤。

---

## 三、距离度量

### 3.1 距离的基本要求

严格的距离度量 $d(\cdot,\cdot)$ 通常要求满足：

1. **非负性**：$d(x,y)\ge 0$，且 $d(x,y)=0 \iff x=y$；
2. **对称性**：$d(x,y)=d(y,x)$；
3. **三角不等式**：$d(x,z)\le d(x,y)+d(y,z)$。

余弦距离 $1-\cos(x,y)$ 不满足严格的同一性与三角不等式，严格说不是度量，但在工程中广泛作为“相似度”使用。理解这一点有助于避免对结果做过度理论化的解释。

### 3.2 常用距离及适用场景

设 $x,y\in\mathbb{R}^{d}$。

| 距离 | 定义 | scikit-learn 写法 | 适用场景 |
|---|---|---|---|
| 欧氏距离 | $\sqrt{\sum_i (x_i-y_i)^2}$ | `metric="euclidean"`，或 `p=2` | 连续、稠密、低维、各维量纲一致 |
| 曼哈顿距离 | $\sum_i \lvert x_i-y_i\rvert$ | `metric="manhattan"`，或 `p=1` | 高维稀疏、异常值较多、网格型特征 |
| 切比雪夫距离 | $\max_i \lvert x_i-y_i\rvert$ | `metric="chebyshev"` | 关注最大单项偏差，如质量控制 |
| 闵可夫斯基距离 | $(\sum_i \lvert x_i-y_i\rvert^{p})^{1/p}$ | `metric="minkowski", p=p` | 用 $p$ 统一搜索 L1/L2 族 |
| 余弦距离 | $1-\frac{x\cdot y}{\lVert x\rVert_2\lVert y\rVert_2}$ | `metric="cosine"` | 文本 TF-IDF、方向相似、模长无意义 |
| 汉明距离 | 不同位置所占比例 | `metric="hamming"` | 等长编码、类别/布尔特征 |
| 杰卡德距离 | $1-\frac{\lvert A\cap B\rvert}{\lvert A\cup B\rvert}$ | `metric="jaccard"` | 集合、布尔特征、标签集合 |
| 马氏距离 | $\sqrt{(x-y)^\top\Sigma^{-1}(x-y)}$ | `metric="mahalanobis", metric_params={"VI": VI}` | 特征相关、协方差结构重要 |
| 标准化欧氏 | $\sqrt{\sum_i (x_i-y_i)^2/V_i}$ | `metric="seuclidean", metric_params={"V": V}` | 各维方差差异大，且不便整体标准化 |

补充：

- `nan_euclidean`：允许缺失值，`KNNImputer` 默认使用；
- 编辑距离、DTW 等序列距离不在 scikit-learn 内置 KNN 的度量列表中，需要自定义或预计算距离矩阵；
- 马氏距离需要估计协方差逆矩阵，时间复杂度约为 $O(d^3)$，高维时成本高且协方差估计不稳定。

### 3.3 如何选择距离

可以按数据形态快速判断：

| 数据特点 | 优先尝试 | 原因 |
|---|---|---|
| 连续稠密、低维、各维可比 | 欧氏距离 | 几何直觉清晰，计算高效 |
| 特征独立、异常值多、希望更稳健 | 曼哈顿距离 | 对单个大偏差的惩罚是线性的 |
| 文本、词袋、TF-IDF、高维稀疏 | 余弦距离 | 只关心方向，忽略文档长度 |
| 布尔/集合特征 | 杰卡德、汉明 | 直接刻画集合重叠或位置差异 |
| 特征强相关、尺度不一 | 马氏距离 | 用协方差消除相关性与尺度影响 |
| 不确定 | 交叉验证对比 | 度量必须与数据语义匹配，不能只看理论 |

一个常见误区是“余弦距离适合所有高维数据”。实际上，如果特征模长本身携带信息（例如鸢尾花的花瓣尺寸），余弦距离会丢掉这部分信息，效果可能明显下降。**度量选择要以数据语义为准，并用验证集验证。**

### 3.4 高维问题：距离集中

随着维度升高，样本间距离趋于集中：最近邻与最远邻的距离之比接近 1，邻居不再“显著更近”，KNN 的局部性假设失效。这就是**维数灾难**在 KNN 中的具体表现。

缓解手段：

- 特征选择，去掉无关或噪声特征；
- PCA 等线性降维，或使用自编码器；
- 使用更适合高维的度量（余弦、马氏）；
- 度量学习（如 LMNN）；
- 增加样本量（高维下所需样本量随维度指数增长）；
- 改用对高维更稳健的模型（线性模型、树模型、神经网络）。

### 3.5 代码：距离计算与度量对比

```python
import numpy as np
from sklearn.metrics import pairwise_distances

X = np.array([[0.0, 0.0], [3.0, 4.0], [1.0, 1.0]])

for name, kwargs in {
    "euclidean": {},
    "manhattan": {},
    "chebyshev": {},
    "minkowski(p=3)": {"p": 3},
    "cosine": {},
}.items():
    metric = "minkowski" if name.startswith("minkowski") else name
    D = pairwise_distances(X, metric=metric, **kwargs)
    print(f"{name}:\n{np.round(D, 3)}\n")
```

在鸢尾花上比较不同度量（统一标准化，保证比较公平）：

```python
from sklearn.datasets import load_iris
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X, y = load_iris(return_X_y=True)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for metric in ["euclidean", "manhattan", "chebyshev", "cosine"]:
    pipe = make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(n_neighbors=5, metric=metric, algorithm="brute"),
    )
    scores = cross_val_score(pipe, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    print(f"{metric:10s}: {scores.mean():.3f} ± {scores.std():.3f}")
```

参考输出（数值随版本和切分变化）：

```text
euclidean : 0.953 ± 0.025
manhattan : 0.947 ± 0.034
chebyshev : 0.947 ± 0.025
cosine    : 0.933 ± 0.038
```

余弦距离在这个任务上略差，因为鸢尾花的特征模长包含类别信息，归一化方向反而损失了信息。这正说明度量要与数据语义匹配。

文本场景使用余弦距离的典型写法：

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import KNeighborsClassifier

corpus = [
    "机器学习 监督 学习 分类",
    "深度学习 神经网络 训练",
    "KNN 最近邻 分类 算法",
    "支持向量机 分类 间隔",
    "卷积 神经网络 图像 识别",
    "Transformer 注意力 模型",
]
labels = ["ml", "dl", "ml", "ml", "dl", "dl"]

vectorizer = TfidfVectorizer()
X_text = vectorizer.fit_transform(corpus)

clf = KNeighborsClassifier(
    n_neighbors=1, metric="cosine", algorithm="brute"
).fit(X_text, labels)

query = vectorizer.transform(["最近邻 分类 算法"])
print(clf.predict(query))   # ['ml']
```

### 3.6 距离加权与注意事项

- `weights="distance"` 使用 $w=1/d$，让更近的邻居拥有更大话语权，常用于类别不平衡或局部结构明显的任务；
- 若存在重复样本，距离为 0，scikit-learn 会给这些零距离邻居权重 1、其余为 0，相当于只在重复样本中投票；
- 自定义度量虽然灵活，但通常比内置度量慢，且并行效率低，生产环境应优先使用内置度量；
- 使用 `metric="precomputed"` 时，`fit` 传入的是训练集内部的 $n\times n$ 距离矩阵，`predict` 传入的是待预测样本到训练样本的 $m\times n$ 距离矩阵，形状必须严格匹配。

---

## 四、特征预处理

### 4.1 为什么 KNN 对量纲敏感

KNN 完全依赖距离。如果各特征的单位和数值范围差异很大，距离会被数值范围大的特征主导。

例如两个样本：

- A =（身高 170 cm，年收入 5,000 元）
- B =（身高 175 cm，年收入 30,000 元）

原始欧氏距离：

$$
d=\sqrt{(170-175)^2+(5000-30000)^2}\approx 25000.0005
$$

身高差异 5 cm 在 25000 的距离中几乎完全被淹没，KNN 实际上只按收入找邻居，身高的作用接近于零。

若把身高除以 10、收入除以 10000，得到 (17, 0.5) 与 (17.5, 3.0)，距离约为 2.55，两个特征都能对距离产生实质影响。

> 标准化本质上是在**人为设定特征权重**。它假设各特征同等重要；如果业务上某特征更重要，应通过特征加权或领域缩放来体现，而不是盲目标准化。

### 4.2 常用预处理方法

| 方法 | 变换 | 输出范围 | 优点 | 局限与适用场景 |
|---|---|---|---|---|
| `MinMaxScaler` | $(x-\min)/(\max-\min)$，可映射到指定区间 | 默认 $[0,1]$ | 保留分布形状、有界 | 对异常值敏感；适合像素、有界特征、小数据集 |
| `StandardScaler` | $(x-\mu)/\sigma$ | 均值 0、方差 1 | 通用，配合距离/正则/ PCA | 均值方差受异常值影响；适合近似对称分布，大数据集|
| `MaxAbsScaler` | $x/\max\lvert x\rvert$ | $[-1,1]$ | 保持稀疏结构 | 稀疏数据（TF-IDF、One-Hot） |
| `RobustScaler` | $(x-\text{median})/\text{IQR}$ | 中位数 0 | 抗异常值 | 异常值较多、分布偏斜 |
| `Normalizer` | 按行做 L1/L2/max 归一化 | 单位范数 | 消除样本模长影响 | 文本/方向相似；不改变单样本内特征比例 |
| `QuantileTransformer` | 分位数映射 | 均匀或正态 | 抗异常值、可处理非线性 | 改变分布形状；需要足够样本 |
| `PowerTransformer` | Yeo-Johnson / Box-Cox | 近似正态 | 稳定方差、降低偏态 | Box-Cox 仅适用于正数；会改变可解释性 |

`fit` / `transform` 的语义：

- `fit`：在**训练集**上学习统计量（最小值、最大值、均值、标准差、中位数、四分位距、分位数等）；
- `transform`：用学到的统计量变换数据；
- `fit_transform`：仅用于训练集；测试集和推理数据只能 `transform`。

### 4.3 预处理对 KNN 的影响

1. **均衡各特征贡献**：标准化后，距离不再被大量纲特征垄断，KNN 才能“看到”所有特征。
2. **异常值会破坏统计量**：`StandardScaler` 的均值和方差对极端值敏感，异常值多时优先 `RobustScaler` 或 `QuantileTransformer`。
3. **稀疏数据不能随意中心化**：`StandardScaler(with_mean=True)` 会把稀疏矩阵稠密化，造成内存爆炸；应使用 `MaxAbsScaler` 或 `StandardScaler(with_mean=False)`。
4. **训练与推理必须一致**：缩放器要和模型一起保存；推理时先 `transform` 再送入 KNN。
5. **交叉验证必须防泄漏**：缩放器只能 `fit` 在每折的训练部分。正确做法是把缩放器放进 `Pipeline`，让交叉验证自动处理；先在全量数据上缩放再切分，会把验证折的统计信息泄漏进训练。
6. **类别特征**：One-Hot 后的欧氏距离与汉明距离单调对应；高基数类别直接 One-Hot 会让距离被大量稀有类别稀释，建议先做目标编码、嵌入或业务归并。
7. **缺失值**：KNN 不能直接处理 NaN（除 `nan_euclidean` 外）；可用 `KNNImputer` 先填补，再缩放。`KNNImputer` 默认用 `nan_euclidean` 忽略缺失维，`n_neighbors` 控制参与填补的邻居数。
8. **分布变换**：对严重偏态特征，`QuantileTransformer` / `PowerTransformer` 可能提升近邻质量，但会降低可解释性，且需要足够样本估计分位数。
9. **标准化不能替代特征选择**：无关特征标准化后仍然是无关特征，甚至会因为方差被放大而带来噪声；高维时应配合特征选择或 PCA。

### 4.4 对比实验：Wine 数据集

Wine 数据集的 13 个特征单位和量级差异明显（酒精浓度、苹果酸、灰分、镁、脯氨酸等），非常适合观察缩放的作用。

```python
from sklearn.datasets import load_wine
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

X, y = load_wine(return_X_y=True)
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

for name, scaler in [
    ("raw", None),
    ("minmax", MinMaxScaler()),
    ("standard", StandardScaler()),
    ("robust", RobustScaler()),
]:
    steps = [] if scaler is None else [scaler]
    pipe = make_pipeline(*steps, KNeighborsClassifier(n_neighbors=5))
    scores = cross_val_score(pipe, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    print(f"{name:9s}: {scores.mean():.4f} ± {scores.std():.4f}")
```

参考输出（实际数值随版本与切分变化）：

```text
raw      : 0.719 ± 0.045
minmax   : 0.944 ± 0.031
standard : 0.972 ± 0.024
robust   : 0.961 ± 0.028
```

结论：

- 未缩放时 KNN 只有约 0.72，距离被大量纲特征主导；
- 缩放后提升到 0.94～0.97，说明预处理对 KNN 是**决定性**的；
- 本数据上 `StandardScaler` 略优，但差距不大；异常值更多时应优先尝试 `RobustScaler`；
- 不要只看均值，标准差同样重要；差距在 1 个标准差以内时，优先选择更简单、更稳定的方案。

### 4.5 预处理检查清单

- [ ] 训练集 `fit`，验证/测试集只 `transform`
- [ ] 缩放器与模型封装进 `Pipeline`
- [ ] 检查特征量纲与异常值比例
- [ ] 稀疏数据使用 `MaxAbsScaler` 或 `with_mean=False`
- [ ] 类别特征先编码，高基数类别谨慎 One-Hot
- [ ] 缺失值先填补（`KNNImputer` 或业务规则）
- [ ] 高维数据配合特征选择 / PCA
- [ ] 保存完整 Pipeline，而不是只保存 KNN 模型

---

## 五、超参数选择方法

### 5.1 数据集划分与评估协议

标准的做法是把数据分为三部分：

| 集合 | 用途 | 使用频率 |
|---|---|---|
| 训练集 | 拟合模型与缩放器 | 每次训练 |
| 验证集（或交叉验证） | 选择超参数、比较模型 | 调参阶段反复使用 |
| 测试集 | 最终评估泛化能力 | 只在最后使用一次 |

常见错误是直接在测试集上试不同的 $k$，然后报告最好的那个结果。这相当于把测试集当验证集用，评估会偏乐观。正确顺序是：

1. 在训练集内部用交叉验证调参；
2. 确定超参数后，在训练集上重新拟合；
3. 只在测试集上评估一次。

如果数据结构特殊，切分方式也要调整：

- 类别不平衡：使用分层切分 `stratify=y` 或 `StratifiedKFold`；
- 时序数据：使用 `TimeSeriesSplit`，不能用随机打乱；
- 分组数据（同一用户/同一设备多条样本）：使用 `GroupKFold`，避免同组样本同时出现在训练和验证中。

### 5.2 交叉验证

K 折交叉验证的流程：

1. 将训练集分成 $K$ 份（分类任务分层）；
2. 每次取 1 份作验证集，其余 $K-1$ 份训练；
3. 重复 $K$ 次，得到 $K$ 个验证分数；
4. 用均值衡量模型性能，用标准差衡量稳定性。

```python
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_validate

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

scores = cross_val_score(
    pipe, X_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1
)
print(f"CV accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

results = cross_validate(
    pipe, X_train, y_train, cv=cv,
    scoring=["accuracy", "f1_macro"],
    return_train_score=True,
    n_jobs=-1,
)
print("test accuracy:", results["test_accuracy"].mean())
print("train accuracy:", results["train_accuracy"].mean())
print("test f1_macro:", results["test_f1_macro"].mean())
```

要点：

- 分类任务默认会使用分层 K 折，但显式写出 `StratifiedKFold` 更清晰；
- 数据量小可用 5 折或 10 折；留一法（LOOCV）方差大、成本高，通常不必要；
- 类别不平衡时，准确率可能误导，改用 `f1_macro`、`balanced_accuracy` 或 `roc_auc`；
- 训练分数与验证分数的差距可以判断过拟合/欠拟合；
- 比较模型时同时看均值和标准差，差距小于 1 个标准差时优先选择更简单的模型（1-SE 规则）。

### 5.3 网格搜索 GridSearchCV

`GridSearchCV` 会穷举参数组合，对每组参数做交叉验证，最后用最优参数在全部训练数据上重新拟合。

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "knn__n_neighbors": [1, 3, 5, 7, 9, 11],
    "knn__weights": ["uniform", "distance"],
    "knn__p": [1, 2],
}

grid = GridSearchCV(
    estimator=pipe,
    param_grid=param_grid,
    cv=cv,
    scoring="accuracy",
    n_jobs=-1,
    return_train_score=True,
    verbose=1,
)
grid.fit(X_train, y_train)

print("best params:", grid.best_params_)
print("best CV score:", grid.best_score_)
```

关键参数：

| 参数 | 含义 | 建议 |
|---|---|---|
| `estimator` | 待调优模型，通常是 Pipeline | 缩放器放在 Pipeline 内 |
| `param_grid` | 参数字典 | Pipeline 中的参数用 `步骤名__参数名` |
| `cv` | 交叉验证策略 | 分类用 `StratifiedKFold(5)` |
| `scoring` | 评分指标 | 分类用 `accuracy` / `f1_macro`；回归用 `neg_mean_squared_error` / `r2` |
| `n_jobs` | 并行数 | `-1` 使用全部 CPU |
| `refit` | 是否用最优参数重新拟合 | 默认 `True`，之后可访问 `best_estimator_` |
| `return_train_score` | 是否记录训练分数 | 诊断过拟合时设为 `True` |
| `verbose` | 日志详细程度 | 大网格可设为 1～2 |

调参完成后：

```python
print(grid.best_estimator_)          # 已用最优参数在 X_train 上重新拟合
print(grid.best_score_)              # 最优参数的平均交叉验证分数
print(grid.best_params_)             # 最优参数组合

import pandas as pd
cv_table = pd.DataFrame(grid.cv_results_)
columns = [
    "param_knn__n_neighbors",
    "param_knn__weights",
    "param_knn__p",
    "mean_test_score",
    "std_test_score",
    "mean_train_score",
]
print(cv_table[columns].sort_values("mean_test_score", ascending=False).head(10))
```

注意：

- `best_score_` 是交叉验证分数，不是测试集分数，通常略偏乐观；
- 网格搜索的成本是“参数组合数 × 折数”次拟合；KNN 的 `fit` 很便宜，但每次验证都要做大量预测，仍可能很慢；
- 参数名必须与 Pipeline 中的步骤名一致，例如步骤名为 `"knn"`，则写成 `"knn__n_neighbors"`。

### 5.4 其他搜索策略

| 方法 | 特点 | 适用情况 |
|---|---|---|
| `GridSearchCV` | 穷举，结果稳定可复现 | 参数少、取值离散、网格小 |
| `RandomizedSearchCV` | 从分布中随机采样 `n_iter` 组 | 参数多、取值连续、网格爆炸 |
| 贝叶斯优化（Optuna 等） | 用历史结果指导下一步采样 | 训练成本高、想用更少尝试找到好参数 |
| `HalvingGridSearchCV` | 逐次减半，早期淘汰差组合 | 大网格、样本多（注意其版本状态） |

`RandomizedSearchCV` 示例：

```python
from scipy.stats import randint, loguniform
from sklearn.model_selection import RandomizedSearchCV

param_dist = {
    "knn__n_neighbors": randint(1, 31),
    "knn__weights": ["uniform", "distance"],
    "knn__p": [1, 2],
}
search = RandomizedSearchCV(
    pipe, param_dist, n_iter=30, cv=cv, scoring="accuracy",
    random_state=42, n_jobs=-1,
)
search.fit(X_train, y_train)
```

对 KNN 而言，参数空间通常不大，`GridSearchCV` 已经足够；随机搜索更适合与特征选择、降维等步骤联合调参的场景。

### 5.5 KNN 调参路线

建议按“先预处理、再距离、后 $k$、最后权重”的顺序，由粗到细：

| 阶段 | 调什么 | 建议范围 | 说明 |
|---|---|---|---|
| 1 | 缩放方式 | Standard / MinMax / Robust | 先确定必须缩放，再比较具体方法 |
| 2 | 距离度量 | 欧氏、曼哈顿、余弦 | 结合数据语义，用交叉验证确认 |
| 3 | `n_neighbors` | 1～30 的奇数，粗搜后细化 | 最重要的参数，先粗后细 |
| 4 | `weights` | uniform / distance | 距离加权常能提升，但可能放大噪声 |
| 5 | 特征工程 | 特征选择、PCA 维数 | 高维时优先做，可能比调 $k$ 更有效 |
| 6 | 速度参数 | `algorithm`、`leaf_size` | 只影响速度，不影响预测结果 |

调参思路：

- **一次只动一个因素**，否则难以判断收益来源；
- 先粗网格定位大致范围，再在最优值附近细化；
- 关注训练分数与验证分数的差距：训练高、验证低是过拟合，二者都低是欠拟合；
- 差距在 1 个标准差以内时，选择更简单的模型；
- 调参的目标是泛化性能，不是把交叉验证分数刷到最高；
- 小数据集上方差大，不要因为 0.5% 的提升就改变最终方案。

常见坑：

- 在测试集上调参，导致评估失真；
- 缩放器在交叉验证之外 `fit`，造成数据泄漏；
- 类别不平衡却只看准确率；
- 把 `best_score_` 当作最终泛化性能；
- 网格过大、收益递减，浪费算力。

### 5.6 综合案例：手写数字识别

本案例使用 scikit-learn 内置的 `digits` 数据集：1797 个样本，每个样本是 8×8 灰度图，展平为 64 维特征，像素值 0～16，共 10 个类别（数字 0～9），类别基本均衡。它比 MNIST 小得多，适合快速实验，但流程与真实图像分类一致。

#### 5.6.1 加载与可视化

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_digits

digits = load_digits()
X, y = digits.data, digits.target

print("X shape:", X.shape)          # (1797, 64)
print("image shape:", digits.images.shape)  # (1797, 8, 8)
print("class counts:", np.bincount(y))

fig, axes = plt.subplots(2, 5, figsize=(10, 4))
for ax, image, label in zip(axes.ravel(), digits.images, y):
    ax.imshow(image, cmap="gray_r")
    ax.set_title(f"label={label}")
    ax.axis("off")
plt.tight_layout()
plt.show()
```

#### 5.6.2 划分数据与建立基线

```python
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42
)

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

raw_scores = cross_val_score(
    KNeighborsClassifier(n_neighbors=5),
    X_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1,
)

scaled_pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier(n_neighbors=5)),
])
scaled_scores = cross_val_score(
    scaled_pipe, X_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1,
)

print(f"raw      CV: {raw_scores.mean():.4f} ± {raw_scores.std():.4f}")
print(f"scaled   CV: {scaled_scores.mean():.4f} ± {scaled_scores.std():.4f}")
```

参考输出：

```text
raw      CV: 0.9861 ± 0.0056
scaled   CV: 0.9861 ± 0.0056
```

这里缩放几乎没有提升，原因是 64 个像素特征的取值范围一致（都是 0～16），本身不存在量纲失衡。这从反面说明：**缩放的作用是消除量纲差异，而不是无条件提升精度**。如果换成一个特征量纲严重失衡的数据集（如 Wine），缩放会成为决定性的步骤。

#### 5.6.3 网格搜索调参

```python
from sklearn.model_selection import GridSearchCV

pipe = Pipeline([
    ("scaler", StandardScaler()),
    ("knn", KNeighborsClassifier()),
])

param_grid = {
    "knn__n_neighbors": [1, 3, 5, 7, 9, 11, 13, 15],
    "knn__weights": ["uniform", "distance"],
    "knn__p": [1, 2],
}

grid = GridSearchCV(
    pipe,
    param_grid,
    cv=cv,
    scoring="accuracy",
    n_jobs=-1,
    return_train_score=True,
    verbose=1,
)
grid.fit(X_train, y_train)

print("best params:", grid.best_params_)
print(f"best CV accuracy: {grid.best_score_:.4f}")
```

参考输出：

```text
best params: {'knn__n_neighbors': 3, 'knn__p': 2, 'knn__weights': 'distance'}
best CV accuracy: 0.9902
```

网格共 $8 \times 2 \times 2 = 32$ 组参数，5 折交叉验证共 160 次拟合与验证。

查看排序后的结果，理解参数影响：

```python
import pandas as pd

cv_table = pd.DataFrame(grid.cv_results_)
columns = [
    "param_knn__n_neighbors",
    "param_knn__weights",
    "param_knn__p",
    "mean_test_score",
    "std_test_score",
    "mean_train_score",
]
print(
    cv_table[columns]
    .sort_values("mean_test_score", ascending=False)
    .head(10)
    .to_string(index=False)
)
```

典型规律：

- $k=1$ 训练准确率为 1.0，但验证准确率略低，说明对噪声敏感；
- $k=3～7$ 通常处于最佳区间；
- `weights="distance"` 往往有小幅提升；
- $p=1$ 与 $p=2$ 的差距通常不大，说明该数据上两种度量的近邻结构相近；
- $k$ 继续增大到 15 以上时，验证分数开始下降，偏向欠拟合。

#### 5.6.4 测试集最终评估

```python
from sklearn.metrics import accuracy_score, classification_report, ConfusionMatrixDisplay

best_model = grid.best_estimator_
y_pred = best_model.predict(X_test)

print(f"test accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, digits=4))

ConfusionMatrixDisplay.from_predictions(
    y_test, y_pred, cmap="Blues", colorbar=False
)
plt.title("Confusion matrix (test set)")
plt.show()
```

参考输出：

```text
test accuracy: 0.9889
```

混淆矩阵中常见的错误是 8↔1、9↔8、5↔9 等，这些数字在手写时本身就容易混淆。错误样本往往笔画缺失、倾斜严重或书写潦草，说明模型已经接近该特征表示下的上限。

#### 5.6.5 错误样本分析

```python
errors = np.flatnonzero(y_pred != y_test)
print("error count:", len(errors))

fig, axes = plt.subplots(2, 4, figsize=(10, 5))
for ax, idx in zip(axes.ravel(), errors[:8]):
    ax.imshow(X_test[idx].reshape(8, 8), cmap="gray_r")
    ax.set_title(f"true={y_test[idx]}, pred={y_pred[idx]}")
    ax.axis("off")
for ax in axes.ravel()[len(errors[:8]):]:
    ax.axis("off")
plt.tight_layout()
plt.show()
```

错误分析的价值在于判断下一步方向：

- 如果错误集中在视觉上确实模糊的样本，应考虑更好的特征（HOG、方向梯度、去斜校正）或更强的模型；
- 如果错误呈现系统性（例如总是把某一类判成另一类），检查类别分布、特征表示和距离度量；
- 如果训练集与测试集错误率差距很大，检查是否过拟合或数据泄漏。

#### 5.6.6 $k$ 值曲线

固定 `weights="uniform"`、`p=2`，只观察 $k$ 的影响：

```python
k_values = list(range(1, 31, 2))
means, stds = [], []

for k in k_values:
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("knn", KNeighborsClassifier(n_neighbors=k)),
    ])
    scores = cross_val_score(
        model, X_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1
    )
    means.append(scores.mean())
    stds.append(scores.std())

plt.figure(figsize=(8, 5))
plt.errorbar(k_values, means, yerr=stds, marker="o", capsize=4)
plt.xlabel("n_neighbors (k)")
plt.ylabel("CV accuracy")
plt.title("KNN accuracy vs k")
plt.grid(alpha=0.3)
plt.show()

best_idx = int(np.argmax(means))
print(f"best k on CV: {k_values[best_idx]}, accuracy={means[best_idx]:.4f}")
```

解读：

- $k$ 很小时曲线抖动，方差大；
- $k$ 增大后曲线趋于平稳，随后缓慢下降；
- 最佳区间通常较宽，说明 KNN 对 $k$ 不是极度敏感；
- 最终选择应结合验证均值、标准差和模型简单性，而不是只取最高点。

#### 5.6.7 无偏评估：嵌套交叉验证

`GridSearchCV.best_score_` 已经用同一批数据选过参数，略有乐观偏差。若要得到更严格的泛化估计，可使用嵌套交叉验证：外层评估，内层调参。

```python
from sklearn.model_selection import cross_val_score

nested_scores = cross_val_score(
    grid, X, y,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=0),
    scoring="accuracy",
    n_jobs=-1,
)
print(f"nested CV: {nested_scores.mean():.4f} ± {nested_scores.std():.4f}")
```

代价是计算量成倍增加（外层 5 折 × 内层 160 次拟合）。数据量小、调参空间大时，嵌套交叉验证能更诚实地反映模型选择过程带来的偏差。

#### 5.6.8 保存与部署

```python
import joblib

joblib.dump(best_model, "knn_digits_pipeline.joblib")

loaded = joblib.load("knn_digits_pipeline.joblib")
print(loaded.predict(X_test[:5]))
```

部署要点：

- 保存整个 Pipeline（含缩放器），不要只保存 `KNeighborsClassifier`；
- 推理输入必须与训练时一致：8×8 图像展平为 64 维，像素范围 0～16；如果线上输入是 0～255，需要先做相同尺度的转换；
- `digits` 规模很小，推理很快；若换成 MNIST（70000×784），暴力 KNN 的延迟会明显上升，应考虑 PCA 降维、KD/Ball 树或近似最近邻；
- 监控输入分布漂移，例如扫描分辨率、笔迹风格变化，必要时重新训练。

#### 5.6.9 案例小结

| 项目 | 结论 |
|---|---|
| 数据 | 1797 个 8×8 手写数字，10 类，基本均衡 |
| 预处理 | 像素尺度一致，标准化收益很小；但仍建议放入 Pipeline，保证流程一致 |
| 最佳参数 | 通常在 $k=3～7$、`weights="distance"`、欧氏距离附近 |
| 测试准确率 | 约 0.98～0.99 |
| 主要错误 | 8/1、9/8、5/9 等视觉相似类别 |
| 改进方向 | HOG/去斜等特征、数据增强、SVM/CNN、近似最近邻加速 |

---

## 附录

### A. 环境与依赖

```text
python>=3.9
numpy>=1.24
scikit-learn>=1.3
matplotlib>=3.7
pandas>=2.0
```

安装：

```bash
pip install numpy scikit-learn matplotlib pandas
```

### B. API 速查

```python
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor, NearestNeighbors
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, MaxAbsScaler
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_score,
    cross_validate, GridSearchCV, RandomizedSearchCV,
)
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.impute import KNNImputer
```

最小分类模板：

```python
pipe = make_pipeline(
    StandardScaler(),
    KNeighborsClassifier(n_neighbors=5, weights="distance"),
)
pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)
```

最小回归模板：

```python
pipe = make_pipeline(
    StandardScaler(),
    KNeighborsRegressor(n_neighbors=5, weights="distance"),
)
pipe.fit(X_train, y_train)
y_pred = pipe.predict(X_test)
```

### C. 常见问题排查

| 现象 | 可能原因 | 处理方式 |
|---|---|---|
| 准确率异常低 | 未缩放特征、量纲差异大 | 加入 `StandardScaler` / `RobustScaler` |
| 交叉验证分数远高于测试分数 | 调参用了测试集、缩放泄漏 | 严格划分，缩放放入 Pipeline |
| 训练准确率 1.0，验证明显更低 | $k$ 过小、噪声/异常值 | 增大 $k$，使用距离加权或清洗异常值 |
| 验证准确率整体偏低 | $k$ 过大、特征不足 | 减小 $k$，增加有效特征 |
| 少数类几乎预测不到 | 类别不平衡，大 $k$ 偏向多数类 | 分层抽样、重采样、改用 `f1_macro` |
| `metric="cosine"` 报错或很慢 | 树结构不支持该度量 | 显式设置 `algorithm="brute"` |
| 稀疏数据内存爆掉 | 中心化导致稠密化 | `MaxAbsScaler` 或 `StandardScaler(with_mean=False)` |
| 预测延迟高 | 样本量大、维度高、暴力搜索 | 减特征、PCA、树索引、近似最近邻 |
| `n_neighbors` 报错 | $k$ 大于训练样本数 | 减小 $k$，检查切分后的训练规模 |
| 回归预测值范围过窄 | KNN 不能外推 | 改用线性/树模型或加入趋势特征 |

### D. 术语表

| 术语 | 含义 |
|---|---|
| 懒惰学习（Lazy Learning） | 训练阶段几乎不计算，预测阶段才处理数据 |
| 基于实例的学习（Instance-based Learning） | 直接用训练样本做预测，不学习显式参数 |
| 维数灾难（Curse of Dimensionality） | 维度升高后样本稀疏、距离区分度下降 |
| 偏差-方差权衡（Bias-Variance Tradeoff） | 模型复杂度与泛化误差之间的平衡 |
| 数据泄漏（Data Leakage） | 训练阶段使用了预测时不可获得的信息 |
| 嵌套交叉验证（Nested CV） | 外层评估、内层调参，得到更无偏的性能估计 |

### E. 参考资料

- scikit-learn 官方文档：Nearest Neighbors（User Guide 与 API）
- Hastie, Tibshirani, Friedman. *The Elements of Statistical Learning*, 第 2 章与第 13 章
- 周志华.《机器学习》. 第 1 章（懒惰学习）与第 10 章（降维与度量学习）
- Bishop. *Pattern Recognition and Machine Learning*，关于非参数方法与核方法的相关章节
