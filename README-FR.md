![Latest Release](https://img.shields.io/github/release/VAKazakov/EDMC-Triumvirate.svg)

This ReadMe on other languages: [English](README-EN.md), [Русский](README.md)

![Triumvirate](https://user-images.githubusercontent.com/25157296/117574269-03a3d500-b0e5-11eb-901d-44a4812e2de0.png)

# EDMC-Triumvirate
Le plugin Triumvirate pour EDMC, développé par Close Encounters Corps, est un élément important de l'écosystème Gehirn (server-site-plugin-discord). Il s'agit d'un outil polyvalent de collecte et de traitement des données de jeu, qui vous permet de surveiller les effets dans les systèmes de faction que vous contrôlez, d'identifier les tâches BGS pour l'utilisateur, de coordonner le travail des pilotes, d'alerter vos collègues sur des situations anormales dans les vols long-courriers. A l'avenir, ce plugin recevra un certain nombre d'améliorations destinées à optimiser le travail des pilotes dans l'immensité de la galaxie.

***Par principe, les informations confidentielles sur les utilisateurs, les caractéristiques des systèmes et les données personnelles non publiques ne sont pas collectées, stockées ou traitées.***

# Prêtez une attention particulière:

La fonctionnalité est garantie sur les systèmes Windows 10 et Windows 11. Le plugin EDMC Triumvirate n'est absolument PAS compatible avec EDMC-Canonn, EDMC-USS-Survey ou l'ancienne édition EDMC-USS-Survey-Triumvirate. Le plugin EDMC-Canonn a été intégré à l'origine dans Triumvirate, et nous avons également intégré le support pour Discord Presence, FCMC et le transfert des données scientifiques collectées non seulement vers les serveurs Canonn mais aussi vers les adresses d'autres entités scientifiques. Un système d'émission et d'enregistrement des missions accomplies dans le cadre de l'activité contre le Club est en place.

# Caractéristiques du plug-in (à mettre à jour au fur et à mesure des améliorations)

## Élément recevant des commandes de l'utilisateur

### Commande /sos

Après qu'un pilote ait écrit la commande "/sos" dans le chat du jeu (dans tous les cas), le plugin générera et enverra au chat discord de la faction* (dans un canal dédié) un paquet de données avec l'emplacement, la quantité de carburant, l'emplacement et le temps pour vider le réservoir. Grâce à ces données, un pilote en situation dangereuse pourra obtenir du carburant et se ravitailler à temps.

AVERTISSEMENT! Une seule demande suffit, les demandes de spam seront ignorées. Après une seule demande, vous devrez vous déconnecter du menu du jeu et contacter le serveur discord du Close Encounters Corps pour savoir quel pilote a répondu à votre demande. Les demandes provenant des systèmes de la liste des grenouilles ne seront pas acceptées, en raison de l'impossibilité d'y arriver. Les pilotes hostiles à la faction du Close Encounters Corps ou ayant des activités suspectes ou provocatrices ne seront pas pris en charge par le système.

\*Si vous êtes un pilote indépendant (selon le plugin), que vous ne figurez pas sur la liste des ennemis de la communauté et que vous ne vous livrez pas à des activités destructrices suspectes, votre demande d'assistance sera transmise à Close Encounters Corps.

## Élément du système de course d'orientation (alias Patrouille)

Le système de guidage est utilisé pour naviguer en vol vers des points d'intérêt et comprend:

* Localisation de vos navires. Un outil qui donne des informations en temps réel sur la localisation de vos navires. L'ajout d'une fonction de type compas/GPS pour le vol visuel vers des points d'intérêt est en cours de développement.
* L'automatisation et le transfert de toutes les fonctions du système pour le suivi des niveaux d'influence fractionnaires dans les systèmes contrôlés pour l'analyse et le traitement vers des serveurs fractionnaires sont en cours de développement. Cet outil donne un bref résumé de l'état des systèmes dans lesquels notre faction est présente. Pour les chefs de faction, il existe une fonction permettant d'assigner manuellement des tâches à des systèmes spécifiques pour les envoyer directement au plugin, et la possibilité d'envoyer semi-automatiquement des tâches pour réduire les statuts négatifs.
* Nous travaillons sur l'ajout d'une fonction de navigation orbitale et de suivi sur les coordonnées spécifiées avec la sortie des informations de référence sur les points connus de l'itinéraire.
* Ajout d'une fonction permettant d'envoyer les données relatives aux navires du commandant au serveur et au site web afin d'afficher les informations de localisation sur une carte interactive en temps réel ou pseudo-réel.
* Ajout d'une fonction pour donner des informations sur la localisation de votre navire porteur, la liste de ses caractéristiques et le taux de remplissage du réservoir de carburant est en cours de développement.
* Ajout d'une fonction d'identification "ami ou ennemi" pour déterminer si vous êtes face à un partenaire, un allié ou un ennemi/neutre.
* Nous travaillons sur l'ajout d'une fonction de distance parcourue sur le SRV.

## Élément du centre d'information

Permet de lire les dernières nouvelles et les informations les plus récentes sur la galaxie.

## Élément sur les rapports d'interceptions des thargoïdes

Permet de collecter et d'analyser des informations sur l'heure et le lieu des interceptions de vos vaisseaux par les Thargoids. Permet d'estimer avec précision l'ampleur d'une invasion extraterrestre.

## Élément sur l'analyse de l'élimination des thargoïdes

Collecte et traite les informations relatives à l'heure, à l'emplacement, au type et au nombre de vaisseaux thargoids abattus. Utilisé pour résumer la semaine et élaborer un plan clair pour contrer l'invasion extraterrestre.

* L'ajout de la fonction de transfert de toutes les informations collectées vers les serveurs de la faction pour traitement et transfert vers les tableaux interactifs sur le site web de la faction est en cours d'élaboration.

## Élément sur les rapports du NHSS

Collecte et analyse des informations sur les signaux extraterrestres détectés.

## Point sur les rapports du FSS

Collecte et analyse des informations complètes sur le système actuel.

## Élément de Codex

Collecte des informations sur les entrées du journal et les synchronise avec des services scientifiques externes tels que la [base de données Canonn] (https://api.canonn.tech/documentation) dans un mode d'échange volontaire.

## Élément d'analyse des informations contenues dans le carnet de vol du pilote

Collecte et traite les informations du journal de bord. Fournit des mises à jour sur les marchés, les produits de base et les prix. Aide tous les pilotes à obtenir des données actualisées. Transmet les informations reçues à l'INARA, à l'EDSM, à l'EDDB et à d'autres systèmes de profil similaires.

## Élément de collecte d'informations sur les navires transporteurs

Collecte et traite les informations relatives au navire transporteur d'un pilote donné. Fournit des mises à jour au site web du FCMC, vous permet d'afficher, presque en temps réel, les porte-avions des pilotes de la faction sur une carte interactive sur le site web de la faction. Aide tous les pilotes à obtenir des données actualisées. Transmet les informations reçues à l'INARA, à l'EDSM, à l'EDDB et à d'autres systèmes de profil similaires.

## Élément sur la modification de l'interface en fonction de la faction

* L'ajout d'une fonction permettant de modifier le style de la fenêtre du plugin pour l'adapter au style d'une faction spécifique est en cours d'élaboration.

## Instructions d'installation:

1) Téléchargez et installez la dernière version de [EDMarketConnector] (https://github.com/Marginal/EDMarketConnector/blob/rel-342/README.md#installation) (si elle est déjà installée, assurez-vous de vérifier les mises à jour de l'EDMC).

2) Téléchargez la dernière version de [EDMC-Triumvirate] (https://github.com/VAKazakov/EDMC-Triumvirate/releases/latest) en cliquant sur Source code(zip)

3) Décompressez le dossier du plugin dans %USERPROFILE%\AppData\Local\EDMarketConnector\plugins (vous pouvez le coller dans la barre d'adresse de l'explorateur).

4) Lancez EDMC, si la fenêtre [such](https://cdn.discordapp.com/attachments/518418556615000074/590004329692397579/unknown.png) apparaît, passez à l'étape 5, sinon vous devrez valider l'installation.

5) ***Vous êtes génial!***

## Développement

Le plugin, comme l'EDMC en général, fonctionne actuellement sous Python 3.7, mais il est possible de passer à des versions plus récentes de Python.
Comment préparer l'environnement pour le développement :

```bash
pip install -r requirements-dev.txt
pre-commit install
```

## Avertissement

EDMC-Triumvirate a été créé à partir de ressources et d'images d'Elite Dangerous, avec la permission de Frontier Developments plc, à des fins non commerciales. Il n'est pas approuvé par Frontier Developments et ne reflète pas ses opinions. Aucun employé de Frontier Developments n'a été impliqué dans la création de ce jeu.

EDMC-Triumvirate utilise des données provenant de [Canonn API V2](https://docs.canonn.tech), [ED Star Map (EDSM)](https://www.edsm.net/), [Elite BGS](https://elitebgs.app/), avec la permission de leurs propriétaires.

EDMC-Triumvirate basé sur [EDMC-Canonn](https://github.com/canonn-science/EDMC-Canonn), avec la permission des développeurs initiaux.

Tous les contenus sont protégés par le droit d'auteur ©️ 2016-2023 Close Encounters Corps, Triumvirate. KAZAK0V, AntonyVern, Osmium, Art-py. Tous droits réservés.

Logo - Антон Верницкий aka AntonyVern/Automatic system
