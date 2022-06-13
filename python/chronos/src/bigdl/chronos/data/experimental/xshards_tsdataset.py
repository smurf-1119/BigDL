#
# Copyright 2016 The BigDL Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from bigdl.orca.data.shard import SparkXShards
from bigdl.orca.learn.utils import dataframe_to_xshards_of_pandas_df
from bigdl.chronos.data.utils.utils import _to_list, _check_type
from bigdl.chronos.data.utils.roll import roll_timeseries_dataframe
from bigdl.chronos.data.utils.impute import impute_timeseries_dataframe
from bigdl.chronos.data.utils.split import split_timeseries_dataframe
from bigdl.chronos.data.experimental.utils import add_row, transform_to_dict


_DEFAULT_ID_COL_NAME = "id"
_DEFAULT_ID_PLACEHOLDER = "0"


class XShardsTSDataset:

    def __init__(self, shards, **schema):
        '''
        XShardTSDataset is an abstract of time series dataset with distributed fashion.
        Cascade call is supported for most of the transform methods.
        XShardTSDataset will partition the dataset by id_col, which is experimental.
        '''
        self.shards = shards
        self.id_col = schema["id_col"]
        self.dt_col = schema["dt_col"]
        self.feature_col = schema["feature_col"].copy()
        self.target_col = schema["target_col"].copy()

        self.numpy_shards = None

        self._id_list = list(shards[self.id_col].unique())

    @staticmethod
    def from_xshards(shards,
                     dt_col,
                     target_col,
                     id_col=None,
                     extra_feature_col=None,
                     with_split=False,
                     val_ratio=0,
                     test_ratio=0.1,
                     largest_look_back=0,
                     largest_horizon=1):
        '''
        Initialize xshardtsdataset(s) from xshard pandas dataframe.

        :param shards: an xshards pandas dataframe for your raw time series data.
        :param dt_col: a str indicates the col name of datetime
               column in the input data frame.
        :param target_col: a str or list indicates the col name of target column
               in the input data frame.
        :param id_col: (optional) a str indicates the col name of dataframe id. If
               it is not explicitly stated, then the data is interpreted as only
               containing a single id.
        :param extra_feature_col: (optional) a str or list indicates the col name
               of extra feature columns that needs to predict the target column.
        :param with_split: (optional) bool, states if we need to split the dataframe
               to train, validation and test set. The value defaults to False.
        :param val_ratio: (optional) float, validation ratio. Only effective when
               with_split is set to True. The value defaults to 0.
        :param test_ratio: (optional) float, test ratio. Only effective when with_split
               is set to True. The value defaults to 0.1.
        :param largest_look_back: (optional) int, the largest length to look back.
               Only effective when with_split is set to True. The value defaults to 0.
        :param largest_horizon: (optional) int, the largest num of steps to look
               forward. Only effective when with_split is set to True. The value defaults
               to 1.

        :return: a XShardTSDataset instance when with_split is set to False,
                 three XShardTSDataset instances when with_split is set to True.

        Create a xshardtsdataset instance by:

        >>> # Here is a df example:
        >>> # id        datetime      value   "extra feature 1"   "extra feature 2"
        >>> # 00        2019-01-01    1.9     1                   2
        >>> # 01        2019-01-01    2.3     0                   9
        >>> # 00        2019-01-02    2.4     3                   4
        >>> # 01        2019-01-02    2.6     0                   2
        >>> from bigdl.orca.data.pandas import read_csv
        >>> shards = read_csv(csv_path)
        >>> tsdataset = XShardsTSDataset.from_xshards(shards, dt_col="datetime",
        >>>                                           target_col="value", id_col="id",
        >>>                                           extra_feature_col=["extra feature 1",
        >>>                                                              "extra feature 2"])
        '''

        _check_type(shards, "shards", SparkXShards)

        target_col = _to_list(target_col, name="target_col")
        feature_col = _to_list(extra_feature_col, name="extra_feature_col")

        if id_col is None:
            shards = shards.transform_shard(add_row,
                                            _DEFAULT_ID_COL_NAME,
                                            _DEFAULT_ID_PLACEHOLDER)
            id_col = _DEFAULT_ID_COL_NAME

        # repartition to id
        shards = shards.partition_by(cols=id_col,
                                     num_partitions=len(shards[id_col].unique()))

        if with_split:
            tsdataset_shards\
                = shards.transform_shard(split_timeseries_dataframe,
                                         id_col, val_ratio, test_ratio,
                                         largest_look_back, largest_horizon).split()
            return [XShardsTSDataset(shards=tsdataset_shards[i],
                                     id_col=id_col,
                                     dt_col=dt_col,
                                     target_col=target_col,
                                     feature_col=feature_col) for i in range(3)]

        return XShardsTSDataset(shards=shards,
                                id_col=id_col,
                                dt_col=dt_col,
                                target_col=target_col,
                                feature_col=feature_col)

    @staticmethod
    def from_sparkdf(df,
                     dt_col,
                     target_col,
                     id_col=None,
                     extra_feature_col=None,
                     with_split=False,
                     val_ratio=0,
                     test_ratio=0.1,
                     largest_look_back=0,
                     largest_horizon=1):
        '''
        Initialize xshardtsdataset(s) from Spark Dataframe.

        :param df: an Spark DataFrame for your raw time series data.
        :param dt_col: a str indicates the col name of datetime
               column in the input data frame.
        :param target_col: a str or list indicates the col name of target column
               in the input data frame.
        :param id_col: (optional) a str indicates the col name of dataframe id. If
               it is not explicitly stated, then the data is interpreted as only
               containing a single id.
        :param extra_feature_col: (optional) a str or list indicates the col name
               of extra feature columns that needs to predict the target column.
        :param with_split: (optional) bool, states if we need to split the dataframe
               to train, validation and test set. The value defaults to False.
        :param val_ratio: (optional) float, validation ratio. Only effective when
               with_split is set to True. The value defaults to 0.
        :param test_ratio: (optional) float, test ratio. Only effective when with_split
               is set to True. The value defaults to 0.1.
        :param largest_look_back: (optional) int, the largest length to look back.
               Only effective when with_split is set to True. The value defaults to 0.
        :param largest_horizon: (optional) int, the largest num of steps to look
               forward. Only effective when with_split is set to True. The value defaults
               to 1.

        :return: a XShardTSDataset instance when with_split is set to False,
                 three XShardTSDataset instances when with_split is set to True.

        Create a xshardtsdataset instance by:

        >>> # Here is a df example:
        >>> # id        datetime      value   "extra feature 1"   "extra feature 2"
        >>> # 00        2019-01-01    1.9     1                   2
        >>> # 01        2019-01-01    2.3     0                   9
        >>> # 00        2019-01-02    2.4     3                   4
        >>> # 01        2019-01-02    2.6     0                   2
        >>> df = <pyspark.sql.dataframe.DataFrame>
        >>> tsdataset = XShardsTSDataset.from_xshards(df, dt_col="datetime",
        >>>                                           target_col="value", id_col="id",
        >>>                                           extra_feature_col=["extra feature 1",
        >>>                                                              "extra feature 2"])
        '''

        from pyspark.sql.dataframe import DataFrame
        _check_type(df, "df", DataFrame)

        target_col = _to_list(target_col, name="target_col")
        feature_col = _to_list(extra_feature_col, name="extra_feature_col")
        all_col = target_col + feature_col + _to_list(id_col, name="id_col") + [dt_col]

        shards = dataframe_to_xshards_of_pandas_df(df,
                                                   feature_cols=all_col,
                                                   label_cols=None,
                                                   accept_str_col=False)

        if id_col is None:
            shards = shards.transform_shard(add_row,
                                            _DEFAULT_ID_COL_NAME,
                                            _DEFAULT_ID_PLACEHOLDER)
            id_col = _DEFAULT_ID_COL_NAME

        # repartition to id
        shards = shards.partition_by(cols=id_col,
                                     num_partitions=len(shards[id_col].unique()))

        if with_split:
            tsdataset_shards\
                = shards.transform_shard(split_timeseries_dataframe,
                                         id_col, val_ratio, test_ratio,
                                         largest_look_back, largest_horizon).split()
            return [XShardsTSDataset(shards=tsdataset_shards[i],
                                     id_col=id_col,
                                     dt_col=dt_col,
                                     target_col=target_col,
                                     feature_col=feature_col) for i in range(3)]

        return XShardsTSDataset(shards=shards,
                                id_col=id_col,
                                dt_col=dt_col,
                                target_col=target_col,
                                feature_col=feature_col)

    def roll(self,
             lookback,
             horizon,
             feature_col=None,
             target_col=None,
             id_sensitive=False):
        '''
        Sampling by rolling for machine learning/deep learning models.

        :param lookback: int, lookback value.
        :param horizon: int or list,
               if `horizon` is an int, we will sample `horizon` step
               continuously after the forecasting point.
               if `horizon` is a list, we will sample discretely according
               to the input list.
               specially, when `horizon` is set to 0, ground truth will be generated as None.
        :param feature_col: str or list, indicates the feature col name. Default to None,
               where we will take all available feature in rolling.
        :param target_col: str or list, indicates the target col name. Default to None,
               where we will take all target in rolling. it should be a subset of target_col
               you used to initialize the xshardtsdataset.
        :param id_sensitive: bool,
               |if `id_sensitive` is False, we will rolling on each id's sub dataframe
               |and fuse the sampings.
               |The shape of rolling will be
               |x: (num_sample, lookback, num_feature_col + num_target_col)
               |y: (num_sample, horizon, num_target_col)
               |where num_sample is the summation of sample number of each dataframe
               |if `id_sensitive` is True, we have not implement this currently.

        :return: the xshardtsdataset instance.
        '''
        from bigdl.nano.utils.log4Error import invalidInputError
        if id_sensitive:
            invalidInputError(False,
                              "id_sensitive option has not been implemented.")
        feature_col = _to_list(feature_col, "feature_col") if feature_col is not None \
            else self.feature_col
        target_col = _to_list(target_col, "target_col") if target_col is not None \
            else self.target_col
        self.numpy_shards = self.shards.transform_shard(roll_timeseries_dataframe,
                                                        None, lookback, horizon,
                                                        feature_col, target_col)
        return self

    def impute(self,
               mode="last",
               const_num=0):
        '''
        Impute the tsdataset by imputing each univariate time series
        distinguished by id_col and feature_col.

        :param mode: imputation mode, select from "last", "const" or "linear".

            "last": impute by propagating the last non N/A number to its following N/A.
            if there is no non N/A number ahead, 0 is filled instead.

            "const": impute by a const value input by user.

            "linear": impute by linear interpolation.
        :param const_num:  indicates the const number to fill, which is only effective when mode
            is set to "const".

        :return: the tsdataset instance.
        '''
        def df_reset_index(df):
                df.reset_index(drop=True, inplace=True)
                return df
        self.shards = self.shards.transform_shard(impute_timeseries_dataframe,
                                                  self.dt_col, mode,
                                                  const_num)
        self.shards.transform_shard(df_reset_index)
        return self

    def scale(self,
              scaler,
              fit = True):
        '''
        Scale the time series dataset's feature column and target column.

        :param scaler: sklearn scaler instance, StandardScaler, MaxAbsScaler,
               MinMaxScaler and RobustScaler are supported.
        :param fit: if we need to fit the scaler. Typically, the value should
               be set to True for training set, while False for validation and
               test set. The value is defaulted to True.

        :return: the tsdataset instance.

        Assume there is a training set tsdata and a test set tsdata_test.
        scale() should be called first on training set with default value fit=True,
        then be called on test set with the same scaler and fit=False.

        >>> from sklearn.preprocessing import StandardScaler
        >>> scaler = StandardScaler()
        >>> tsdata.scale(scaler, fit=True)
        >>> tsdata_test.scale(scaler, fit=False)
        '''
        tmp_shards = self.shards.transform_shard(scale_timeseries_dataframe,
                                                        scaler, fit)
        
        return self

    def to_xshards(self):
        '''
        Export rolling result in form of a dict of numpy ndarray {'x': ..., 'y': ...}

        :return: a 2-element dict xshard. each value is a 3d numpy ndarray. The ndarray
                 is casted to float32.
        '''
        from bigdl.nano.utils.log4Error import invalidInputError
        if self.numpy_shards is None:
            invalidInputError(False,
                              "Please call 'roll' method "
                              "before transform a XshardsTSDataset to numpy ndarray!")
        return self.numpy_shards.transform_shard(transform_to_dict)

