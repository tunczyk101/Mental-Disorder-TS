import lightgbm as lgb
import optuna.integration.lightgbm as opt_lgb
from lightgbm import early_stopping, log_evaluation
from sklearn.model_selection import KFold


def lightgbm_fit_binary(X_train, y_train) -> lgb.Booster:
    """
    Performs tuning and fits LightGBM model for binary classification

    :param X_train: train set with features to use during fitting
    :param y_train: train set with binary target values (0 or 1)
    :return: trained LightGBM model
    """
    lgb_train = opt_lgb.Dataset(X_train, y_train)
    params = {
        "boosting_type": "gbdt",
        "objective": "binary",
        "metric": "binary_logloss",
        "verbosity": -1,
    }

    tuner = opt_lgb.LightGBMTunerCV(
        params,
        lgb_train,
        folds=KFold(n_splits=5),
        num_boost_round=10000,
        callbacks=[early_stopping(100), log_evaluation(100)],
    )

    tuner.run()
    best_params = tuner.best_params

    lgb_tuned = lgb.train(
        best_params,
        lgb_train,
        num_boost_round=10000,
    )

    return lgb_tuned