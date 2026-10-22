"""
案例：演示网格搜索 和 交叉验证。

交叉验证解释：
    原理：把数据分成 n 份，例如分成：4 份 → 也叫：4 折交叉验证。
        - 第 1 次：把第 1 份数据作为 **验证集（测试集）**，其它作为训练集，训练模型，模型预测，获取：准确率 → 准确率 1
        - 第 2 次：把第 2 份数据作为 **验证集（测试集）**，其它作为训练集，训练模型，模型预测，获取：准确率 → 准确率 2
        - 第 3 次：把第 3 份数据作为 **验证集（测试集）**，其它作为训练集，训练模型，模型预测，获取：准确率 → 准确率 3
        - 第 4 次：把第 4 份数据作为 **验证集（测试集）**，其它作为训练集，训练模型，模型预测，获取：准确率 → 准确率 4
    然后计算上述的 4 次准确率的 **平均值**，作为：模型最终的准确率。
    假设第 4 次最好（准确率最高），则：用全部数据（训练集 + 测试集）训练模型，再次用（第 4 次的）测试集对模型测试。

    目的:为了让模型的最终验真结果更准确。

网格搜索：
    目的/作用：寻找最优超参数。

    原理：接收超参可能出现的值，然后针对于超参的每个值进行 **交叉验证**，获取到 **最优超参组合**。

    超参数：需要用户手动录入的数据，不同的超参（组合），可能会影响模型的最终评测结果。

大白话解释：网格搜索 + 交叉验证，本质上指的是 **GridSearchCV** 这个 API，它会帮我们寻找最优超参（供参考）。

"""
# 导包
from sklearn.datasets import load_iris  #加载 鸢尾花 测试集
from sklearn.model_selection import train_test_split    # 分割训练和测试集
from sklearn.preprocessing import StandardScaler    # 数据标准化
from sklearn.neighbors import KNeighborsClassifier  # KNN分类对象
from sklearn.metrics import accuracy_score  # 模型评估

# 获取数据
iris_data = load_iris()

# 数据预处理 - 将数据按 8:2 切分成训练集和测试集
x_train, x_test, y_train, y_test = train_test_split(iris_data.data, iris_data.target, test_size=0.2, random_state=22)

# 特征工程 - 特征预处理 - 标准化
x_test = StandardScaler(x_test)
x_train = StandardScaler(x_train)

# 