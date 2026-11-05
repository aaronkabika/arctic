// ============================================================
// ARCTIC — SCRIPT PRINCIPAL
// Connexion, inscription, recherche et gestion des œuvres
// ============================================================

document.addEventListener("DOMContentLoaded", function () {
    // --------------------------------------------------------
    // OUTILS COMMUNS
    // --------------------------------------------------------

    const formulaireAjoutOeuvre = document.getElementById("form-ajout-oeuvre");
    const formulaireModificationOeuvre = document.getElementById("form-modification-oeuvre");
    const formulaireOeuvre = formulaireAjoutOeuvre || formulaireModificationOeuvre;
    const selectTypeOeuvre = document.getElementById("type-oeuvre");
    const estPageAjoutOeuvre = Boolean(formulaireAjoutOeuvre);
    const estPageModificationOeuvre = Boolean(formulaireModificationOeuvre);

    function afficherMessage(element, texte, type) {
        if (!element) return;
        element.textContent = texte || "";
        if (type) {
            element.dataset.typeMessage = type;
        } else {
            delete element.dataset.typeMessage;
        }
    }

    function extensionDuFichier(nom) {
        const position = nom.lastIndexOf(".");
        return position >= 0 ? nom.slice(position + 1).toLowerCase() : "";
    }

    function obtenirFichiersNonVides(champ) {
        if (!champ || !champ.files) return [];
        return Array.from(champ.files).filter(function (fichier) {
            return fichier && fichier.name && fichier.name.trim() !== "";
        });
    }

    function dateLocaleISO(date) {
        const annee = date.getFullYear();
        const mois = String(date.getMonth() + 1).padStart(2, "0");
        const jour = String(date.getDate()).padStart(2, "0");
        return `${annee}-${mois}-${jour}`;
    }

    function configurerPreventionDoubleEnvoi(formulaire, texteBouton) {
        if (!formulaire) return;

        let envoiEnCours = false;

        formulaire.addEventListener("submit", function (event) {
            // Un autre validateur a déjà bloqué l'envoi.
            if (event.defaultPrevented || !formulaire.checkValidity()) return;

            if (envoiEnCours) {
                event.preventDefault();
                return;
            }

            envoiEnCours = true;
            const bouton = formulaire.querySelector('button[type="submit"]');
            if (bouton) {
                bouton.disabled = true;
                bouton.textContent = texteBouton;
            }
        });
    }

    // --------------------------------------------------------
    // RECHERCHE D'ARTISTE
    // --------------------------------------------------------

    const rechercheArtiste = document.getElementById("recherche-artiste");

    if (rechercheArtiste) {
        rechercheArtiste.addEventListener("input", function () {
            // La recherche est actuellement enregistrée dans la console.
            // Pour filtrer réellement les artistes, il faudra relier ce champ
            // aux résultats affichés ou à une route de recherche Flask.
            console.log(rechercheArtiste.value.trim());
        });
    }

    // --------------------------------------------------------
    // CONNEXION
    // --------------------------------------------------------

    const formulaireConnexion = document.getElementById("form-connexion");
    const messageConnexion = document.getElementById("message-connexion");

    if (formulaireConnexion) {
        formulaireConnexion.addEventListener("submit", function (event) {
            const email = formulaireConnexion.querySelector('[name="email"], #email');
            const motDePasse = formulaireConnexion.querySelector(
                '[name="password"], [name="mot_de_passe"], #password'
            );

            if (!email || !motDePasse) return;

            if (!email.value.trim() || !motDePasse.value) {
                event.preventDefault();
                afficherMessage(messageConnexion, "Veuillez remplir tous les champs.", "erreur");
            }
        });

        formulaireConnexion.addEventListener("input", function () {
            afficherMessage(messageConnexion, "");
        });
    }

    const champMotDePasseConnexion = document.getElementById("password");
    const boutonVisibiliteConnexion = document.getElementById("basculer-mot-de-passe");

    if (champMotDePasseConnexion && boutonVisibiliteConnexion) {
        boutonVisibiliteConnexion.addEventListener("click", function () {
            const doitAfficher = champMotDePasseConnexion.type === "password";
            champMotDePasseConnexion.type = doitAfficher ? "text" : "password";
            boutonVisibiliteConnexion.textContent = doitAfficher ? "Masquer" : "Afficher";
            boutonVisibiliteConnexion.setAttribute("aria-pressed", String(doitAfficher));
        });
    }

    // --------------------------------------------------------
    // INSCRIPTION
    // --------------------------------------------------------

    const formulaireInscription = document.getElementById("form-inscription");
    const messageInscription = document.getElementById("message-inscription");

    const champNomInscription = document.getElementById("nom");
    const champEmailInscription = document.getElementById("email");
    const champMotDePasseInscription = document.getElementById("password");
    const champConfirmationInscription = document.getElementById("confirmation_password");
    const champTelephoneInscription = document.getElementById("telephone");
    const champDateNaissance = document.getElementById("date-naissance");

    const aideNom = document.getElementById("aide-nom");
    const aideEmail = document.getElementById("aide-email");
    const aideMotDePasse = document.getElementById("aide-mot-de-passe");
    const aideConfirmation = document.getElementById("aide-confirmation-mot-de-passe");
    const aideTelephone = document.getElementById("aide-telephone");
    const aideDateNaissance = document.getElementById("aide-date-naissance");

    function verifierNomInscription() {
        if (!champNomInscription) return true;
        const valide = champNomInscription.value.trim() !== "";
        champNomInscription.setCustomValidity(valide ? "" : "Veuillez saisir votre nom.");
        if (aideNom) {
            aideNom.textContent = valide
                ? "Le nom est renseigné."
                : "Le nom ne peut pas être vide.";
        }
        return valide;
    }

    function verifierEmailInscription() {
        if (!champEmailInscription) return true;
        const email = champEmailInscription.value.trim();
        const valide = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        champEmailInscription.setCustomValidity(
            email === "" || valide ? "" : "Saisis une adresse e-mail valide."
        );
        if (aideEmail) {
            aideEmail.textContent = email === ""
                ? "Saisis ton adresse e-mail."
                : valide
                    ? "Le format de l'adresse e-mail semble correct."
                    : "Le format de l'adresse e-mail semble incorrect.";
        }
        return email !== "" && valide;
    }

    function verifierMotDePasseInscription() {
        if (!champMotDePasseInscription) return true;
        const valeur = champMotDePasseInscription.value;
        const reglesManquantes = [];

        if (valeur.length < 8 || valeur.length > 20) reglesManquantes.push("8 à 20 caractères");
        if (!/[A-Z]/.test(valeur)) reglesManquantes.push("une majuscule");
        if (!/\d/.test(valeur)) reglesManquantes.push("un chiffre");
        if (!/[!@#$%^&*]/.test(valeur)) {
            reglesManquantes.push("un caractère spécial parmi !@#$%^&*");
        }

        const valide = reglesManquantes.length === 0;
        champMotDePasseInscription.setCustomValidity(
            valeur === "" || valide ? "" : "Le mot de passe ne respecte pas toutes les règles."
        );

        if (aideMotDePasse) {
            aideMotDePasse.textContent = valeur === ""
                ? "Utilise 8 à 20 caractères, une majuscule, un chiffre et un caractère spécial."
                : valide
                    ? "Le mot de passe respecte les règles."
                    : "Il manque : " + reglesManquantes.join(", ") + ".";
        }
        return valeur !== "" && valide;
    }

    function verifierConfirmationInscription() {
        if (!champMotDePasseInscription || !champConfirmationInscription) return true;
        const motDePasse = champMotDePasseInscription.value;
        const confirmation = champConfirmationInscription.value;
        const valide = confirmation !== "" && motDePasse === confirmation;

        champConfirmationInscription.setCustomValidity(
            confirmation === "" || valide ? "" : "Les mots de passe ne correspondent pas."
        );

        if (aideConfirmation) {
            aideConfirmation.textContent = confirmation === ""
                ? (motDePasse !== "" ? "Saisis à nouveau ton mot de passe." : "")
                : valide
                    ? "Les mots de passe correspondent."
                    : "Les mots de passe ne correspondent pas.";
        }
        return valide;
    }

    function verifierTelephoneInscription() {
        if (!champTelephoneInscription) return true;
        const telephone = champTelephoneInscription.value.trim();
        const valide = /^\d{9}$/.test(telephone);

        champTelephoneInscription.setCustomValidity(
            telephone === "" || valide ? "" : "Le numéro doit contenir exactement 9 chiffres."
        );

        if (aideTelephone) {
            aideTelephone.textContent = telephone === ""
                ? "Saisis 9 chiffres après l'indicatif +243."
                : valide
                    ? "Le format du numéro est correct."
                    : "Le numéro doit contenir exactement 9 chiffres.";
        }
        return telephone !== "" && valide;
    }

    function verifierDateNaissance() {
        if (!champDateNaissance) return true;

        const maintenant = new Date();
        const dateLimite = new Date(
            maintenant.getFullYear() - 18,
            maintenant.getMonth(),
            maintenant.getDate()
        );
        const maxDate = dateLocaleISO(dateLimite);
        champDateNaissance.max = maxDate;

        const valeur = champDateNaissance.value;
        const valide = valeur !== "" && valeur <= maxDate;

        champDateNaissance.setCustomValidity(
            valeur === "" || valide ? "" : "Vous devez avoir au moins 18 ans."
        );

        if (aideDateNaissance) {
            aideDateNaissance.textContent = valeur === ""
                ? "Choisis ta date de naissance."
                : valide
                    ? "La date de naissance est valide."
                    : "Vous devez avoir au moins 18 ans pour vous inscrire.";
        }
        return valide;
    }

    if (champNomInscription) {
        champNomInscription.addEventListener("input", verifierNomInscription);
    }
    if (champEmailInscription) {
        champEmailInscription.addEventListener("input", verifierEmailInscription);
    }
    if (champMotDePasseInscription) {
        champMotDePasseInscription.addEventListener("input", function () {
            verifierMotDePasseInscription();
            verifierConfirmationInscription();
        });
    }
    if (champConfirmationInscription) {
        champConfirmationInscription.addEventListener("input", verifierConfirmationInscription);
    }
    if (champTelephoneInscription) {
        champTelephoneInscription.addEventListener("input", verifierTelephoneInscription);
    }
    if (champDateNaissance) {
        champDateNaissance.addEventListener("input", verifierDateNaissance);
        champDateNaissance.addEventListener("change", verifierDateNaissance);
        verifierDateNaissance();
    }

    if (formulaireInscription) {
        formulaireInscription.addEventListener("submit", function (event) {
            const controles = [
                verifierNomInscription(),
                verifierEmailInscription(),
                verifierMotDePasseInscription(),
                verifierConfirmationInscription(),
                verifierTelephoneInscription(),
                verifierDateNaissance()
            ];

            if (!controles.every(Boolean)) {
                event.preventDefault();
                afficherMessage(
                    messageInscription,
                    "Vérifie les champs signalés avant de créer ton compte.",
                    "erreur"
                );
            } else {
                afficherMessage(messageInscription, "");
            }
        });

        formulaireInscription.addEventListener("input", function () {
            afficherMessage(messageInscription, "");
        });
    }

    function configurerVisibilite(champ, bouton) {
        if (!champ || !bouton) return;

        bouton.addEventListener("click", function () {
            const doitAfficher = champ.type === "password";
            champ.type = doitAfficher ? "text" : "password";
            bouton.textContent = doitAfficher ? "Masquer" : "Afficher";
            bouton.setAttribute("aria-pressed", String(doitAfficher));
        });
    }

    configurerVisibilite(
        champMotDePasseInscription,
        document.getElementById("basculer-password-inscription")
    );
    configurerVisibilite(
        champConfirmationInscription,
        document.getElementById("basculer-confirmation-inscription")
    );

    // --------------------------------------------------------
    // CONFIGURATION DES FICHIERS D'ŒUVRE
    // --------------------------------------------------------

    const configurationFichiers = {
        musique: {
            idChamp: "fichier-musique",
            idApercu: "apercu-musique",
            idErreur: "erreur-format-musique",
            extensions: ["mp3", "wav", "ogg", "m4a"],
            typeFichier: "audio",
            tailleMaxMo: 20,
            maximum: 1
        },
        peinture: {
            idChamp: "images-oeuvre",
            idApercu: "apercu-images-oeuvre",
            idErreur: "erreur-images-oeuvre",
            extensions: ["jpg", "jpeg", "png", "webp"],
            typeFichier: "image",
            tailleMaxMo: 7,
            maximum: 3
        },
        litterature: {
            idChamp: "fichier-litterature",
            idApercu: "apercu-litterature",
            idErreur: "erreur-format-litterature",
            extensions: ["pdf", "doc", "docx", "txt"],
            typeFichier: "document",
            tailleMaxMo: 10,
            maximum: 1
        },
        sculpture: {
            idChamp: "images-sculpture",
            idApercu: "apercu-images-sculpture",
            idErreur: "erreur-images-sculpture",
            extensions: ["jpg", "jpeg", "png", "webp"],
            typeFichier: "image",
            tailleMaxMo: 7,
            maximum: 3
        }
    };

    function afficherErreurFichier(configuration, texte) {
        const champ = document.getElementById(configuration.idChamp);
        const erreur = document.getElementById(configuration.idErreur);
        if (erreur) erreur.textContent = texte || "";
        if (champ) champ.setCustomValidity(texte || "");
    }

    function verifierFichiersPourType(configuration, fichiers) {
        if (fichiers.length > configuration.maximum) {
            return configuration.typeFichier === "image"
                ? "Sélectionne au maximum 3 images."
                : "Un seul fichier peut être sélectionné.";
        }

        for (const fichier of fichiers) {
            const extension = extensionDuFichier(fichier.name);
            if (!configuration.extensions.includes(extension)) {
                return `Format refusé : ${fichier.name}. Formats autorisés : ${configuration.extensions.join(", ")}.`;
            }
            if (fichier.size > configuration.tailleMaxMo * 1024 * 1024) {
                return `${fichier.name} dépasse la limite de ${configuration.tailleMaxMo} Mo.`;
            }
        }
        return "";
    }

    function configurerApercuFichiers(configuration) {
        const champ = document.getElementById(configuration.idChamp);
        const zoneApercu = document.getElementById(configuration.idApercu);
        if (!champ || !zoneApercu) return;

        let urlsTemporaires = [];

        champ.addEventListener("change", function () {
            urlsTemporaires.forEach(function (url) {
                URL.revokeObjectURL(url);
            });
            urlsTemporaires = [];
            zoneApercu.replaceChildren();

            const fichiers = obtenirFichiersNonVides(champ);
            if (fichiers.length === 0) {
                zoneApercu.textContent = estPageModificationOeuvre
                    ? "Aucun nouveau fichier sélectionné : le contenu actuel sera conservé."
                    : "Aucun fichier sélectionné.";
                return;
            }

            const titre = document.createElement("p");
            titre.textContent = fichiers.length === 1
                ? "1 fichier sélectionné :"
                : `${fichiers.length} fichiers sélectionnés :`;
            zoneApercu.appendChild(titre);

            fichiers.forEach(function (fichier) {
                const bloc = document.createElement("div");
                bloc.className = "apercu-fichier";

                const nom = document.createElement("p");
                nom.textContent = `${fichier.name} (${(fichier.size / 1024 / 1024).toFixed(2)} Mo)`;
                bloc.appendChild(nom);

                if (configuration.typeFichier === "image" && fichier.type.startsWith("image/")) {
                    const url = URL.createObjectURL(fichier);
                    urlsTemporaires.push(url);

                    const image = document.createElement("img");
                    image.src = url;
                    image.alt = `Aperçu de ${fichier.name}`;
                    image.style.maxWidth = "180px";
                    image.style.maxHeight = "180px";
                    image.style.objectFit = "contain";
                    bloc.appendChild(image);
                } else if (configuration.typeFichier === "audio" && fichier.type.startsWith("audio/")) {
                    const url = URL.createObjectURL(fichier);
                    urlsTemporaires.push(url);

                    const lecteur = document.createElement("audio");
                    lecteur.controls = true;
                    lecteur.src = url;
                    lecteur.style.display = "block";
                    lecteur.style.maxWidth = "100%";
                    bloc.appendChild(lecteur);
                }
                // Pour un document, le nom et la taille sont indiqués sans tenter
                // de l'ouvrir dans le navigateur.
                zoneApercu.appendChild(bloc);
            });
        });
    }

    function configurerValidationFichier(type, configuration) {
        const champ = document.getElementById(configuration.idChamp);
        const erreur = document.getElementById(configuration.idErreur);
        if (!champ) return;

        function verifierFichier() {
            if (erreur) erreur.textContent = "";
            champ.setCustomValidity("");

            // Sur la page de modification, un nouveau fichier est facultatif.
            const fichiers = obtenirFichiersNonVides(champ);
            if (fichiers.length === 0) return;

            const probleme = verifierFichiersPourType(configuration, fichiers);
            if (probleme) {
                afficherErreurFichier(configuration, probleme);
                return;
            }

            if (erreur) {
                erreur.textContent = configuration.typeFichier === "image"
                    ? `✓ ${fichiers.length} image(s) au format accepté.`
                    : "✓ Format et taille du fichier acceptés.";
            }
            champ.setCustomValidity("");
        }

        champ.addEventListener("change", verifierFichier);
        verifierFichier();
    }

    Object.entries(configurationFichiers).forEach(function ([type, configuration]) {
        configurerApercuFichiers(configuration);
        configurerValidationFichier(type, configuration);
    });

    // --------------------------------------------------------
    // CONTENU DYNAMIQUE SELON LE TYPE D'ART
    // --------------------------------------------------------

    if (selectTypeOeuvre) {
        const sectionsTypeArt = {
            musique: document.getElementById("contenu-musique"),
            peinture: document.getElementById("contenu-image"),
            litterature: document.getElementById("contenu-litterature"),
            sculpture: document.getElementById("contenu-sculpture")
        };

        const messageTypeAjout = document.getElementById("message-oeuvre");
        const messageModification = document.getElementById("message-modification-oeuvre");

        function actualiserContenuTypeArt() {
            const typeSelectionne = selectTypeOeuvre.value;

            Object.entries(sectionsTypeArt).forEach(function ([type, section]) {
                if (!section) return;
                const sectionActive = type === typeSelectionne;
                section.style.display = sectionActive ? "" : "none";

                const champsFichiers = section.querySelectorAll('input[type="file"]');
                champsFichiers.forEach(function (champ) {
                    champ.required = estPageAjoutOeuvre && sectionActive;
                    if (!sectionActive) {
                        // Un message de validation d'une section cachée ne doit pas
                        // bloquer l'envoi lorsqu'un autre type est sélectionné.
                        champ.setCustomValidity("");
                        const config = Object.values(configurationFichiers).find(
                            function (item) { return item.idChamp === champ.id; }
                        );
                        const erreur = config
                            ? document.getElementById(config.idErreur)
                            : null;
                        if (erreur) erreur.textContent = "";
                    }
                });
            });

            const message = estPageModificationOeuvre
                ? messageModification
                : messageTypeAjout;
            if (message) afficherMessage(message, "");
        }

        selectTypeOeuvre.addEventListener("change", actualiserContenuTypeArt);
        actualiserContenuTypeArt();
    }

    // --------------------------------------------------------
    // VALIDATION À L'ENVOI : AJOUT D'UNE ŒUVRE
    // --------------------------------------------------------

    if (formulaireAjoutOeuvre) {
        formulaireAjoutOeuvre.addEventListener("submit", function (event) {
            const message = document.getElementById("message-oeuvre");
            const type = selectTypeOeuvre ? selectTypeOeuvre.value : "";
            const configuration = configurationFichiers[type];
            const champ = configuration
                ? document.getElementById(configuration.idChamp)
                : null;

            if (!configuration || !champ) {
                event.preventDefault();
                afficherMessage(message, "Veuillez choisir un type d'art valide.", "erreur");
                return;
            }

            const fichiers = obtenirFichiersNonVides(champ);
            if (fichiers.length === 0) {
                event.preventDefault();
                afficherMessage(message, "Sélectionne le contenu demandé pour cette œuvre.", "erreur");
                champ.focus();
                return;
            }

            const probleme = verifierFichiersPourType(configuration, fichiers);
            if (probleme) {
                event.preventDefault();
                afficherErreurFichier(configuration, probleme);
                afficherMessage(message, probleme, "erreur");
                champ.focus();
                return;
            }

            afficherMessage(message, "");
        });
    }

    // --------------------------------------------------------
    // VALIDATION À L'ENVOI : MODIFICATION D'UNE ŒUVRE
    // --------------------------------------------------------

    if (formulaireModificationOeuvre) {
        formulaireModificationOeuvre.addEventListener("submit", function (event) {
            const message = document.getElementById("message-modification-oeuvre");
            const titre = document.getElementById("titre-oeuvre");
            const dateCreation = document.getElementById("date-creation");
            const prix = document.getElementById("prix-oeuvre");
            const type = selectTypeOeuvre ? selectTypeOeuvre.value : "";
            const configuration = configurationFichiers[type];

            if (titre && !titre.value.trim()) {
                event.preventDefault();
                afficherMessage(message, "Le titre de l'œuvre est obligatoire.", "erreur");
                titre.focus();
                return;
            }

            if (!dateCreation || !dateCreation.value) {
                event.preventDefault();
                afficherMessage(message, "La date de création est obligatoire.", "erreur");
                if (dateCreation) dateCreation.focus();
                return;
            }

            const aujourdHui = dateLocaleISO(new Date());
            if (dateCreation.value > aujourdHui) {
                event.preventDefault();
                afficherMessage(message, "La date de création ne peut pas être dans le futur.", "erreur");
                dateCreation.focus();
                return;
            }

            if (prix) {
                const valeurPrix = Number(prix.value);
                if (prix.value.trim() === "" || !Number.isFinite(valeurPrix) || valeurPrix <= 0) {
                    event.preventDefault();
                    afficherMessage(message, "Le prix doit être un nombre fini supérieur à zéro.", "erreur");
                    prix.focus();
                    return;
                }
            }

            // Un nouveau fichier reste facultatif pendant la modification.
            // Si l'utilisateur en choisit un, le format et la taille sont contrôlés.
            if (configuration) {
                const champ = document.getElementById(configuration.idChamp);
                const fichiers = obtenirFichiersNonVides(champ);
                if (fichiers.length > 0) {
                    const probleme = verifierFichiersPourType(configuration, fichiers);
                    if (probleme) {
                        event.preventDefault();
                        afficherErreurFichier(configuration, probleme);
                        afficherMessage(message, probleme, "erreur");
                        if (champ) champ.focus();
                        return;
                    }
                }
            }

            afficherMessage(message, "");
        });
    }

    // Placer ces gestionnaires après les validateurs : ils ne désactivent le
    // bouton que si aucun contrôle précédent n'a empêché l'envoi.
    configurerPreventionDoubleEnvoi(formulaireConnexion, "Connexion en cours...");
    configurerPreventionDoubleEnvoi(formulaireInscription, "Création du compte...");
    configurerPreventionDoubleEnvoi(formulaireAjoutOeuvre, "Enregistrement en cours...");
    configurerPreventionDoubleEnvoi(formulaireModificationOeuvre, "Enregistrement en cours...");
});
