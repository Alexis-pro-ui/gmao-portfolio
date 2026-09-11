"""
Tests UI de la GMAO — testent le parcours utilisateur réel via le navigateur.
"""
from playwright.sync_api import Page, expect
 
BASE_URL = "http://127.0.0.1:8000"
TEST_USERNAME = "testeur"
TEST_PASSWORD = "Test1234!"
 
 
def se_connecter(page: Page, username: str = TEST_USERNAME, password: str = TEST_PASSWORD):
    """Remplit et valide le formulaire de connexion."""
    page.goto(BASE_URL)
    page.locator("#login-username").fill(username)
    page.locator("#login-password").fill(password)
    page.get_by_role("button", name="Se connecter").click()
 
 
# --- Authentification ---
 
def test_connexion_reussie_affiche_lappli(page: Page):
    se_connecter(page)
    expect(page.get_by_role("heading", name="GMAO — Stock pièces de rechange")).to_be_visible()
 
 
def test_connexion_echouee_affiche_erreur(page: Page):
    se_connecter(page, password="mauvais_mot_de_passe")
    expect(page.locator("#login-error")).to_be_visible()
    expect(page.locator("#login-error")).to_contain_text("incorrect")
    # L'appli ne doit pas être accessible
    expect(page.locator("#app-content")).to_be_hidden()
 
 
def test_deconnexion_revient_a_lecran_de_login(page: Page):
    se_connecter(page)
    page.get_by_role("button", name="Déconnexion").click()
    expect(page.locator("#login-screen")).to_be_visible()
    expect(page.locator("#app-content")).to_be_hidden()
 
 
# --- Fonctionnalités (nécessitent d'être connecté) ---
 
def test_page_charge_correctement(page: Page):
    se_connecter(page)
    expect(page.get_by_role("heading", name="GMAO — Stock pièces de rechange")).to_be_visible()
 
 
def test_creer_piece_via_formulaire(page: Page, reference_unique):
    se_connecter(page)
 
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Capteur de proximité")
    page.locator("#np-fournisseur").fill("Sick")
    page.locator("#np-quantite").fill("20")
    page.locator("#np-seuil").fill("5")
    page.get_by_role("button", name="Créer la pièce").click()
 
    expect(page.get_by_text(reference_unique)).to_be_visible()
 
 
def test_creer_piece_reference_dupliquee_affiche_erreur(page: Page, reference_unique):
    se_connecter(page)
 
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Pièce originale")
    page.get_by_role("button", name="Créer la pièce").click()
    expect(page.get_by_text(reference_unique)).to_be_visible()
 
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Doublon")
    page.get_by_role("button", name="Créer la pièce").click()
 
    expect(page.locator("#err-reference")).to_be_visible()
    expect(page.locator("#err-reference")).to_contain_text("existe déjà")
 
 
def test_alerte_stock_bas_saffiche(page: Page, reference_unique):
    se_connecter(page)
 
    page.get_by_role("button", name="+ Nouvelle pièce").click()
    page.locator("#np-reference").fill(reference_unique)
    page.locator("#np-designation").fill("Pièce en rupture")
    page.locator("#np-quantite").fill("1")
    page.locator("#np-seuil").fill("5")
    page.get_by_role("button", name="Créer la pièce").click()
 
    expect(page.locator("#alerte-banner")).to_be_visible()
    ligne = page.get_by_role("row", name=reference_unique)
    expect(ligne.get_by_text("STOCK BAS")).to_be_visible()
 
 
def test_sortie_stock_insuffisant_affiche_erreur(page: Page, reference_unique):
    se_connecter(page)
 
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