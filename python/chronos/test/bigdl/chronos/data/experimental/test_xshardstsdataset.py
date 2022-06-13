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

import pytest
import numpy as np
import pandas as pd
import random
import os

from unittest import TestCase
from bigdl.chronos.data import TSDataset
from bigdl.chronos.data.experimental import XShardsTSDataset
from bigdl.orca.data.pandas import read_csv
from bigdl.orca.common import init_orca_context, stop_orca_context, OrcaContext

from pandas.testing import assert_frame_equal
from numpy.testing import assert_array_almost_equal


def generate_spark_df():
    init_orca_context(cores=8)
    sc = OrcaContext.get_spark_context()
    rdd = sc.range(0, 100)
    from pyspark.ml.linalg import DenseVector
    df = rdd.map(lambda x: (DenseVector(np.random.randn(1, ).astype(np.float)),
                            int(np.random.randint(0, 2, size=())),
                            int(x))).toDF(["feature", "id", "date"])
    return df

class TestXShardsTSDataset(TestCase):

    def setUp(self):
        self.resource_path = os.path.join(os.path.split(__file__)[0], "../../resources/")

    def tearDown(self):
        pass
    
    @classmethod
    def tearDownClass(cls):
        # stop possible active_spark_context
        from pyspark import SparkContext
        from bigdl.orca.ray import OrcaRayContext
        if SparkContext._active_spark_context is not None:
            print("Stopping spark_orca context")
            sc = SparkContext.getOrCreate()
            if sc.getConf().get("spark.master").startswith("spark://"):
                from bigdl.dllib.nncontext import stop_spark_standalone
                stop_spark_standalone()
            sc.stop()

    def test_xshardstsdataset_initialization(self):
        shards_single = read_csv(os.path.join(self.resource_path, "single.csv"))
        tsdata = XShardsTSDataset.from_xshards(shards_single, dt_col="datetime", target_col="value",
                                               extra_feature_col=["extra feature"], id_col="id")
        assert tsdata._id_list == [0]
        assert tsdata.feature_col == ["extra feature"]
        assert tsdata.target_col == ["value"]
        assert tsdata.dt_col == "datetime"
        assert tsdata.shards.num_partitions() == 1

        tsdata = XShardsTSDataset.from_xshards(shards_single, dt_col="datetime",
                                               target_col=["value"],
                                               extra_feature_col="extra feature", id_col="id")
        assert tsdata._id_list == [0]
        assert tsdata.feature_col == ["extra feature"]
        assert tsdata.target_col == ["value"]
        assert tsdata.dt_col == "datetime"
        assert tsdata.shards.num_partitions() == 1

        tsdata = XShardsTSDataset.from_xshards(shards_single, dt_col="datetime",
                                               target_col=["value"],
                                               extra_feature_col="extra feature")
        assert tsdata._id_list == ["0"]
        assert tsdata.feature_col == ["extra feature"]
        assert tsdata.target_col == ["value"]
        assert tsdata.dt_col == "datetime"
        assert tsdata.shards.num_partitions() == 1

    def test_xshardstsdataset_initialization_multiple(self):
        shards_multiple = read_csv(os.path.join(self.resource_path, "multiple.csv"))
        # legal input
        tsdata = XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime",
                                               target_col="value",
                                               extra_feature_col=["extra feature"], id_col="id")
        assert tsdata._id_list == [0, 1]
        assert tsdata.feature_col == ["extra feature"]
        assert tsdata.target_col == ["value"]
        assert tsdata.dt_col == "datetime"
        assert tsdata.shards.num_partitions() == 2

        tsdata = XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime",
                                               target_col=["value"],
                                               extra_feature_col="extra feature", id_col="id")
        assert tsdata._id_list == [0, 1]
        assert tsdata.feature_col == ["extra feature"]
        assert tsdata.target_col == ["value"]
        assert tsdata.dt_col == "datetime"
        assert tsdata.shards.num_partitions() == 2

        tsdata = XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime",
                                               target_col=["value"],
                                               extra_feature_col="extra feature")
        assert tsdata._id_list == ['0']
        assert tsdata.feature_col == ["extra feature"]
        assert tsdata.target_col == ["value"]
        assert tsdata.dt_col == "datetime"
        assert tsdata.shards.num_partitions() == 1

    def test_xshardstsdataset_split(self):
        shards_multiple = read_csv(os.path.join(self.resource_path, "multiple.csv"))
        # only train and test
        tsdata_train, tsdata_valid, tsdata_test =\
            XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime", target_col="value",
                                          extra_feature_col=["extra feature"], id_col="id",
                                          with_split=True, val_ratio=0, test_ratio=0.1)
        # standard split with all three sets
        tsdata_train, tsdata_valid, tsdata_test =\
            XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime", target_col="value",
                                          extra_feature_col=["extra feature"], id_col="id",
                                          with_split=True, val_ratio=0.1, test_ratio=0.1,
                                          largest_look_back=5, largest_horizon=2)

        tsdata_train.feature_col.append("new extra feature")
        assert len(tsdata_train.feature_col) == 2
        assert len(tsdata_valid.feature_col) == 1
        assert len(tsdata_test.feature_col) == 1

        tsdata_train.target_col[0] = "new value"
        assert tsdata_train.target_col[0] == "new value"
        assert tsdata_valid.target_col[0] != "new value"
        assert tsdata_test.target_col[0] != "new value"

    def test_xshardstsdataset_roll_multiple_id(self):
        shards_multiple = read_csv(os.path.join(self.resource_path, "multiple.csv"))
        horizon = random.randint(1, 10)
        lookback = random.randint(1, 20)

        tsdata = XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime",
                                               target_col="value",
                                               extra_feature_col=["extra feature"], id_col="id")

        with pytest.raises(RuntimeError):
            tsdata.to_xshards()

        # roll train
        tsdata.roll(lookback=lookback, horizon=horizon)
        shards_numpy = tsdata.to_xshards()
        collected_numpy = shards_numpy.collect()  # collect and valid
        x = np.concatenate([collected_numpy[i]['x'] for i in range(len(collected_numpy))], axis=0)
        y = np.concatenate([collected_numpy[i]['y'] for i in range(len(collected_numpy))], axis=0)
        assert x.shape == ((50-lookback-horizon+1)*2, lookback, 2)
        assert y.shape == ((50-lookback-horizon+1)*2, horizon, 1)

        tsdata.roll(lookback=lookback, horizon=horizon,
                    feature_col=["extra feature"], target_col="value")
        shards_numpy = tsdata.to_xshards()
        collected_numpy = shards_numpy.collect()  # collect and valid
        x = np.concatenate([collected_numpy[i]['x'] for i in range(len(collected_numpy))], axis=0)
        y = np.concatenate([collected_numpy[i]['y'] for i in range(len(collected_numpy))], axis=0)
        assert x.shape == ((50-lookback-horizon+1)*2, lookback, 2)
        assert y.shape == ((50-lookback-horizon+1)*2, horizon, 1)

        tsdata.roll(lookback=lookback, horizon=horizon,
                    feature_col=[], target_col="value")
        shards_numpy = tsdata.to_xshards()
        collected_numpy = shards_numpy.collect()  # collect and valid
        x = np.concatenate([collected_numpy[i]['x'] for i in range(len(collected_numpy))], axis=0)
        y = np.concatenate([collected_numpy[i]['y'] for i in range(len(collected_numpy))], axis=0)
        assert x.shape == ((50-lookback-horizon+1)*2, lookback, 1)
        assert y.shape == ((50-lookback-horizon+1)*2, horizon, 1)

        # roll test
        horizon = 0
        lookback = random.randint(1, 20)

        tsdata.roll(lookback=lookback, horizon=horizon)
        shards_numpy = tsdata.to_xshards()
        collected_numpy = shards_numpy.collect()  # collect and valid
        x = np.concatenate([collected_numpy[i]['x'] for i in range(len(collected_numpy))], axis=0)
        assert x.shape == ((50-lookback-horizon+1)*2, lookback, 2)

    def test_xshardstsdataset_impute(self):
        for val in ["last", "const", "linear"]:
            shards_tmp = read_csv(os.path.join(self.resource_path, "impute_test.csv"))
            tsdata = XShardsTSDataset.from_xshards(shards_tmp, 
                                                dt_col="datetime", target_col="e",
                                           extra_feature_col=["a", "b", "c", "d"], id_col="id")

            tsdata.impute(mode=val)
            collected_df = tsdata.shards.collect()
            collected_df = pd.concat(collected_df, axis=0)
            
            assert collected_df.isna().sum().sum() == 0
            assert len(collected_df) == 100



    def test_xshardstsdataset_sparkdf(self):
        df = generate_spark_df()

        # with id
        tsdata = XShardsTSDataset.from_sparkdf(df, dt_col="date",
                                               target_col="feature",
                                               id_col="id")
        tsdata.roll(lookback=4, horizon=2)
        data = tsdata.to_xshards().collect()
        assert data[0]['x'].shape[1] == 4
        assert data[0]['x'].shape[2] == 1
        assert data[0]['y'].shape[1] == 2
        assert data[0]['y'].shape[2] == 1
        assert tsdata.shards.num_partitions() == 2

        # with only 1 id
        tsdata = XShardsTSDataset.from_sparkdf(df, dt_col="date",
                                               target_col="feature")
        tsdata.roll(lookback=4, horizon=2)
        data = tsdata.to_xshards().collect()
        assert data[0]['x'].shape[1] == 4
        assert data[0]['x'].shape[2] == 1
        assert data[0]['y'].shape[1] == 2
        assert data[0]['y'].shape[2] == 1
        assert tsdata.shards.num_partitions() == 1

    def test_xshardstsdataset_scale(self):
        from sklearn.preprocessing import StandardScaler
        shards_multiple = read_csv(os.path.join(self.resource_path, "multiple.csv"))

        tsdata = XShardsTSDataset.from_xshards(shards_multiple, dt_col="datetime",
                                               target_col="value",
                                               extra_feature_col=["extra feature"], id_col="id")


        scaler = StandardScaler()
        tsdata.scale(scaler)
