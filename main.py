# coding=utf-8

import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.linear_model import Lasso
from sklearn import cross_validation
from sklearn.linear_model import SGDRegressor
import matplotlib.pyplot as plt
import xgboost as xgb


def pre_process_data():
    print("begin to read data")
    train_data = pd.read_excel('train.xlsx')
    x_test = pd.read_excel('test_a.xlsx')

    # 去掉空行
    print("raw_data:" + str(train_data.shape))
    nan_data_value = remove_nan_data(train_data)

    train_data.drop(nan_data_value, axis=1, inplace=True)
    print("remove nan data:" + str(train_data.shape))
    float_data = remove_no_float(train_data)
    # train_data = remove_date(train_data)
    train_data = train_data[float_data]
    print(float_data)
    print(train_data.shape)
    train_data = remove_waste_col(train_data)
    print(train_data.shape)
    y_train = train_data['Y']
    train_data.drop(['Y'], axis=1, inplace=True)
    # x_train = normalize_data(train_data)
    x_train = train_data
    x_train.fillna(x_train.mean(), inplace=True)
    corr_df = cal_corrcoef(x_train, y_train)
    corr02 = corr_df[corr_df.corr_value >= 0.20]
    corr02_col = corr02['col'].values.tolist()
    x_train = x_train[corr02_col]
    x_test = x_test[corr02_col]
    # x_test = normalize_data(x_test)
    x_test.fillna(x_test.mean(), inplace=True)
    print("Finish preprocess")
    print(x_train.shape, y_train.shape)
    return x_train, y_train, x_test


def remove_nan_data(data):
    nan_data = data.isnull().sum(axis=0).reset_index()
    nan_data.columns = ['col', 'nan_count']
    nan_data = nan_data.sort_values(by='nan_count')
    nan_data_value = nan_data[nan_data.nan_count > 200].col.values
    print("nan_data_value:" + str(nan_data_value))
    return nan_data_value


#  删除非数字行
def remove_no_float(data):
    data_type = data.dtypes.reset_index()
    data_type.columns = ['col', 'dtype']
    data_object = data_type[data_type.dtype == 'object'].col.values
    data_object = data[data_object]
    data_object.to_csv('main.csv', index=False)
    return data_type[data_type.dtype == 'float64'].col.values


# 计算协方差
def cal_corrcoef(float_df, y_train):
    corr_values = []
    float_col = list(float_df.columns)
    for col in float_col:
        corr_values.append(abs(np.corrcoef(float_df[col].values, y_train) \
                                   [0, 1]))
    corr_df = pd.DataFrame({'col': float_col, 'corr_value': corr_values})
    corr_df = corr_df.sort_values(by='corr_value', ascending=False)
    return corr_df


# 去掉数字相同的列以及日期列
def remove_waste_col(data):
    columns = list(data.columns)
    same_num_col = []
    for col in columns:
        max_num = data[col].max()
        if max_num != data[col].min() and str(max_num).find('2017') == -1 and str(max_num).find(
                '2016') == -1 and max_num < 1e13:
            same_num_col.append(col)
    return data[same_num_col]


def normalize_data(data):
    return data.apply(lambda x: (x - np.min(x)) / (np.max(x) - np.min(x)))
    # return preprocessing.scale(data, axis=0)
    # return data.apply(lambda x: (x - np.average(x)) / np.std(x))


def create_model(x_train, y_train, alpha):
    print("begin to train...")
    model = Ridge(alpha=alpha)
    model.fit(x_train, y_train)
    return model


def cal_MSE(y_predict, y_real):
    n = len(y_predict)
    print("样本数量:" + str(n))
    return np.sum(np.square(y_predict - y_real)) / n


def find_min_alpha(x_train, y_train):
    alphas = np.logspace(-2, 3, 200)
    # print(alphas)
    test_scores = []
    alpha_score = []
    for alpha in alphas:
        clf = Ridge(alpha)
        test_score = -cross_validation.cross_val_score(clf, x_train, y_train, cv=10, scoring='neg_mean_squared_error')
        test_scores.append(np.mean(test_score))
        alpha_score.append([alpha, np.mean(test_score)])
    print("final test score:")
    print(test_scores)
    print(alpha_score)

    sorted_alpha = sorted(alpha_score, key=lambda x: x[1], reverse=False)
    print(sorted_alpha)
    alpha = sorted_alpha[0][0]
    print("best alpha:" + str(alpha))
    return alpha


def train_with_xgboost(x_train, y_train, x_test, alpha):
    params = {
        'booster': 'gblinear',
        'silent': 0,
        'eta': 0.01,
        'lambda': alpha,
        'objective': 'reg:linear'
    }
    # 划分训练数据集与验证数据集
    offset = 394
    num_rounds = 10000
    # 划分训练集与验证集
    # for offset in offsets:
    x_test = xgb.DMatrix(x_test)
    xgtrain = xgb.DMatrix(x_train[:offset], label=y_train[:offset])
    xgval = xgb.DMatrix(x_train[offset:], label=y_train[offset:])
    # return 训练和验证的错误率
    watchlist = [(xgtrain, 'train'), (xgval, 'val')]
    # begin to train
    print("Begin to train with xgboost")
    model = xgb.train(params, xgtrain, num_rounds, watchlist, early_stopping_rounds=50)
    preds = model.predict(x_test)
    sub_df = pd.read_csv('sub_a.csv', header=None)
    sub_df['Y'] = preds
    sub_df.to_csv('xgboost2.csv', header=None, index=False)


def plot_image(x, y, x_label=None, y_label=None):
    plt.plot(x, y)
    plt.title("cross val score")
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.show()

def train_with_LR_L2(x_train, y_train, x_test, alpha):
    model = create_model(x_train, y_train, alpha)
    print("交叉验证...")
    scores = cross_validation.cross_val_score(model, x_train, y_train, cv=10, scoring='neg_mean_squared_error')
    print(scores)
    print("mean:" + str(scores.mean()))
    ans = model.predict(x_test)
    sub_df = pd.read_csv('sub_a.csv', header=None)
    sub_df['Y'] = ans
    sub_df.to_csv('final.csv', header=None, index=False)
    print("MSE:")
    print(cal_MSE(ans, y_train))


if __name__ == '__main__':
    # 数据预处理，特征工程
    # x_train, y_train, x_test = pre_process_data()
    # # 保存特征工程的结果到文件
    # x_train.to_csv('x_train.csv', header=None, index=False)
    # y_train.to_csv('y_train.csv', header=None, index=False)
    # x_test.to_csv('x_test.csv', header=None, index=False)
    # 从文件中读取经过预处理的数据
    x_train = pd.read_csv('x_train.csv', header=None)
    y_train = pd.read_csv('y_train.csv', header=None)
    x_test = pd.read_csv('x_test.csv', header=None)
    x_train = x_train.values
    y_train = y_train.values
    x_test = x_test.values
    X = np.vstack((x_train, x_test))
    # normalize数据
    X = preprocessing.scale(X)

    x_train = X[0:len(x_train)]
    x_test = X[len(x_train):]
    # 寻找L2正则的最优化alpha
    alpha = find_min_alpha(x_train, y_train)
    # 训练模型
    # train_with_LR_L2(x_train, y_train,x_test, alpha)
    # alpha = 890
    train_with_xgboost(x_train, y_train, x_test, alpha)
