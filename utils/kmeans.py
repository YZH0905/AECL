import torch
import numpy as np
from utils.metric import Confusion
from sklearn.cluster import KMeans


def get_mean_embeddings(bert, input_ids, attention_mask):
    bert_output = bert.forward(input_ids=input_ids, attention_mask=attention_mask)
    attention_mask = attention_mask.unsqueeze(-1)
    mean_output = torch.sum(bert_output[0]*attention_mask, dim=1) / torch.sum(attention_mask, dim=1)
    return mean_output

    
def get_batch_token(tokenizer, text, max_length):
    token_feat = tokenizer.batch_encode_plus(
        text, 
        max_length=max_length, 
        return_tensors='pt', 
        padding='max_length', 
        truncation=True
    )
    return token_feat


def get_kmeans_centers(args, model, test_Dataloader, num_classes):
    for i, (input_ids, attention_mask, label, index) in enumerate(test_Dataloader):
        corpus_embeddings = model.get_mean_embeddings(input_ids.squeeze(), attention_mask.squeeze())
        
        if i == 0:
            all_labels = label
            all_embeddings = corpus_embeddings.detach().cpu().numpy()
        else:
            all_labels = torch.cat((all_labels, label), dim=0)
            all_embeddings = np.concatenate((all_embeddings, corpus_embeddings.detach().cpu().numpy()), axis=0)



    # Perform KMeans clustering
    confusion = Confusion(num_classes)
    clustering_model = KMeans(n_clusters=num_classes, n_init='auto', random_state=args.seed, max_iter=3000, tol=0.01)
    clustering_model.fit(all_embeddings)
    cluster_assignment = clustering_model.labels_

    true_labels = all_labels
    kmeans_label = torch.tensor(cluster_assignment.astype(int))

    confusion.add(kmeans_label, true_labels)
    confusion.optimal_assignment(num_classes)
    clusterscores = confusion.clusterscores(true_labels, kmeans_label)

    print("Iterations:{}, Clustering ACC:{:.4f}, centers:{}".format(clustering_model.n_iter_, confusion.acc(), clustering_model.cluster_centers_.shape))
    print('Clustering scores:', clusterscores)


    return kmeans_label



