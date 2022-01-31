
"""
LDIS 
"""

from src.main.python.iSel.base import InstanceSelectionMixin
import numpy as np
import random
from sklearn.utils.validation import check_X_y
from sklearn.neighbors.classification import KNeighborsClassifier

from src.main.python.iSel.enn import ENN
from src.main.python.iSel.cnn import CNN

from src.main.python.utils.general import load_splits_ids
from sklearn.metrics.pairwise import euclidean_distances

from collections import Counter
import copy
import time


class CDIS(InstanceSelectionMixin):
    """ Central density-based instance selection (LDIS)
    Descrição:
    ==========


    Parametros:
    ===========


    Atributos:
    ==========


    Ref.
    ====

    """

    # def __init__(self, dataset, fold, n_neighbors=3):
    def __init__(self, n_neighbors=3):
        self.n_neighbors = n_neighbors
        #self.fold = fold
        #self.dataset = dataset
        self.sample_indices_ = []

    def set_nn(self, X, y):
        """#setando o classificador
        #if self.classifier == None:

        #Coloquei um a mais pq o vizinho mais proximo de x é ele mesmo
        self.classifier = KNeighborsClassifier(n_neighbors=self.n_neighbors+1)
        #if self.classifier.n_neighbors != self.n_neighbors:
        #	self.classifier.n_neighbors = self.n_neighbors

        self.classifier.fit(X, y)
        #print(self.classifier.kneighbors(X,return_distance=False)[0])
        #print(self.classifier.kneighbors(X,return_distance=False)[1])

        #[:,1:] Faz slice de 1 a ultima coluna, ou seja, remove o proprio x
        #self.nn = self.classifier.kneighbors(X,return_distance=False)[:,1:]
        result = self.classifier.kneighbors(X,return_distance=False)[:,1:]
        self.nn = [set(result[x]) for x in range(len(result))]
        #print(self.nn)"""

        self.k = copy.copy(self.n_neighbors)
        if X.shape[0] <= self.k:
            print("mudou k")
            self.k = X.shape[0] - 1

        #self.pairwise_distances = euclidean_distances(X)
        #self.pkn = np.argsort(self.pairwise_distances)[:,1:self.k+1]

        # Primeiro computa a distancia de todo mundo pra todo mundo
        self.pairwise_distances = euclidean_distances(X)

        # Depois setamos a distancia pra ele mesmo (diagonal) como -1, pra garantir que cada instancia seja o mais proximo de si memso
        for i in range(self.pairwise_distances.shape[0]):
            self.pairwise_distances[i][i] = -1.0

        # A seguir ordenamos a distancia e pegamos da coluna 1 em diante (excluindo a propria isntancia)
        #self.nn_complete = np.argsort(self.pairwise_distances)[:,1:]

        #self.nn = [x[:self.n_neighbors] for x in self.nn_complete]
        self.pkn = np.argsort(self.pairwise_distances)[:, 1:self.k+1]

    def set_density(self):

        len_c = len(self.pairwise_distances)
        self.density = np.zeros(len_c)
        for i in range(len_c):
            #dens = 0.0
            for j in range(len_c):
                if i != j:
                    # dens += self.pairwise_distances[]
                    #self.density[i] += self.pairwise_distances[i][j]
                    self.density[i] += 1.0 / \
                        (1.0 + self.pairwise_distances[i][j])

            #self.density[i] = self.density[i] * (-1.0) / len_c
            self.density[i] = self.density[i] / \
                (1.0 + self.dist_x_to_centroid_pkn[i])

        # exit()

    def set_dist_x_to_centroid_pkn(self, X):
        #centroid_pkn = []
        self.dist_x_to_centroid_pkn = np.zeros(X.shape[0])

        for i in range(X.shape[0]):

            # print(X[self.pkn[i]].shape)
            #print(np.all(np.sum(X[self.pkn[i]], axis=0)/3.0 == np.mean(X[self.pkn[i]], axis=0)))
            # exit()
            # print(X[self.pkn[i]].shape[0])
            if X[self.pkn[i]].shape[0] > 0:
                # , dtype=np.float64)
                centroid_pkn_x = np.mean(X[self.pkn[i]], axis=0)
                self.dist_x_to_centroid_pkn[i] = euclidean_distances(X[i], centroid_pkn_x)[
                    0]
            else:
                print("Sem viz")
                centroid_pkn_x = X[i]
                self.dist_x_to_centroid_pkn[i] = 0.0
            # print(centroid_pkn_x.shape)
            # exit()
            #self.dist_x_to_centroid_pkn[i] = euclidean_distances(X[i], centroid_pkn_x)[0]

        #np.mean(X[self.pkn[0]], axis=0)
        #print(euclidean_distances(X[0], centroid_pkn))
        #self.centroid = np.zeros(X.shape[1])
        #self.centroid = np.mean(X,axis=0)
        # print(X.shape)
        # print(self.centroid.shape)
        # for x in range(X.shape[0]):
            # print(self.pkn[0])
            #print(np.mean(X[self.pkn[0]], axis=0).shape)

        # exit()
    def c(self, X, y, l):

        indice_mapeado = np.where(y == l)[0]
        X_tmp = copy.copy(X[indice_mapeado])
        y_tmp = copy.copy(y[indice_mapeado])
        return X_tmp, y_tmp, indice_mapeado

    def select_data(self, X, y):

        X, y = check_X_y(X, y, accept_sparse="csr")

        len_original_y = len(y)

        self.S = [x for x in range(len_original_y)]

        # mask contem os elementos escolhidos, inicialmente todos são True
        self.mask = np.zeros(y.size, dtype=bool)  # mask = mascars

        # seta os n vizinhos mais proximos de cada instancia
        #self.set_nn(X, y)

        labels = list(sorted(list(set(y))))

        nSel = 0

        for l in labels:

            X_tmp, y_tmp, indice_mapeado = self.c(X, y, l)

            self.set_nn(X_tmp, y_tmp)
            self.set_dist_x_to_centroid_pkn(X_tmp)
            self.set_density()

            for x in range(X_tmp.shape[0]):
                foundDenser = False

                for neighbor in self.pkn[x]:
                    # print(neighbor)

                    if(self.density[x] < self.density[neighbor]):
                        foundDenser = True
                        # print("sim")
                        break

                if not foundDenser:
                    nSel += 1
                    self.mask[indice_mapeado[x]] = True

        # print(nSel)

        # exit()

        self.X_ = np.asarray(X[self.mask])
        self.y_ = np.asarray(y[self.mask])
        # print(X[self.mask].shape)
        self.sample_indices_ = np.asarray(self.S)[self.mask]

        # print(sorted(idx_prots_s))
        # print(float(len(self.y_))/len(y))

        self.reduction_ = 1.0 - float(len(self.y_))/len_original_y
        return self.X_, self.y_
