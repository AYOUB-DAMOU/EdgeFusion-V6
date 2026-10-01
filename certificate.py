import os
from _paths import DATA_DIR

CERT_FILE = os.path.join(DATA_DIR, "client_cert.pem")
KEY_FILE  = os.path.join(DATA_DIR, "client_key.pem")

def check_certificate():
    """Retourne True si les fichiers certificat existent."""
    return os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE)

def generate_certificate(on_success=None, on_error=None):
    """
    Génère client_cert.pem + client_key.pem dans le dossier de l'app.
    - Si déjà existants → ne fait rien
    - on_success(msg) : callback si certificat généré
    - on_error(msg)   : callback si erreur
    """
    if check_certificate():
        print("[CERT] Certificat déjà existant")
        return

    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        import datetime

        # Génération clé privée RSA 2048
        key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Génération certificat auto-signé (valide 10 ans)
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "MA"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "ManaTechnology"),
            x509.NameAttribute(NameOID.COMMON_NAME, "EdgeFusion"),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=3650))
            .add_extension(
                x509.SubjectAlternativeName([
                    x509.UniformResourceIdentifier("urn:ManaTechnology:EdgeFusion"),
                ]),
                critical=False,
            )
            .sign(key, hashes.SHA256(), default_backend())
        )

        # Sauvegarde certificat
        with open(CERT_FILE, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        # Sauvegarde clé privée
        with open(KEY_FILE, "wb") as f:
            f.write(key.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.TraditionalOpenSSL,
                serialization.NoEncryption()
            ))

        print(f"[CERT] Certificat généré : {CERT_FILE}")
        if on_success:
            on_success(f"Certificat généré ✅\n\nFichier : client_cert.pem\nDossier : {DATA_DIR}")

    except ImportError:
        msg = "Package 'cryptography' manquant\npip install cryptography"
        print(f"[CERT] {msg}")
        if on_error:
            on_error(msg)
    except Exception as e:
        msg = f"Erreur génération certificat :\n{e}"
        print(f"[CERT] {msg}")
        if on_error:
            on_error(msg)
