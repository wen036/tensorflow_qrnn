import unittest
import numpy as np
from sklearn.datasets import load_digits
from sklearn.metrics import accuracy_score
import tensorflow as tf
from tensorflow.python.ops import rnn, rnn_cell
from tf_qrnn import QRNN


class TestQRNNWork(unittest.TestCase):

    def test_qrnn(self):
        print("QRNN Working check")
        with tf.Graph().as_default() as qrnn:
            self.check_by_digits(qrnn=5)

    def xtest_baseline(self):
        print("Baseline Working check")
        with tf.Graph().as_default() as baseline:
            self.check_by_digits()

    def check_by_digits(self, qrnn=-1):
        digits = load_digits()
        horizon, vertical, n_class = (8, 8, 10)  # 8 x 8 image, 0~9 number(=10 class)
        size = 128  # state vector size
        batch_size = 128
        images = digits.images / np.max(digits.images)  # simple normalization
        target = np.array([[1 if t == i else 0 for i in range(n_class)] for t in digits.target])  # to 1 hot vector
        learning_rate = 0.001
        train_iter = 1000

        X = tf.placeholder(tf.float32, [batch_size, vertical, horizon])
        y = tf.placeholder(tf.float32, [batch_size, n_class])
        if qrnn > 0:
            pred = self.qrnn_forward(X, size, n_class, batch_size, conv_size=qrnn)
        else:
            pred = self.baseline_forward(X, size, n_class)

        cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(pred, y))
        optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cost)
        correct_pred = tf.equal(tf.argmax(pred, 1), tf.argmax(y, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            for i in range(train_iter):
                indices = np.random.randint(len(digits.target) - batch_size, size=batch_size)
                _X = images[indices]
                _y = target[indices]
                sess.run(optimizer, feed_dict={X: _X, y: _y})

                if i % 100 == 0:
                    loss = sess.run(cost, feed_dict={X: _X, y: _y})
                    acc = sess.run(accuracy, feed_dict={X: _X, y: _y})
                    print("Iter {}: loss={}, accuracy={}".format(i, loss, acc))
            
            acc = sess.run(accuracy, feed_dict={X: images[-batch_size:], y: target[-batch_size:]})
            print("Testset Accuracy={}".format(acc))
    
    def baseline_forward(self, X, size, n_class):
        shape = X.get_shape()
        _X = tf.transpose(X, [1, 0, 2])
        _X = tf.reshape(_X, [-1, int(shape[2])])
        seq = tf.split(0, int(shape[1]), _X)

        lstm_cell = rnn_cell.BasicLSTMCell(size, forget_bias=1.0)
        outputs, states = rnn.rnn(lstm_cell, seq, dtype=tf.float32)
        with tf.name_scope("baseline_check"):
            W = tf.Variable(tf.random_normal([size, n_class]))
            b = tf.Variable(tf.random_normal([n_class]))
        output = tf.matmul(outputs[-1], W) + b
        return output

    def qrnn_forward(self, X, size, n_class, batch_size, conv_size):
        in_size = int(X.get_shape()[2])
        qrnn = QRNN(in_size=in_size, size=size, conv_size=conv_size)
        qrnn.initialize(batch_size)
        hidden = qrnn.forward(X)
        with tf.name_scope("qrnn_check"):
            W = tf.Variable(tf.random_normal([size, n_class]))
            b = tf.Variable(tf.random_normal([n_class]))
        output = tf.add(tf.matmul(hidden, W), b)
        return output


if __name__ == "__main__":
    unittest.main()