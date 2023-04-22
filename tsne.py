'''
 * @Author: YuanBo 
 * @Date: 2022-11-07 18:33:16 
 * @Last Modified by:   YuanBo 
 * @Last Modified time: 2022-11-07 18:33:16 
 '''
'''
#  tsne_torch.py
#
# Implementation of t-SNE in pytorch. The implementation was tested on pytorch
# > 1.0, and it requires Numpy to read files. In order to plot the results,
# a working installation of matplotlib is required.
#
#
# The example can be run by executing: `python tsne.py`
'''

import numpy as np
import matplotlib.pyplot as pyplot
import argparse
import torch

parser = argparse.ArgumentParser()
parser.add_argument("--xfile", type=str, default="tsne/feature_tsne_adapt_15-1_UCD_step5.csv", help="file name of feature stored")
parser.add_argument("--yfile", type=str, default="tsne/label_tsne_adapt_15-1_UCD_step5.csv", help="file name of label stored")
parser.add_argument("--cuda", type=int, default=1, help="if use cuda accelarate")

opt = parser.parse_args()
print("get choice from args", opt)
xfile = opt.xfile
yfile = opt.yfile

if opt.cuda:
    print("set use cuda")
    torch.set_default_tensor_type(torch.cuda.DoubleTensor)
else:
    torch.set_default_tensor_type(torch.DoubleTensor)


def Hbeta_torch(D, beta=1.0):
    P = torch.exp(-D.clone() * beta)

    sumP = torch.sum(P)

    H = torch.log(sumP) + beta * torch.sum(D * P) / sumP
    P = P / sumP

    return H, P


def x2p_torch(X, tol=1e-5, perplexity=30.0):
    """
        Performs a binary search to get P-values in such a way that each
        conditional Gaussian has the same perplexity.
    """

    # Initialize some variables
    print("Computing pairwise distances...")
    (n, d) = X.shape

    sum_X = torch.sum(X*X, 1)
    D = torch.add(torch.add(-2 * torch.mm(X, X.t()), sum_X).t(), sum_X)

    P = torch.zeros(n, n)
    beta = torch.ones(n, 1)
    logU = torch.log(torch.tensor([perplexity]))
    n_list = [i for i in range(n)]

    # Loop over all datapoints
    for i in range(n):

        # Print progress
        if i % 500 == 0:
            print("Computing P-values for point %d of %d..." % (i, n))

        # Compute the Gaussian kernel and entropy for the current precision
        # there may be something wrong with this setting None
        betamin = None
        betamax = None
        Di = D[i, n_list[0:i]+n_list[i+1:n]]

        (H, thisP) = Hbeta_torch(Di, beta[i])

        # Evaluate whether the perplexity is within tolerance
        Hdiff = H - logU
        tries = 0
        while torch.abs(Hdiff) > tol and tries < 50:

            # If not, increase or decrease precision
            if Hdiff > 0:
                betamin = beta[i].clone()
                if betamax is None:
                    beta[i] = beta[i] * 2.
                else:
                    beta[i] = (beta[i] + betamax) / 2.
            else:
                betamax = beta[i].clone()
                if betamin is None:
                    beta[i] = beta[i] / 2.
                else:
                    beta[i] = (beta[i] + betamin) / 2.

            # Recompute the values
            (H, thisP) = Hbeta_torch(Di, beta[i])

            Hdiff = H - logU
            tries += 1

        # Set the final row of P
        P[i, n_list[0:i]+n_list[i+1:n]] = thisP

    # Return final P-matrix
    return P


def pca_torch(X, no_dims=50):
    print("Preprocessing the data using PCA...")
    (n, d) = X.shape
    X = X - torch.mean(X, 0)

    (l, M) = torch.eig(torch.mm(X.t(), X), True)
    # split M real
    # this part may be some difference for complex eigenvalue
    # but complex eignevalue is meanless here, so they are replaced by their real part
    i = 0
    while i < d:
        if l[i, 1] != 0:
            M[:, i+1] = M[:, i]
            i += 2
        else:
            i += 1

    Y = torch.mm(X, M[:, 0:no_dims])
    return Y


