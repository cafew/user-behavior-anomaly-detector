#!/usr/bin/python

import json
import lsanomaly
import matplotlib.pyplot as plt
import numpy as np
import pandas
from keras.preprocessing import sequence
from sklearn import metrics
from sklearn import svm

import helpers

class OCSVM:
    def __init__(self):
        self.settings = helpers.ConfigSectionMap('settings.ini', 'OCSVM')
        self.data = helpers.ConfigSectionMap('settings.ini', 'Data')

    def print_accuracy(self, title, datasetY, predictions):
        print title

        print("accuracy: ", metrics.accuracy_score(datasetY, predictions))
        print("precision: ", metrics.precision_score(datasetY, predictions))
        print("recall: ", metrics.recall_score(datasetY, predictions))
        print("f1: ", metrics.f1_score(datasetY, predictions))
        print("area under curve (auc): ", metrics.roc_auc_score(datasetY, predictions))

    def replace_in_list(self, list, oldChar, newChar):
        for n, i in enumerate(list):
            if i == 'anomaly':
                list[n] = -1.

    def save_parameters(self, model):
        parameters = model.get_params()
        parameters = json.dumps(parameters)
        with open("model_ocsvm.json", "w") as json_file:
            json_file.write(parameters)

        print("Saved parameters to filesystem")

    def load_parameters(self, model, model_filename = 'model_ocsvm.json'):
        json_file = open(model_filename, 'r')
        loaded_parameters = json.loads(json_file)
        json_file.close()
        print "Loaded parameters from filesystem."

        return model.set_params(loaded_parameters)


    def train_with_scikit(self, trainX, testX):
        settings = self.settings

        if (settings['load_parameters'] == True):
            parameters = self.load_parameters()
            clf = svm.OneClassSVM(parameters)
        else:
            clf = svm.OneClassSVM(nu=settings['nu'], kernel=settings['kernel'], gamma=settings['gamma'], verbose=settings['verbose'])

        clf.fit(trainX)
        y_pred_train = clf.predict(trainX)
        y_pred_test = clf.predict(testX)

        n_error_train = y_pred_train[y_pred_train == -1].size
        n_error_test = y_pred_test[y_pred_test == -1].size

        return y_pred_train, y_pred_test, n_error_train, n_error_test


    def train_with_lsanomaly(self, trainX, testX):
        anomalymodel = lsanomaly.LSAnomaly()
        anomalymodel.fit(trainX)
        y_pred_train = anomalymodel.predict(trainX)
        y_pred_test = anomalymodel.predict(testX)

        # Process results
        self.replace_in_list(y_pred_train, 'anomaly', -1)
        self.replace_in_list(y_pred_test, 'anomaly', -1)
        n_error_train = y_pred_train.count(-1)
        n_error_test = y_pred_test.count(-1)

        return y_pred_train, y_pred_test, n_error_train, n_error_test

    def run(self):
        xx, yy = np.meshgrid(np.linspace(-5, 5, 500), np.linspace(-5, 5, 500))
        max_vector_length = 30

        # Create datasets
        train_dataset = pandas.read_csv(self.data['train_dataset_file'], delimiter=';', engine='python')
        test_dataset = pandas.read_csv(self.data['test_dataset_file'], delimiter=';', engine='python')

        train_dataset = train_dataset[:len(train_dataset)/6]

        # Convert strings
        train_dataset_array = helpers.collection_values_to_array(train_dataset)
        test_dataset_array = helpers.collection_values_to_array(test_dataset)

        # Padding (from left)
        trainX = sequence.pad_sequences(train_dataset_array, maxlen=max_vector_length)
        testX = sequence.pad_sequences(test_dataset_array, maxlen=max_vector_length) #padding='pre'

        assert (trainX.shape[1] == testX.shape[1])

        # fit the model
        if (self.settings['use_lsanomaly'] == True):
            y_pred_train, y_pred_test, n_error_train, n_error_test = self.train_with_lsanomaly(trainX, testX)
        else:
            y_pred_train, y_pred_test, n_error_train, n_error_test = self.train_with_scikit(trainX, testX)

        #testX_plot = []
        #for n, i in enumerate(testX):
        #    for m, j in enumerate(testX):
        #        if i >= 0:
        #            testX_plot.append(n)

        #plt.set_cmap(plt.cm.Paired)
        #plt.scatter(trainX[y_pred_train>0], trainX[y_pred_train>0], c='black', label='inliers')
        #plt.scatter(trainX[y_pred_train <= 0], trainX[y_pred_train <= 0], c='red', label='outliers')
        #plt.scatter(testX_plot, testX_plot, c='black', label='inliers')
        #plt.scatter(testX[y_pred_test < 0], testX[y_pred_test < 0], c='red', label='outliers')
        #plt.axis('tight')
        #plt.legend()
        #plt.show()

        # Visualize
        plt.title("Novelty Detection")
        plt.figure(1)
        plt.subplot(211)
        plt.plot(trainX, 'ro', testX, 'g^')

        plt.subplot(212)
        plt.plot(y_pred_train, 'ro', y_pred_test, 'g^')
        plt.xlabel(
            "Anomalies in training set: %d/%d; Anomalies in test set: %d/%d;"
            % (n_error_train, trainX.shape[0], n_error_test, testX.shape[0]))
        plt.show()


        # Display accuracy on validation set
        #print_accuracy("Validation", testX, y_pred_test)

        #plt.contourf(xx, yy, Z, levels=np.linspace(Z.min(), 0, 7), cmap=plt.cm.PuBu)
        #a = plt.contour(xx, yy, Z, levels=[0], linewidths=2, colors='darkred')
        #plt.contourf(xx, yy, Z, levels=[0, Z.max()], colors='palevioletred')
