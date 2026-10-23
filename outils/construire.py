"""Construit le site publié à partir des 3 fichiers Turtle produits par uns_ontologie.py (kit PFD-OKDP).

- vérifie la syntaxe et la présence des métadonnées de publication ;
- écrit les formats JSON-LD (.jsonld) et RDF/XML (.rdf) à côté de chaque .ttl ;
- écrit la documentation HTML : def.html (pyLODE), ref.html (référentiels SKOS), shapes.html (contrôles SHACL) ;
- copie l'ensemble sous versions/<version>/.

Usage, depuis la racine du dépôt : python -P outils/construire.py
Prérequis : pip install rdflib pylode==3.2.1
"""
import html
import shutil
import sys
from collections import Counter
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, SKOS, Namespace

SH = Namespace("http://www.w3.org/ns/shacl#")
BASE = "https://w3id.org/pfd-okdp/uns/"
RACINE = Path(__file__).resolve().parent.parent
FICHIERS = ("uns_ontologie.ttl", "uns_referentiels.ttl", "uns_decp_shacl.ttl")
STYLE = """<style>
:root { --fond: #fff; --texte: #1d1d1f; --trait: #d8d8dc; --doux: #f4f4f6; --lien: #0b57d0; }
@media (prefers-color-scheme: dark) { :root { --fond: #17171a; --texte: #ececf1; --trait: #3a3a40; --doux: #222227; --lien: #8ab4f8; } }
body { background: var(--fond); color: var(--texte); font-family: system-ui, sans-serif; line-height: 1.5;
       max-width: 72rem; margin: 2rem auto; padding: 0 1rem; }
a { color: var(--lien); } code { background: var(--doux); padding: 0 .25rem; }
table { border-collapse: collapse; width: 100%; font-size: .92rem; }
th, td { border-bottom: 1px solid var(--trait); padding: .3rem .5rem; text-align: left; vertical-align: top; }
th { background: var(--doux); position: sticky; top: 0; }
.niv1 { padding-left: 1rem; } .niv2 { padding-left: 2rem; } .niv3 { padding-left: 3rem; } .niv4 { padding-left: 4rem; }
</style>"""


def page(titre, corps):
    return (f'<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{html.escape(titre)}</title>\n'
            f"{STYLE}\n</head>\n<body>\n{corps}\n</body>\n</html>\n")


def e(x):
    return html.escape(str(x))


def libelle(g, s):
    v = g.value(s, SKOS.prefLabel) or g.value(s, URIRef("http://www.w3.org/2000/01/rdf-schema#label"))
    return str(v) if v is not None else str(s)


def verifier(graphes):
    ont = graphes["uns_ontologie.ttl"]
    o = URIRef(BASE + "def")
    manquants = [p for p in (DCTERMS.license, DCTERMS.creator, DCTERMS.publisher, DCTERMS.modified, OWL.versionInfo,
                             OWL.versionIRI) if ont.value(o, p) is None]
    if manquants:
        sys.exit("ERREUR : métadonnées absentes de l'ontologie (régénérer avec uns_ontologie.py à jour) : "
                 + ", ".join(str(p) for p in manquants))
    return str(ont.value(o, OWL.versionInfo))


def doc_ontologie(g):
    """HTML pyLODE, avec une ancre au nom local de chaque classe (pyLODE ancre les classes sur leur libellé)."""
    from pylode import OntPub
    page_html = OntPub(str(RACINE / "uns_ontologie.ttl")).make_html()
    for c in g.subjects(RDF.type, OWL.Class):
        local, lib = str(c).split("#")[-1], libelle(g, c)
        if local != lib:
            page_html = page_html.replace(f'class="property entity" id="{lib}">',
                                          f'class="property entity" id="{lib}"><span id="{local}"></span>', 1)
    return page_html


