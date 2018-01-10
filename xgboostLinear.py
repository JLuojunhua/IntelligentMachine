#!/usr/bin/python
import numpy as np
import xgboost as xgb
import pandas as pd
### load data in do training
x_train = pd.read_csv('half_data/x_train.csv')
y_train = pd.read_csv('half_data/y_train.csv')
dtrain = xgb.DMatrix(x_train, label=y_train)
param = {'booster': 'gblinear', 'lambda': 6, 'silent': 0, 'objective': 'reg:linear'}
num_round = 10000

print('running cross validation')
# do cross validation, this will print result out as
# [iteration]  metric_name:mean_value+std_value
# std_value is standard deviation of the metric
# xgb.cv(param, dtrain, num_round, nfold=5,
#        metrics={'rmse'}, seed=0,
#        callbacks=[xgb.callback.print_evaluation(show_stdv=True)])

print('running cross validation, disable standard deviation display')
# do cross validation, this will print result out as
# [iteration]  metric_name:mean_value

res = xgb.cv(param, dtrain, num_boost_round=1000,
             metrics={'rmse'},
             callbacks=[xgb.callback.print_evaluation(show_stdv=False),
                        xgb.callback.early_stop(50)])
print(res)
# print('running cross validation, with preprocessing function')
#
#
# # define the preprocessing function
# # used to return the preprocessed training, test data, and parameter
# # we can use this to do weight rescale, etc.
# # as a example, we try to set scale_pos_weight
# def fpreproc(dtrain, dtest, param):
#     label = dtrain.get_label()
#     ratio = float(np.sum(label == 0)) / np.sum(label == 1)
#     param['scale_pos_weight'] = ratio
#     return (dtrain, dtest, param)
#
#
# # do cross validation, for each fold
# # the dtrain, dtest, param will be passed into fpreproc
# # then the return value of fpreproc will be used to generate
# # results of that fold
# xgb.cv(param, dtrain, num_round, nfold=5,
#        metrics={'auc'}, seed=0, fpreproc=fpreproc)
#
# ###
# # you can also do cross validation with cutomized loss function
# # See custom_objective.py
# ##
# print('running cross validation, with cutomsized loss function')
#
#
# def logregobj(preds, dtrain):
#     labels = dtrain.get_label()
#     preds = 1.0 / (1.0 + np.exp(-preds))
#     grad = preds - labels
#     hess = preds * (1.0 - preds)
#     return grad, hess
#
#
# def evalerror(preds, dtrain):
#     labels = dtrain.get_label()
#     return 'error', float(sum(labels != (preds > 0.0))) / len(labels)
#
#
# param = {'max_depth': 2, 'eta': 1, 'silent': 1}
# # train with customized objective
# xgb.cv(param, dtrain, num_round, nfold=5, seed=0,
#        obj=logregobj, feval=evalerror)
