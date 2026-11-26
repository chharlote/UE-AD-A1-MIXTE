# UE-AD-A1-MIXTE — Application Microservices de Réservation de Cinéma

Projet d'architecture distribuée basé sur 4 microservices mixtes (GraphQL et REST) développés en Python (Flask), connectés à MongoDB et sécurisés par authentification JWT.

---

## Auteurs

- Titouan NICOLAS 
- Charlotte GERME

## Architecture du projet

| Service | Dossier | Port | URL locale | Rôle |
| :--- | :--- | :---: | :--- | :--- |
| **Movie** | `src/movie/` | `3001` | `http://localhost:3001/graphql` | Consultation et gestion du catalogue de films et des acteurs (**GraphQL**) |
| **Booking** | `src/booking/` | `3201` | `http://localhost:3201/graphql` | Consultation et gestion des réservations par utilisateur (**GraphQL**) |
| **Schedule** | `src/schedule/` | `3202` | `http://localhost:3202` | Gestion de la programmation des films par date (**REST**) |
| **User** | `src/user/` | `3203` | `http://localhost:3203` | Connexion et gestion des utilisateurs (**REST**) |
| **MongoDB** | `src/*/databases/` | `27017` | `mongodb://localhost:27017` | Stockage des films, horaires et réservations |
| **Mongo Express** | — | `8081` | `http://localhost:8081` | Interface web d'administration MongoDB (via Docker Compose) |
| **Utils** | `utils/jwt.py` |  |  | Création et vérification des tokens JWT |
| **Ressources** | `ressources/` | — | — | Collection de requêtes pour tester les API |



## Comment lancer le projet

### Option 1 : En local avec Python - Mode développement

1. Cloner le dépôt et installer les dépendances :
   ```bash
   git clone https://github.com/chharlote/UE-AD-A1-MIXTE.git
   cd UE-AD-A1-MIXTE
   python -m venv .venv
   source .venv/bin/activate        # Sur Windows : .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Démarrer les 4 microservices** (ouvrir **4 terminaux** à la racine du projet) :

   > Se placer dans le dossier `UE-AD-A1-MIXTE` et exécuter les commandes suivantes dans chaque terminal (nécessite une instance MongoDB locale active et une configuration adaptée des adresses des services) :

   ```bash
   # Terminal 1 — Movie Service (port 3001)
   python -m src.movie.movie

   # Terminal 2 — Booking Service (port 3201)
   python -m src.booking.booking

   # Terminal 3 — Schedule Service (port 3202)
   python -m src.schedule.schedule

   # Terminal 4 — User Service (port 3203)
   python -m src.user.user
   ```

### Option 2 : Avec Docker Compose - Mode production

1. Cloner le dépôt :
   ```bash
   git clone https://github.com/chharlote/UE-AD-A1-MIXTE.git
   ```

2. Lancer les conteneurs Docker Compose :
   ```bash
   docker compose up --build
   ```
   Les services sont exposés sur les ports `3001`, `3201`, `3202`, `3203`, `27017` (données conservées dans le volume `mongo_data`) et `8081`. Pour arrêter les conteneurs :
   ```bash
   docker compose down
   ```

---

## Liens rapides & Documentation interactive (GraphQL & Swagger)

Une fois les services démarrés, vous pouvez accéder directement aux interfaces et schémas suivants :

- **GraphQL Playground — Movie Service :** [http://localhost:3001/graphql](http://localhost:3001/graphql)
- **Schéma GraphQL Movie :** `src/movie/movie.graphql`
---
- **GraphQL Playground — Booking Service :** [http://localhost:3201/graphql](http://localhost:3201/graphql)
- **Schéma GraphQL Booking :** `src/booking/booking.graphql`
---
- **Accueil Schedule :** [http://localhost:3202/](http://localhost:3202/)
- **Swagger UI — Schedule Service :** [http://localhost:3202/docs](http://localhost:3202/docs)
---
* **Accueil User :** [http://localhost:3203/](http://localhost:3203/)
* **Swagger UI — User Service :** [http://localhost:3203/docs](http://localhost:3203/docs)
* ---
- **Interface Mongo Express :** [http://localhost:8081/](http://localhost:8081/)

---

## Authentification (JWT)

Les routes protégées exigent un jeton **JWT** valide pendant **1 heure**, à transmettre dans l'en-tête HTTP de chaque requête :

```http
Authorization: Bearer <VOTRE_TOKEN_JWT>
```

### Comptes pré-enregistrés pour tester (`src/user/databases/users.json`)

L'authentification via `POST http://localhost:3203/login` s'effectue sans mot de passe en envoyant uniquement l'`id` de l'utilisateur au format JSON (`{"id": "pam_beesly"}`) :

| Identifiant (`id`) | Nom | Rôle (`admin`) | Droits |
| :--- | :--- | :---: | :--- |
| `pam_beesly` | Pam Beesly | `true` | **Administrateur** (accès complet en lecture et écriture) |
| `chris_rivers` | Chris Rivers | `false` | **Utilisateur standard** (accès lecture et réservations personnelles) |

---

## Collection de requêtes API (Postman / Bruno / Insomnia...)

Une collection de requêtes prête à l'emploi est disponible dans le dossier `ressources/` (au format standard **Postman Collection v2.1**) pour tester un scénario de test des endpoints REST et GraphQL.

### Importation et utilisation

1. Importer le fichier `.json` situé dans `ressources/` dans votre client API :
   - **Postman** : `Import` → sélectionner le fichier
   - **Bruno** : `Import Collection` → `Postman Collection`
   - **Insomnia** : `Import` → `From File`
2. Exécuter d'abord la requête **`POST /login`** (service `User`) avec un identifiant valide pour obtenir un jeton JWT.
3. Renseigner ce jeton dans l'onglet **Authorization** (type **Bearer Token**) avant de lancer les autres requêtes.