"""
K近邻算法
    分类问题思路如下：
        给定训练集 D 和查询样本 x：
        1. 预处理：按训练集统计量对特征做缩放（KNN 对量纲敏感）。
        2. 计算距离：计算 x 到所有训练样本的距离 d(x,x_i)，暴力计算复杂度为 O(nd)。
        3. 选取近邻：按距离升序排序，取前 k 个；也可用堆、KD 树或 Ball 树加速。
        4. 加权投票：统计近邻中各类别的票数；使用距离权重时，按 1/d 累加。
        5. 输出类别：取票数最高的类别。
    
    代码实现思路：
        1. 导包
        2. 准备数组集(测试集 和 训练集)
        3. 创建模型对象
        4. 模型训练
        5. 模型预测
        6. 模型评估
"""

# 导包
from pyexpat import model

from sklearn.neighbors import KNeighborsClassifier

# 2. 准备数组集
x_train = [[0], [1], [2],[ 3]]  # 特征集, 每个样本两个特征
y_train = [0,1,1,1]     # 标签集

x_test = [[5]]  # 测试集

# 3. 创建模型对象
model = KNeighborsClassifier(n_neighbors=2)

# 4. 模型训练
model.fit(x_train, y_train)

# 5. 模型预测
y_test = model.predict(x_test)
print(f"预测值为：{y_test}")
proba  = model.predict_proba(x_train)
print(f"各类别投票占比:\n", proba)
dis_idx = model.kneighbors(x_train[:1])
print("距离与索引", dis_idx)
# 6. 模型评估