def scale_timeseries_dataframe(df, scaler, fit=True):
        '''
        Scale the time series dataset's feature column and target column.

        :param scaler: sklearn scaler instance, StandardScaler, MaxAbsScaler,
               MinMaxScaler and RobustScaler are supported.
        :param fit: if we need to fit the scaler. Typically, the value should
               be set to True for training set, while False for validation and
               test set. The value is defaulted to True.

        :return: the tsdataset instance.

        Assume there is a training set tsdata and a test set tsdata_test.
        scale() should be called first on training set with default value fit=True,
        then be called on test set with the same scaler and fit=False.

        >>> from sklearn.preprocessing import StandardScaler
        >>> scaler = StandardScaler()
        >>> tsdata.scale(scaler, fit=True)
        >>> tsdata_test.scale(scaler, fit=False)
        '''
       #  if self.roll_additional_feature:
       #      feature_col = []
       #      for feature in self.feature_col:
       #          if feature not in self.roll_additional_feature:
       #              feature_col.append(feature)
        import sklearn
        scaler = sklearn.preprocessing.StandardScaler()
        
        
        if fit:
            df[:] = scaler.fit_transform(df[:])
        else:
            from sklearn.utils.validation import check_is_fitted
            from bigdl.nano.utils.log4Error import invalidInputError
            try:
                invalidInputError(not check_is_fitted(scaler), "scaler is not fittedd")
            except Exception:
                invalidInputError(False,
                                  "When calling scale for the first time, "
                                  "you need to set fit=True.")
            df[:] = scaler.transform(df[:])

        return {df["id_col"][0]:{"scaler": scaler, "df": df}}