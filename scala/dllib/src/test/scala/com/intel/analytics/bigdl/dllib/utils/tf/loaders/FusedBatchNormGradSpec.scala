/*
 * Copyright 2016 The BigDL Authors.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.intel.analytics.bigdl.dllib.utils.tf.loaders

import com.intel.analytics.bigdl.dllib.tensor.Tensor
import com.intel.analytics.bigdl.dllib.utils.RandomGenerator
import com.intel.analytics.bigdl.dllib.utils.tf.Tensorflow.{booleanAttr, floatAttr, typeAttr}
import com.intel.analytics.bigdl.dllib.utils.tf.{TensorflowDataFormat, TensorflowSpecHelper}
import org.tensorflow.framework.{DataType, NodeDef}

class FusedBatchNormGradSpec extends TensorflowSpecHelper {

  "FusedBatchNormGrad gradInput" should "be correct when is training is true" in {
    RandomGenerator.RNG.setSeed(2000)
    val x = Tensor[Float](4, 8, 8, 256).rand()
    val g = Tensor[Float](4, 8, 8, 256).rand()
    val scale = Tensor[Float](256).rand()
    val mean = Tensor[Float](256).rand()
    val variance = Tensor[Float](256).rand()

    compare[Float](
      NodeDef.newBuilder()
        .setName("fusedbn_grad_test")
        .putAttr("T", typeAttr(DataType.DT_FLOAT))
        .putAttr("epsilon", floatAttr(0.0001f))
        .putAttr("data_format", TensorflowDataFormat.NHWC.value)
        .putAttr("is_training", booleanAttr(true))
        .setOp("FusedBatchNormGrad"),
      Seq(g, x, scale, mean, variance),
      0, 1e-3
    )
  }

  "FusedBatchNormGrad weight" should "be correct when is training is true" in {
    val x = Tensor[Float](4, 8, 8, 256).rand()
    val g = Tensor[Float](4, 8, 8, 256).rand()
    val scale = Tensor[Float](256).rand()
    val mean = Tensor[Float](256).rand()
    val variance = Tensor[Float](256).rand()

    compare[Float](
      NodeDef.newBuilder()
        .setName("fusedbn_grad_test")
        .putAttr("T", typeAttr(DataType.DT_FLOAT))
        .putAttr("epsilon", floatAttr(0.0001f))
        .putAttr("data_format", TensorflowDataFormat.NHWC.value)
        .putAttr("is_training", booleanAttr(true))
        .setOp("FusedBatchNormGrad"),
      Seq(g, x, scale, mean, variance),
      1, 1e-3
    )
  }

  "FusedBatchNormGrad bias" should "be correct when is training is true" in {
    val x = Tensor[Float](4, 8, 8, 256).rand()
    val g = Tensor[Float](4, 8, 8, 256).rand()
    val scale = Tensor[Float](256).rand()
    val mean = Tensor[Float](256).rand()
    val variance = Tensor[Float](256).rand()

    compare[Float](
      NodeDef.newBuilder()
        .setName("fusedbn_grad_test")
        .putAttr("T", typeAttr(DataType.DT_FLOAT))
        .putAttr("epsilon", floatAttr(0.0001f))
        .putAttr("data_format", TensorflowDataFormat.NHWC.value)
        .putAttr("is_training", booleanAttr(true))
        .setOp("FusedBatchNormGrad"),
      Seq(g, x, scale, mean, variance),
      2
    )
  }

  "FusedBatchNormGrad gradInput" should "be correct when is training is false" in {
    RandomGenerator.RNG.setSeed(2000)
    val x = Tensor[Float](4, 8, 8, 256).rand()
    val g = Tensor[Float](4, 8, 8, 256).rand()
    val scale = Tensor[Float](256).rand()
    val mean = Tensor[Float](256).rand()
    val variance = Tensor[Float](256).rand()

    compare[Float](
      NodeDef.newBuilder()
        .setName("fusedbn_grad_test")
        .putAttr("T", typeAttr(DataType.DT_FLOAT))
        .putAttr("epsilon", floatAttr(0.0001f))
        .putAttr("data_format", TensorflowDataFormat.NHWC.value)
        .putAttr("is_training", booleanAttr(false))
        .setOp("FusedBatchNormGrad"),
      Seq(g, x, scale, mean, variance),
      0, 1e-3
    )
  }

  "FusedBatchNormGrad weight" should "be correct when is training is false" in {
    val x = Tensor[Float](4, 8, 8, 256).rand()
    val g = Tensor[Float](4, 8, 8, 256).rand()
    val scale = Tensor[Float](256).rand()
    val mean = Tensor[Float](256).rand()
    val variance = Tensor[Float](256).rand()

    compare[Float](
      NodeDef.newBuilder()
        .setName("fusedbn_grad_test")
        .putAttr("T", typeAttr(DataType.DT_FLOAT))
        .putAttr("epsilon", floatAttr(0.0001f))
        .putAttr("data_format", TensorflowDataFormat.NHWC.value)
        .putAttr("is_training", booleanAttr(false))
        .setOp("FusedBatchNormGrad"),
      Seq(g, x, scale, mean, variance),
      1, 1e-3
    )
  }

  "FusedBatchNormGrad bias" should "be correct when is training is false" in {
    val x = Tensor[Float](4, 8, 8, 256).rand()
    val g = Tensor[Float](4, 8, 8, 256).rand()
    val scale = Tensor[Float](256).rand()
    val mean = Tensor[Float](256).rand()
    val variance = Tensor[Float](256).rand()

    compare[Float](
      NodeDef.newBuilder()
        .setName("fusedbn_grad_test")
        .putAttr("T", typeAttr(DataType.DT_FLOAT))
        .putAttr("epsilon", floatAttr(0.0001f))
        .putAttr("data_format", TensorflowDataFormat.NHWC.value)
        .putAttr("is_training", booleanAttr(false))
        .setOp("FusedBatchNormGrad"),
      Seq(g, x, scale, mean, variance),
      2
    )
  }
}

