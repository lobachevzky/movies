# Copyright 2015 Google Inc. All Rights Reserved.
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
# ==============================================================================

"""Fundamental operations of the autoencoder

Implements the inference/loss/training pattern for model building.

1. inference() - Builds the model as far as is required for running the network
forward to make predictions.
2. loss() - Adds to the inference model the layers required to generate loss.
3. training() - Adds to the loss model the Ops required to generate and
apply gradients.

This file is used by the various "fully_connected_*.py" files and not meant to
be run.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import math

import tensorflow as tf
import numpy as np


def inference(inputs,
              embedding_dim,
              hidden1_units,
              hidden2_units,
              keep_prob=.8):
    """Build the MNIST model up to where it may be used for inference.

  Args:
    inputs: inputs placeholder, from inputs().
    hidden1_units: Size of the first hidden layer.
    hidden2_units: Size of the second hidden layer.

  Returns:
    softmax_linear: Output tensor with the computed logits.
    :param embedding_size:
  """
    # Embeddings
    # embeddings = tf.Variable(
    #     tf.random_uniform([embedding_size, embedding_dim], -1.0, 1.0))

    # hash into embeddings
    # embedding_lookup = tf.nn.embedding_lookup(embeddings, entities)

    # multiply each embedding vector elemwise with ratings
    # scale_by_value = tf.transpose(tf.mul(tf.transpose(embedding_lookup),
    #                                      tf.transpose(ratings)))
    # sum all vectors in each instance
    # vector_sums = tf.reduce_sum(scale_by_value, 1)

    # Hidden 1
    with tf.name_scope('hidden1'):
        shape = [embedding_dim, hidden1_units]
        weights = tf.Variable(
            tf.truncated_normal(shape,
                                stddev=1.0 / math.sqrt(embedding_dim)),
            name='weights')
        biases = tf.Variable(tf.zeros([hidden1_units]),
                             name='biases')
        hidden1 = tf.nn.relu(tf.matmul(inputs, weights) + biases)
    # Hidden 2
    with tf.name_scope('hidden2'):
        weights = tf.Variable(
            tf.truncated_normal([hidden1_units, hidden2_units],
                                stddev=1.0 / math.sqrt(float(hidden1_units))),
            name='weights')
        biases = tf.Variable(tf.zeros([hidden2_units]),
                             name='biases')
        hidden2 = tf.nn.relu(tf.matmul(hidden1, weights) + biases)
        hidden2_dropout = tf.nn.dropout(hidden2, tf.constant(keep_prob, dtype='float32'))
    # Linear
    with tf.name_scope('softmax_linear'):
        weights = tf.Variable(
            tf.truncated_normal([hidden2_units, embedding_dim],
                                stddev=1.0 / math.sqrt(float(hidden2_units))),
            name='weights')
        biases = tf.Variable(tf.zeros([embedding_dim]), name='biases')
        logits = tf.matmul(hidden2_dropout, weights) + biases
    return logits


def loss(logits, labels, mask):
    """Calculates the loss from the logits and the labels.

  Args:
    logits: Logits tensor, float - [batch_size, NUM_CLASSES].
    labels: Labels tensor, int32 - [batch_size, NUM_CLASSES].

  Returns:
    loss: Loss tensor of type float.
    :param mask:
  """
    diff = tf.boolean_mask(logits - labels, mask)
    return tf.nn.l2_loss(diff)


def training(loss, learning_rate):
    """Sets up the training Ops.

  Creates a summarizer to track the loss over time in TensorBoard.

  Creates an optimizer and applies the gradients to all trainable variables.

  The Op returned by this function is what must be passed to the
  `sess.run()` call to cause the model to train.

  Args:
    loss: Loss tensor, from loss().
    learning_rate: The learning rate to use for gradient descent.

  Returns:
    train_op: The Op for training.
  """
    # Add a scalar summary for the snapshot loss.
    tf.scalar_summary(loss.op.name, loss)
    # Create the gradient descent optimizer with the given learning rate.
    optimizer = tf.train.GradientDescentOptimizer(learning_rate)
    # Create a variable to track the global step.
    global_step = tf.Variable(0, name='global_step', trainable=False)
    # Use the optimizer to apply the gradients that minimize the loss
    # (and also increment the global step counter) as a single training step.
    train_op = optimizer.minimize(loss, global_step=global_step)
    return train_op


def almost_equal(a, b):
    """
    :param a: tensor :param b: tensor
    :returns equivalent to numpy: a == b, if a and b were ndarrays
    """
    not_almost_equal = tf.abs(tf.sign(tf.round(a - b)))
    return tf.abs(not_almost_equal - 1)


def evaluation(logits, labels, mask):
    """Evaluate the quality of the logits at predicting the label.

  Args:
    logits: Logits tensor, float - [batch_size, NUM_CLASSES].
    labels: Labels tensor, int32 - [batch_size], with values in the
      range [0, NUM_CLASSES).

  Returns:
    A scalar int32 tensor with the number of examples (out of batch_size)
    that were predicted correctly.
  """
    # For a classifier model, we can use the in_top_k Op.
    # It returns a bool tensor with shape [batch_size] that is true for
    # the examples where the label's is was in the top k (here k=1)
    # of all logits for that example.
    total_correct = almost_equal(logits, labels)
    # Return the number of true entries.
    correct_that_count = tf.reduce_sum(tf.boolean_mask(total_correct, mask))
    total_that_count = tf.reduce_sum(tf.to_int32(mask))
    return np.array([correct_that_count, total_that_count])