def tsne(X, no_dims=2, initial_dims=50, perplexity=30.0):
    """
        Runs t-SNE on the dataset in the NxD array X to reduce its
        dimensionality to no_dims dimensions. The syntaxis of the function is
        `Y = tsne.tsne(X, no_dims, perplexity), where X is an NxD NumPy array.
    """

    # Check inputs
    if isinstance(no_dims, float):
        print("Error: array X should not have type float.")
        return -1
    if round(no_dims) != no_dims:
        print("Error: number of dimensions should be an integer.")
        return -1

    # Initialize variables
    X = pca_torch(X, initial_dims)
    (n, d) = X.shape
    max_iter = 1000
    initial_momentum = 0.5
    final_momentum = 0.8
    eta = 500
    min_gain = 0.01
    Y = torch.randn(n, no_dims)
    dY = torch.zeros(n, no_dims)
    iY = torch.zeros(n, no_dims)
    gains = torch.ones(n, no_dims)

    # Compute P-values
    P = x2p_torch(X, 1e-5, perplexity)
    P = P + P.t()
    P = P / torch.sum(P)
    P = P * 4.    # early exaggeration
    print("get P shape", P.shape)
    P = torch.max(P, torch.tensor([1e-21]))

    # Run iterations
    for iter in range(max_iter):

        # Compute pairwise affinities
        sum_Y = torch.sum(Y*Y, 1)
        num = -2. * torch.mm(Y, Y.t())
        num = 1. / (1. + torch.add(torch.add(num, sum_Y).t(), sum_Y))
        num[range(n), range(n)] = 0.
        Q = num / torch.sum(num)
        Q = torch.max(Q, torch.tensor([1e-12]))

        # Compute gradient
        PQ = P - Q
        for i in range(n):
            dY[i, :] = torch.sum((PQ[:, i] * num[:, i]).repeat(no_dims, 1).t() * (Y[i, :] - Y), 0)

        # Perform the update
        if iter < 20:
            momentum = initial_momentum
        else:
            momentum = final_momentum

        gains = (gains + 0.2) * ((dY > 0.) != (iY > 0.)).double() + (gains * 0.8) * ((dY > 0.) == (iY > 0.)).double()
        gains[gains < min_gain] = min_gain
        iY = momentum * iY - eta * (gains * dY)
        Y = Y + iY
        Y = Y - torch.mean(Y, 0)

        # Compute current value of cost function
        if (iter + 1) % 10 == 0:
            C = torch.sum(P * torch.log(P / Q))
            print("Iteration %d: error is %f" % (iter + 1, C))

        # Stop lying about P-values
        if iter == 100:
            P = P / 4.

    # Return solution
    return Y

 


