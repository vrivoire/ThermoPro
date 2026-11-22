import email
import imaplib
from email.header import decode_header

# From: =?iso-8859-1?q?Hydro-Qu=E9bec?=
# 	<hydro-quebec@communications.hydro.qc.ca>
# Subject: Votre code de
# Body:
#
#
# ( http://www.hydroquebec.com/residentiel?utm_campaign=avis-connexion&utm_source=tous-sys-fr&utm_medium=email&utm_content=logotype&utm_creative_format=autre&utm_marketing_tactic=notoriete-produit )
#
# Bonjour,
#
# Pour confirmer votre identité et poursuivre votre connexion, veuillez utiliser le code de vérification ci-dessous.
#
# *Code de vérification : 808740*
#
# Ce code est valide pour une durée limitée. Ne le communiquez à personne. Si vous n’êtes pas à l’origine de cette demande, veuillez ne pas tenir compte de ce courriel.
#
# Meilleures salutations,
# Les Services à la clientèle
#
# Veuillez ne pas répondre au présent courriel. Puisqu'il a été généré automatiquement, nous ne pouvons donner suite à vos questions ou commentaires. Pour joindre un représentant des Services à la clientèle, visitez la page Nous joindre ( http://www.hydroquebec.com/nous-joindre?utm_campaign=avis-connexion&utm_source=tous-sys-fr&utm_medium=email&utm_content=nous-joindre&utm_creative_format=cta&utm_marketing_tactic=notoriete-produit ).
#
# Hydro-Québec ne vous demandera jamais des renseignements personnels par courriel.
# Consultez notre Politique en matière de confidentialité ( http://www.hydroquebec.com/conditions-confidentialite.html?utm_campaign=avis-connexion&utm_source=tous-sys-fr&utm_medium=email&utm_content=politique-en-matiere-de-confidentialite&utm_creative_format=cta&utm_marketing_tactic=notoriete-produit ).
#
# *Avis de confidentialité* – Avertissement relatif à la Loi sur l'accès aux documents des organismes publics et sur la protection des renseignements personnels. L'information transmise avec ce courrier électronique est de nature privilégiée et confidentielle. Elle est destinée à l'usage exclusif de la personne visée. Si vous n'êtes pas cette personne, nous vous saurions gré d'en aviser l'expéditeur et de détruire le contenu sans le communiquer ni le reproduire.
#
# @hydroquebec.com #808740


EMAIL = "rivoire.vincent@gmail.com"
APP_PASSWORD = "nmhz fpyl zkkh bvwz"

# Connect to Gmail's IMAP server
imap = imaplib.IMAP4_SSL("imap.gmail.com")
imap.login(EMAIL, APP_PASSWORD)
imap.select("INBOX")

# Search for all unread emails
status, messages = imap.search(None, "UNSEEN")
email_ids = messages[0].split()

for e_id in email_ids:
    # Fetch the email by ID (Use '(BODY.PEEK[])' instead of '(RFC822)' to keep it unread)
    _, msg_data = imap.fetch(e_id, "(BODY.PEEK[])")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])

            # Decode subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            sender = msg.get("From")
            if 'hydro-quebec@communications.hydro.qc.ca' in sender:
                print(f"From: {sender}\nSubject: {subject}")

                # Extract plain text body
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(
                                errors="ignore"
                            )
                            parts = body.split("*")
                            if len(parts) > 2:
                                result = parts[1]
                                result = result.replace("Code de vérification : ", "")
                                print(result)
                            break
                else:
                    body = msg.get_payload(decode=True).decode(errors="ignore")
                    print(f"Body:\n{body}\n" + "-" * 40)

imap.close()
imap.logout()
