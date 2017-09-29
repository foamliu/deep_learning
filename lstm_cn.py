#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Wed Sep 27 18:13:56 2017

@author: yangliu
"""

from __future__ import print_function
import collections
import numpy as np
import random
import collections
import time
import os
from os import walk
from os.path import join
from six.moves import range
import tensorflow as tf
from tensorflow.contrib import rnn
import jieba


def cleanse(content):
    content = content.replace('\n','')
    content = content.replace('\r','')
    content = content.replace('\u3000','')
    content = content.replace(' ','')
    content = content.replace('\t','')
    return content


def load_file(folder):
    paths = [join(dirpath, name)
        for dirpath, dirs, files in walk(folder)
        for name in files
        if not name.startswith('.') ]
    concat = u''
    for path in paths:
        with open(path, 'r', encoding='utf-8') as myfile:
            #print(path)
            content = myfile.read()
            concat += cleanse(content)

    return concat


def read_data(concat):
    """Extract as a list of words"""
    seg_list = jieba.cut(concat, cut_all=False)
    #print "/".join(seg_list)
    words = []
    for t in seg_list:
        words.append(t)

    return words


def build_dataset(words):
    vocab = set(words)
    vocab_size = len(vocab)
    print('Vocabulary size %d' % vocab_size)

    count = [['UNK', -1]]
    count.extend(collections.Counter(words).most_common(vocab_size))
    dictionary = dict()
    for word, _ in count:
        dictionary[word] = len(dictionary)
    data = list()
    unk_count = 0
    for word in words:
        if word in dictionary:
            index = dictionary[word]
        else:
            index = 0  # dictionary['UNK']
            unk_count = unk_count + 1
        data.append(index)
    count[0][1] = unk_count
    reverse_dictionary = dict(zip(dictionary.values(), dictionary.keys()))
    return data, count, dictionary, reverse_dictionary, vocab_size


start_time = time.time()
def elapsed(sec):
    if sec<60:
        return str(sec) + " sec"
    elif sec<(60*60):
        return str(sec/60) + " min"
    else:
        return str(sec/(60*60)) + " hr"
    
    
def tf_lstm():

    # Parameters
    learning_rate = 0.001
    training_iters = 50000
    display_step = 1000
    n_input = 3
    # number of units in RNN cell
    n_hidden = 512

    graph = tf.Graph()
    with graph.as_default():
        # tf Graph input
        x = tf.placeholder("float", [None, n_input, 1])
        y = tf.placeholder("float", [None, vocab_size])
        # RNN output node weights and biases
        weights = {
            'out': tf.Variable(tf.random_normal([n_hidden, vocab_size]))
        }
        biases = {
            'out': tf.Variable(tf.random_normal([vocab_size]))
        }
        def RNN(x, weights, biases):
            # reshape to [1, n_input]
            x = tf.reshape(x, [-1, n_input])
            # Generate a n_input-element sequence of inputs
            # (eg. [had] [a] [general] -> [20] [6] [33])
            x = tf.split(x,n_input,1)
            # 2-layer LSTM, each layer has n_hidden units.
            # Average Accuracy= 95.20% at 50k iter
            
            # rnn_cell = rnn.MultiRNNCell([rnn.BasicLSTMCell(n_hidden),rnn.BasicLSTMCell(n_hidden)])
            # 1-layer LSTM with n_hidden units but with lower accuracy.
            # Average Accuracy= 90.60% 50k iter
            # Uncomment line below to test but comment out the 2-layer rnn.MultiRNNCell above
            rnn_cell = rnn.BasicLSTMCell(n_hidden)
            # generate prediction
            outputs, states = rnn.static_rnn(rnn_cell, x, dtype=tf.float32)
            # there are n_input outputs but
            # we only want the last output
            return tf.matmul(outputs[-1], weights['out']) + biases['out']
        pred = RNN(x, weights, biases)
        # Loss and optimizer
        cost = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(logits=pred, labels=y))
        optimizer = tf.train.RMSPropOptimizer(learning_rate=learning_rate).minimize(cost)
        # Model evaluation
        correct_pred = tf.equal(tf.argmax(pred,1), tf.argmax(y,1))
        accuracy = tf.reduce_mean(tf.cast(correct_pred, tf.float32))
        
        # Create a summary to monitor cost tensor
        tf.summary.scalar("loss", cost)
        # Create a summary to monitor accuracy tensor
        tf.summary.scalar("accuracy", accuracy)

        # Merge all summaries into a single op
        merged_summary_op = tf.summary.merge_all()
        
        # Initializing the variables
        init = tf.global_variables_initializer()


    with tf.Session(graph=graph) as session:
        session.run(init)
        print('Initialized')
        
        step = 0
        offset = random.randint(0,n_input+1)
        end_offset = n_input + 1
        acc_total = 0
        loss_total = 0
        
        writer.add_graph(session.graph)

        while step < training_iters:
            # Generate a minibatch. Add some randomness on selection process.
            if offset > (len(training_data)-end_offset):
                offset = random.randint(0, n_input+1)
            symbols_in_keys = [ [dictionary[ str(training_data[i])]] for i in range(offset, offset+n_input) ]
            symbols_in_keys = np.reshape(np.array(symbols_in_keys), [-1, n_input, 1])
            symbols_out_onehot = np.zeros([vocab_size], dtype=float)
            symbols_out_onehot[dictionary[str(training_data[offset+n_input])]] = 1.0
            symbols_out_onehot = np.reshape(symbols_out_onehot,[1,-1])
            _, acc, loss, onehot_pred, summary = session.run([optimizer, accuracy, cost, pred, merged_summary_op], \
                                                    feed_dict={x: symbols_in_keys, y: symbols_out_onehot})
            loss_total += loss
            acc_total += acc
            if (step+1) % display_step == 0:
                print("Iter= " + str(step+1) + ", Average Loss= " + \
                      "{:.6f}".format(loss_total/display_step) + ", Average Accuracy= " + \
                      "{:.2f}%".format(100*acc_total/display_step))
                acc_total = 0
                loss_total = 0
                symbols_in = [training_data[i] for i in range(offset, offset + n_input)]
                symbols_out = training_data[offset + n_input]
                symbols_out_pred = reverse_dictionary[int(tf.argmax(onehot_pred, 1).eval())]
                print("%s - [%s] vs [%s]" % (symbols_in,symbols_out,symbols_out_pred))
                
                writer.add_summary(summary, step)
            step += 1
            offset += (n_input+1)
        print("Optimization Finished!")
        print("Elapsed time: ", elapsed(time.time() - start_time))
        print("Run on command line.")
        print("\ttensorboard --logdir=%s" % (log_path))
        print("Point your web browser to: http://localhost:6006/")
    
        while True:
            prompt = "%s words: " % n_input
            sentence = input(prompt)
            sentence = sentence.strip()
            words = sentence.split(' ')
            if len(words) != n_input:
                continue
            try:
                symbols_in_keys = [dictionary[str(words[i])] for i in range(len(words))]
                for i in range(32):
                    keys = np.reshape(np.array(symbols_in_keys), [-1, n_input, 1])
                    onehot_pred = session.run(pred, feed_dict={x: keys})
                    onehot_pred_index = int(tf.argmax(onehot_pred, 1).eval())
                    sentence = "%s %s" % (sentence,reverse_dictionary[onehot_pred_index])
                    symbols_in_keys = symbols_in_keys[1:]
                    symbols_in_keys.append(onehot_pred_index)
                print(sentence)
            except:
                print("Word not in dictionary")




if __name__ == '__main__':
    folder = '《刘慈欣作品全集》(v1.0)'
    concat = load_file(folder)
    #print(concat[20000:20000+100])
    print("Full text length %d" %len(concat))

    words = read_data(concat)
    print('Data size %d' % len(words))

    data, count, dictionary, reverse_dictionary, vocab_size = build_dataset(words)
    print('Most common words ', count[:10])
    print('Sample data', data[:10])
    #del words  # Hint to reduce memory.

    # Target log path
    log_path = '/tmp/tensorflow/rnn_words'
    logdir = log_path
    
    previous_runs = os.listdir(logdir)
    if len(previous_runs) == 0:
        run_number = 1
    else:
        run_number = max([int(s.split('run_')[1]) for s in previous_runs]) + 1
    
    rundir = 'run_%02d' % run_number
    logdir = os.path.join(logdir, rundir)
    writer = tf.summary.FileWriter(logdir)
    training_data = words
    tf_lstm()
