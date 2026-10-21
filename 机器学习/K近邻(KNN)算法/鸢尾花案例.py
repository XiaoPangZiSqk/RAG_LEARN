"""
案例：通过KNN算法实现 鸢尾花 分类操作。

机器学习项目的研发流程
    1.加载数据
    2.数据的预处理
    3.特征工程
    4.模型训练
    5.模型评估
    6.模型预测
"""

# 导包
from sklearn.datasets import load_iris  #加载 鸢尾花 测试集
import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split    # 分割训练和测试集
from sklearn.preprocessing import StandardScaler    # 数据标准化
from sklearn.neighbors import KNeighborsClassifier  # KNN分类对象
from sklearn.metrics import accuracy_score  # 模型评估

# 1.定义函数，加载鸢尾花数据集，并查看数据集
def get_data_iris() :
    # 1.加载鸢尾花数据集
    iris_data = load_iris()
    # 2.查看数据集
    #print(f"鸢尾花数据集：\n", iris_data)   #字典类型, 共150条数据
    # print(f"包含的键：{iris_data.keys()}")
    # print(f"具体的特征：{iris_data.feature_names[:5]}")
    # print(f"具体数据：{iris_data.data[:5]}")
    # print(f"具体的标签：{iris_data.target[:5]}")
    # print(f"具体的标签名：{iris_data.target_names[:5]}")
    # 3.封装成 DataFrame 对象并返回
    return  iris_data


# 2.定义函数，绘制数据集的散点图
def show_iris_picture() :
    # 获取数据
    iris_data = get_data_iris()
    iris_data_df = pd.DataFrame(data=iris_data.data, columns=iris_data.feature_names)
    target_names = [iris_data.target_names[i] for i in iris_data.target]
    iris_data_df["target"] = target_names

    # 绘制散点图
    # 参1：数据集，参2：x轴，参3：y轴，参4：分组字段，参5：是否显示 拟合线
    sns.lmplot(data=iris_data_df, x="sepal length (cm)", y= "sepal width (cm)", 
               hue="target", fit_reg=True)
    # 设置标题，显示
    plt.title("iris_data")
    plt.tight_layout()      # 自动调整子图参数，以使整个图像的边界与子图匹配
    plt.show()

# 3.定义函数，对数据集进行划分
def split_data(datas) :
    # 数据集预处理：从150各特征和标签中，按照8：2的比例，切分训练集和测试集
    # 参1：特征数据，参2：标签数据，参3：测试集比例
    # 返回值：训练集的特征数据，测试集的特征数据，训练集的标签数据，测试集的标签数据
    x_train, x_test, y_train, y_test = train_test_split(
        datas.data, datas.target, test_size=0.2, random_state=42
    )

    # print(x_train)
    # print(y_train)
    # print(x_test)
    # print(y_test)

# 定义函数，实现鸢尾花完整案例 -》 加载数据， 特征工程，模型训练，模型评估，模型预测。
def iris_model_evaluate() :
    # 1.加载数据集
    iris_datas = get_data_iris()
    #iris_datas.target = [str(iris_datas.target_names[i]) for i in iris_datas.target]

    # 2.数据切分
    x_train, x_test, y_train, y_test = train_test_split(
        iris_datas.data, iris_datas.target, test_size=0.2, random_state=42
    )

    # 3.特征工程(提取、预处理、选择、降维、组合)
    # 思考1：特征提取，因为源数据只有4各特征列，且都是我们用的，所以这里无需特征提取
    # 思考2：预处理：（归一化 or 标准化）因为源数据的4个特征列差值不大，所以无需预处理。
        # 但是，加入预处理会让代码更完善。
    # 3.1创建标准化对象
    scaler = StandardScaler()

    # 3.2对特征列做标准化，即：x_train: 训练集特征数据， x_test：测试集特征数据
        # fit：训练，在训练集上学习统计量（最小值、最大值、均值、标准差、中位数、四分位距、分位数等）；
        # transform：转换，用学到的统计量变换数据；
        # fit_transform：仅用于训练集；测试集和推理数据只能 transform。
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)

    # 4.模型训练
    # 使用KNN分类算法
    model = KNeighborsClassifier(n_neighbors=3)
    # 训练模型
    model.fit(x_train, y_train)

    # 5.模型预测
    # 场景一：对切分数据集做测试
    y_pre = model.predict(x_test)
    print(f"预测结果为：{y_pre}")
    print(f"原始结果：  {y_test}")

    # # 场景二：对新数据集做测试
    # # 5.1自定义测试数据集
    # my_data = [[7.8, 2.1, 3.9, 1.6]]
    # # 5.2 标准化
    # my_data = scaler.transform(my_data)
    # # 5.3 模型预测
    # my_pre = model.predict(my_data)
    # print(f"新数据预测值：{my_pre}")

    # # 5.4 查看上述数据集，每种分类的预测概率。
    # x_test_proba = model.predict_proba(x_test)
    # my_pre_proba = model.predict_proba(my_data)
    # print(f"test 预测g概率: {x_test_proba}")
    # print(f"自定义预测概率：{my_pre_proba}")

    # 6.模型评估
    # 方式一：直接评分，基于 训练集的特征 和 训练集的标签
    print(f"正确率(准确率): {model.score(x_train, y_train)}")
    print(f"正确率(准确率): {model.score(x_test, y_test)}")
    # 方式二：基于 测试集的标签 和 预测结果 进行评分
    print(f"正确率(准确率): {accuracy_score(y_test, y_pred=y_pre)}")


# 测试
if __name__ == '__main__' :
    iris_model_evaluate()