# colors = ['springgreen','darkorange','deepskyblue','navy','darkslategray','brown','gold','blueviolet',
#             'rosybrown','gray','deeppink','sienna','violet','aquamarine','black','darkcyan','red','blue','green','purple','mediumspringgreen']
# colors = [
#     (255,255,255,1),(128,0,0,1),(0,128,0,1),(128,128,0,1),(0,0,128,1),(128,0,128,1),(0,128,128,1),(128,128,128,1),(64,0,0,1),
#     (192,0,0,1),(64,128,0,1),(192,128,0,1),(64,0,128,1),(192,0,128,1),(64,128,128,1),(192,128,128,1),(0,64,0,1),(128,64,0,1),
#     (0,192,0,1),(128,192,0,1),(0,64,128,1)
# ]     
colors = [
    '#FFFFFF','#800000','#008000','#808000','#000080','#800080','#008080','#808080','#400000',
    '#C00000','#408000','#C08000','#400080','#C00080','#408080','#C08080','#004000','#804000',
    '#00C000','#80C000','#004080'
]  
def plot_embedding(data, label, title):
    x_min, x_max = np.min(data, 0), np.max(data, 0)
    data = (data - x_min) / (x_max - x_min)
    fig = pyplot.figure(dpi=300,figsize=(10.0,10.0))
    # fig = pyplot.figure()
    ax = pyplot.subplot(111)
    for i in range(data.shape[0]):
        if label[i]>21 and label[i]!=255:
            label[i]=255
        if label[i]<=0 or label[i]>20:
            continue
        pyplot.text(data[i, 0], data[i, 1], str(int(label[i])),
                #  color=pyplot.cm.Set1(label[i]),
                color = colors[int(label[i])] if int(label[i])<=20 else [0,0,0,0],
                fontdict={'weight': 'bold', 'size': 10}
                )
    # pyplot.legend(loc="best")
    # pyplot.scatter(data[i, 0], data[i, 1], label[i],size=5, marker='.')
        
    pyplot.xticks([])
    pyplot.yticks([])
    # pyplot.title(title)
    pyplot.savefig('tsne/figs/tsne_15-1_PLOP_step5.png')
    return fig

def plot_embedding_3D(data, label, title):
    x_min, x_max = np.min(data, 0), np.max(data, 0)
    data = (data - x_min) / (x_max - x_min)
    # fig = pyplot.figure(dpi=300,figsize=(5.0,5.0))
    fig = pyplot.figure()
    ax = pyplot.subplot(111)
    ax = pyplot.axes(projection='3d')
    for i in range(data.shape[0]):
        if label[i]>21 and label[i]!=255:
            label[i]=255
        if label[i]<=0 or label[i]>20:
            continue
        pyplot.text(data[i, 0], data[i, 1], str(int(label[i])),
                #  color=pyplot.cm.Set1(label[i]),
                color = colors[int(label[i])] if int(label[i])<=20 else [0,0,0,0],
                fontdict={'weight': 'bold', 'size': 8}
                )
    # pyplot.legend(loc="best")
    # pyplot.scatter(data[i, 0], data[i, 1], label[i],size=5, marker='.')
        
    pyplot.xticks([])
    pyplot.yticks([])
    pyplot.zticks([])
    # pyplot.title(title)
    pyplot.savefig('tsne/tsne_15-5_step1_ours8.png')
    return fig



if __name__ == "__main__":
    print("Run Y = tsne.tsne(X, no_dims, perplexity) to perform t-SNE on your dataset.")

    X = np.loadtxt(xfile)
    X_T = torch.Tensor(X)
    labels = np.loadtxt(yfile).tolist()
    

    # confirm that x file get same number point than label file
    # otherwise may cause error in scatter
    assert(len(X_T[:, 0])==len(X_T[:,1]))
    assert(len(X_T)==len(labels))

    
    # with torch.no_grad():
    #     Y = tsne(X_T, 2, 50, 20.0)

    # if opt.cuda:
    #     Y = Y.cpu().numpy()

    # cValue = ['b','c','g','k','m','r','w','y','r','g','b']
    # # pyplot.scatter(Y[:, 0], Y[:, 1], labels, marker='.')
    # pyplot.scatter(Y[:, 0], Y[:, 1], s=5, c = labels, marker='.')
    
    # pyplot.savefig('tsne.png')
    # pyplot.show()
    
    



    from sklearn.manifold import TSNE
    # tsne = TSNE(n_components=2, init='pca', random_state=0)
    tsne = TSNE(n_components=3, init='pca', n_iter=500)
    result = tsne.fit_transform(X)
    print('result:',result.shape)

    # save 2D map
    fig = plot_embedding(result, labels,  'tsne') 
    pyplot.show()

    #save 3D map
    # fig = plot_embedding_3D(result, labels, 'tsne')
    # pyplot.show()

 
