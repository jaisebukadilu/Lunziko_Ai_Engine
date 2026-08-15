"""Module neural — système de réseau neuronal de l'AI Engine.

Couche d'abstraction au-dessus des bibliothèques neuronales : backend NumPy natif
(offline, from scratch) + adaptateurs OPTIONNELS vers PyTorch / TensorFlow / Keras / JAX /
scikit-learn / Transformers (import paresseux, jamais requis pour démarrer). Fournit des
capacités qui améliorent la réflexion et l'efficacité (routage d'intention neuronal, reranking).

Licences : frameworks importés comme dépendances optionnelles (PyTorch BSD, TF/Keras/JAX
Apache-2.0, scikit-learn/Caffe BSD, Transformers Apache-2.0). AUCUN code tiers copié dans le
dépôt (⚠️ OpenNN = LGPL : non embarqué). Cf. règle clean-room de l'écosystème.
"""
