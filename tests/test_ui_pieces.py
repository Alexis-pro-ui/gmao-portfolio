"""
Tests UI de la GMAO — testent le parcours utilisateur réel via le navigateur.
"""
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:8000"


def test_page_charge_correctement(page: Page):
    page.goto(BASE_URL)
    expect(page.get_by_role("heading", name="GMAO — Stock pièces de rechange")).to_be_visible()


def test_creer_piece_via_formulaire(page: Page, reference_unique):
    page.goto(BASE_URL)

    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Capteur de proximité")
    page.locator("#np-fournisseur").fill("Sick")
    page.locator("#np-quantite").fill("20")
    page.locator("#np-seuil").fill("5")
    page.get_by_role("button", name="Créer la pièce").click()

    # La pièce doit apparaître dans le tableau
    expect(page.get_by_text(reference_unique)).to_be_visible()


def test_creer_piece_reference_dupliquee_affiche_erreur(page: Page, reference_unique):
    page.goto(BASE_URL)

    # Première création : doit réussir
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Pièce originale")
    page.get_by_role("button", name="Créer la pièce").click()
    expect(page.get_by_text(reference_unique)).to_be_visible()

    # Deuxième création avec la même référence : doit échouer visuellement
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Doublon")
    page.get_by_role("button", name="Créer la pièce").click()

    expect(page.locator("#err-reference")).to_be_visible()
    expect(page.locator("#err-reference")).to_contain_text("existe déjà")


def test_alerte_stock_bas_saffiche(page: Page, reference_unique):
    page.goto(BASE_URL)

    # Crée une pièce avec un stock déjà sous son seuil d'alerte
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Pièce en rupture")
    page.locator("#np-quantite").fill("1")
    page.locator("#np-seuil").fill("5")
    page.get_by_role("button", name="Créer la pièce").click()
    # Prendre la ligne qu'on vient de créer
    ligne = page.get_by_role("row", name=reference_unique)
    expect(ligne.get_by_text("STOCK BAS")).to_be_visible()
    expect(page.locator("#alerte-banner")).to_be_visible()


def test_sortie_stock_insuffisant_affiche_erreur(page: Page, reference_unique):
    page.goto(BASE_URL)

    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Petit stock")
    page.locator("#np-quantite").fill("3")
    page.get_by_role("button", name="Créer la pièce").click()

    page.get_by_role("row", name=reference_unique).get_by_role("button", name="Mouvement").click()
    page.locator("#mv-type").select_option("sortie")
    page.locator("#mv-quantite").fill("50")
    page.get_by_role("button", name="Valider").click()

    expect(page.locator("#err-mouvement")).to_be_visible()
    expect(page.locator("#err-mouvement")).to_contain_text("insuffisant")
