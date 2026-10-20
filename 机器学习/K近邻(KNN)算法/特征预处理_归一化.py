"""
案例：演示特征预处理之 归一化操作

特征工程的目的 和 步骤
    目的：
        利用专业背景知识 和 技巧处理数据，用于提升模型的性能
    步骤：
        1.特征提取
        2.特征预处理
        3.特征降维
        4.特征选择
        5.特征组合

归一化：
    目的：
        防止因为 量纲(单位) 问题，导致特征列的方差值相差较大，影响模型的最终结果。将各列的值映射到 [0,1] 之间
    公式：
        x' = (x - x_min) / (x_max - x_min)
        x'' = x' * (max_x - min_x) * min_x
    公式解释：
        x' 是 归一化的结果，范围在 [0,1] 之间
        x'' 是最终结果，该结果在 人为控制 的 [min_x, max_x] 之间。

    弊端：
        容易受到最大值和最小值的影响，所以它一般用于处理 小数据集。
"""

# 导包
from sklearn.preprocessing import MinMaxScaler

# 准备数据集（归一化之前的数据）
x_tranin = [[90,2,10,40],[60,4,15,45],[75,3,13,46]]

# 创建归一化对象
scaler = MinMaxScaler(feature_range=(3,5))

# 对元数据集进行归一化操作
x_tranin_scaler = scaler.fit_transform(x_tranin)
print("归一化后的数据集：\n", x_tranin_scaler)