def doc_referentiels(g, version):
    schemas = sorted(g.subjects(RDF.type, SKOS.ConceptScheme), key=str)
    nb = Counter(g.value(c, SKOS.inScheme) for c in g.subjects(RDF.type, SKOS.Concept))
    lignes = []
    for sc in schemas:
        ident = str(sc)[len(BASE + "ref/"):]
        lic = g.value(sc, DCTERMS.license)
        lignes.append(f'<tr id="{e(ident)}"><td><code>{e(ident)}</code></td><td>{e(libelle(g, sc))}</td>'
                      f'<td>{e(g.value(sc, DCTERMS.description) or "")}</td><td>{nb.get(sc, 0)}</td>'
                      f'<td>{f"<a href={chr(34)}{e(lic)}{chr(34)}>{e(lic)}</a>" if lic else ""}</td></tr>')
    cpv_sc = URIRef(BASE + "ref/cpv")
    codes = sorted((c for c in g.subjects(SKOS.inScheme, cpv_sc)), key=lambda c: str(g.value(c, SKOS.notation)))
    cpv = []
    for c in codes:
        code = str(g.value(c, SKOS.notation))
        prof = 0
        p = g.value(c, SKOS.broader)
        while p is not None and prof < 4:
            prof, p = prof + 1, g.value(p, SKOS.broader)
        ue = g.value(c, SKOS.exactMatch)
        cpv.append(f'<tr id="cpv-{e(code)}"><td><code>{e(code)}</code></td><td class="niv{prof}">{e(libelle(g, c))}</td>'
                   f'<td><a href="{e(ue)}">{e(ue)}</a></td></tr>')
    corps = (f"<h1>Référentiels SKOS du vocabulaire UNS</h1>\n<p>Version {e(version)}. Espace d'URI "
             f"<code>{BASE}ref/</code>. Formats : <a href=\"uns_referentiels.ttl\">Turtle</a>, "
             f"<a href=\"uns_referentiels.jsonld\">JSON-LD</a>, <a href=\"uns_referentiels.rdf\">RDF/XML</a>. "
             f"<a href=\"./\">Accueil</a>.</p>\n"
             f"<h2>Schémas de concepts ({len(schemas)})</h2>\n<table><thead><tr><th>Identifiant</th><th>Libellé</th>"
             f"<th>Statut</th><th>Concepts</th><th>Licence</th></tr></thead><tbody>\n" + "\n".join(lignes)
             + f"\n</tbody></table>\n<h2 id=\"cpv\">Nomenclature CPV 2008 ({len(codes)} codes)</h2>\n"
             "<p>Source : Office des publications de l'Union européenne, licence CC BY 4.0. Chaque code est relié "
             "à son URI officielle (<code>skos:exactMatch</code>).</p>\n<table><thead><tr><th>Code</th><th>Libellé</th>"
             "<th>URI européenne</th></tr></thead><tbody>\n" + "\n".join(cpv) + "\n</tbody></table>")
    return page("Référentiels UNS PFD-OKDP", corps)


def doc_formes(g, version):
    blocs = []
    for forme in sorted(g.subjects(RDF.type, SH.NodeShape), key=str):
        lignes = []
        for pr in g.objects(forme, SH.property):
            chemin = g.value(pr, SH.path)
            regles = "; ".join(f"{str(p).split('#')[-1]} = {o}" for p, o in g.predicate_objects(pr)
                               if p not in (SH.path, SH.message))
            lignes.append(f"<tr><td><code>{e(str(chemin).split('#')[-1])}</code></td><td>{e(regles)}</td>"
                          f"<td>{e(g.value(pr, SH.message) or '')}</td></tr>")
        for sq in g.objects(forme, SH.sparql):
            lignes.append(f"<tr><td>requête SPARQL</td><td><pre>{e(g.value(sq, SH.select))}</pre></td>"
                          f"<td>{e(g.value(sq, SH.message) or '')}</td></tr>")
        cible = g.value(forme, SH.targetClass)
        blocs.append(f"<h2>{e(str(forme).split('#')[-1])}</h2>\n<p>Classe ciblée : <code>{e(cible)}</code></p>\n"
                     "<table><thead><tr><th>Propriété</th><th>Contrainte</th><th>Message</th></tr></thead><tbody>\n"
                     + "\n".join(lignes) + "\n</tbody></table>")
    corps = (f"<h1>Contrôles SHACL du vocabulaire UNS (cas DECP)</h1>\n<p>Version {e(version)}. Formats : "
             "<a href=\"uns_decp_shacl.ttl\">Turtle</a>, <a href=\"uns_decp_shacl.jsonld\">JSON-LD</a>, "
             "<a href=\"uns_decp_shacl.rdf\">RDF/XML</a>. <a href=\"./\">Accueil</a>.</p>\n" + "\n".join(blocs))
    return page("Contrôles SHACL UNS PFD-OKDP", corps)


def main():
    graphes = {}
    for f in FICHIERS:
        graphes[f] = Graph().parse(RACINE / f, format="turtle")
        print(f"{f} : {len(graphes[f])} triplets")
    version = verifier(graphes)
    for f, g in graphes.items():
        racine = RACINE / f[:-4]
        g.serialize(f"{racine}.jsonld", format="json-ld", encoding="utf-8", auto_compact=True)
        g.serialize(f"{racine}.rdf", format="xml", encoding="utf-8")
    (RACINE / "def.html").write_text(doc_ontologie(graphes["uns_ontologie.ttl"]), encoding="utf-8")
    (RACINE / "ref.html").write_text(doc_referentiels(graphes["uns_referentiels.ttl"], version), encoding="utf-8")
    (RACINE / "shapes.html").write_text(doc_formes(graphes["uns_decp_shacl.ttl"], version), encoding="utf-8")
    cible = RACINE / "versions" / version
    cible.mkdir(parents=True, exist_ok=True)
    for f in [*FICHIERS] + [x[:-4] + ext for x in FICHIERS for ext in (".jsonld", ".rdf")] + ["def.html", "ref.html",
                                                                                              "shapes.html"]:
        shutil.copy2(RACINE / f, cible / f)
    print(f"version {version} : site construit, copie sous versions/{version}/")


if __name__ == "__main__":
    main()
