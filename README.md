# pfd-okdp-uns

Vocabulaire UNS de la plateforme PFD-OKDP, publié pour les identifiants persistants
`https://w3id.org/pfd-okdp/uns/`. Site : https://dibled.github.io/pfd-okdp-uns/

| Fichiers | Contenu | Identifiant |
|---|---|---|
| `uns_ontologie.{ttl,jsonld,rdf}`, `def.html` | ontologie et vocabulaire (OWL) | `https://w3id.org/pfd-okdp/uns/def` |
| `uns_referentiels.{ttl,jsonld,rdf}`, `ref.html` | référentiels SKOS, dont CPV 2008 | `https://w3id.org/pfd-okdp/uns/ref/` |
| `uns_decp_shacl.{ttl,jsonld,rdf}`, `shapes.html` | contrôles SHACL du cas DECP | `https://w3id.org/pfd-okdp/uns/shapes` |
| `versions/<version>/` | copie figée de chaque version publiée | `https://w3id.org/pfd-okdp/uns/def/<version>` |

Licence : Licence Ouverte 2.0 (Etalab) ; CPV sous CC BY 4.0. Voir [LICENSE.md](LICENSE.md).

## Publier une nouvelle version

1. Régénérer les 3 fichiers Turtle sur la plateforme (`app/nifi-opale/outils/generer_ontologie.sh` du kit,
   avec `--version` à jour dans `uns_ontologie.py`) et les copier à la racine de ce dépôt.
2. `pip install rdflib pylode==3.2.1`, puis `python -P outils/construire.py` : vérifie les métadonnées,
   écrit JSON-LD, RDF/XML, la documentation HTML et la copie `versions/<version>/`.
3. Ajouter la version dans `index.html`, valider et pousser.
