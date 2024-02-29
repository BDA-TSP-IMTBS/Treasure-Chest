# Treasure Chest

<span>
<img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
</span>
<span>
<img alt="Flask" src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white">
</span>
<span>
<img alt="MySQL" src="https://img.shields.io/badge/MySQL-00000F?style=for-the-badge&logo=mysql&logoColor=white">
</span>
<span>
<img alt="MariaDB" src="https://img.shields.io/badge/MariaDB-003545?style=for-the-badge&logo=mariadb&logoColor=white">
</span>


Treasure Chest est une application web qui permet de récupérer une récompense en fin d'un jeu de chasse au trésor. L'utilisateur doit s'authentifier par son adresse mail TSP ou IMT-BS. La récompense donnée est déterminée par l'ordre dans lequel les personnes ont rentrés le code. Elle a été créée en 2024 par le pôle web du BDA du campus TSP/IMTBS.

## Installation

Pour déployer l'application, vous pouvez le faire dans une machine virtuelle (VM)

### Déploiement dans une VM

Il vous faut installer `docker compose` dans votre VM. Vous pouvez utiliser les commandes suivantes pour le faire ou suivre d'autres méthodes.

```bash
 curl -fsSL https://get.docker.com -o get-docker.sh
 sudo sh get-docker.sh
```

Ensuite, clonez le repository où vous le souhaitez dans la machine. Déplacez vous dans le dossier racine du projet puis lancez selon votre installation :

```bash
docker compose up
```

ou

```bash
docker-compose up
```

Si vous apportez des modifications à l'application, il faut rebuild l'application en la lancant : 
```bash
docker compose up --build
```

L'application est exposée sur le port **5000** de votre VM.

## Utiliser l'application

### Étape 1 : Question préliminaire

Une des particularité de l'application est qu'au moment de la création du compte, l'utilisateur se voit poser une question de culture générale empêchant la création du compte si elle n'est pas bien répondue.

Pour la modifier, cela ce fait dans le fichier `./app/question.json` :

```json
{
    "image": "image",
    "question": "votre-question",
    "answers": [
        "reponse-1",
        "reponse-2",
        "reponse-3"
    ]
  }
```
- `image`: image accompagnant la question
- `question` : question à afficher
- `answers` : liste de toutes les réponses possible <b>en minuscule</b>

### Étape 2 : Envoie de mails

Pour authentifier les élèves, l'application utilise un code à 6 chiffres envoyé par mail à l'adresse donnée. Il faut donc définir une adresse mail d'envoie. Ici, on utilise une adresse gmail.

Il faut <b>rajouter</b> au projet un fichier `./.env` dans lequel on défini des variables d'environnement:
```
SENDER_MAIL='votre-adresse-gmail'
APP_PASSWORD='mot-de-passe-application'
```

APP_PASSWORD est le mot de passe d'application qui permet à certaines application un accès pour se connecter aux outils de Google, sans utiliser votre vrai mot de passe.

### Étape 3 : Récupération des récompenses

Les récompenses sont définies par le fichiers `./app/tresures.json`

Dans cette chasse aux QR Code, un code correspond à un item. Cet item peut être n'importe quoi. Pour définir les différents items de votre chasse, il vous faut modifier à la main le fichier `./app/items.json`.

```json
{
  "final-enigme": "Enigme finale",
  "code": "1234",
  "treasures": [
    {
      "slug": "f6b3MghwUMdKEl6y",
      "places": [1],
      "treasure": "Code - 1",
      "description-1": "phrase-1",
      "description-2": "phrase-2"
    },
    {
      "slug": "NHrvtJFrS8CQW5CG",
      "places": [2],
      "treasure": "Code - 2",
      "description-1": "phrase-1",
      "description-2": "phrase-2"
    }
  ],
  "too-late": {
    "treasure": "Rien",
    "description-1": "phrase-1",
    "slug": "too-late"
  }
}
```
- `final-enigme` : énigme finale de la chasse au trésor
- `code` : code à trouver à la fin de la chasse au trésor
- `treasures` : liste de toutes les récompenses
```json
    ...
    {
      "slug": "f6b3MghwUMdKEl6y",
      "places": [1],
      "treasure": "Code - 1",
      "description-1": "phrase-1",
      "description-2": "phrase-2"
    },
    ...
```
- `slug` : morceau de l’URL d’une récompense généré aléatoirement.
- `places` : liste des places concernées par cette récompense. Ainsi, les personnes arrivées deuxième et troisième peuvent partager la même récompense.
- `treasure` : la récompense en question, un code à récupérer et utiliser auprès du BDA
- `description-1` et `description-2`: phrases de description de la récompense

Si toutes les récompenses ont été épuisées:

- `too-late` : défini ce qu'il se passe quand il ne reste plus de récompenses:
```json
  ...
  "too-late": {
    "treasure": "Rien",
    "description-1": "phrase-1",
    "slug": "too-late"
  }
```
- `slug` : morceau de l’URL pour la page
- `treasure` : phrase qui vient remplacer la récompense
- `description-1` : phrases de description


### Générer les slugs

Il est important que les URLs des pages de vos items soient complexes pour que personne ne puisse deviner sans avoir à trouver le code de la chasse au trésor.

Pour générer automatiquement les slugs de vos items, vous pouvez lancer le script python : `./utils/generateSlugs.py`.

```bash
python3 ./utils/generateSlugs.py
```

Un nouveau fichier `treasures.json` sera créé à la racine de l'application, qu'il faudra ensuite déplacer dans le dossier `./app`