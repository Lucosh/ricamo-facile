"""User interface texts in Italian and English."""

TEXTS = {
    "app_title": ("Ricamo Facile", "Easy Embroidery"),
    "home": ("Inizio", "Home"),
    "back": ("Indietro", "Back"),
    "help": ("Aiuto", "Help"),
    "other_lang": ("English", "Italiano"),
    "home_hello": ("Ciao! Cosa vuoi ricamare oggi?", "Hello! What would you like to embroider today?"),
    "home_photo": ("Una mia foto", "My own photo"),
    "home_photo_sub": ("Trasforma una foto o un disegno\nin un ricamo",
                       "Turn a photo or a drawing\ninto embroidery"),
    "home_catalog": ("Ricami pronti", "Ready-made designs"),
    "home_catalog_sub": ("Scegli tra oltre {n}\ndisegni già pronti", "Choose from over {n}\nready-made designs"),
    "home_text": ("Scrivi un nome", "Write a name"),
    "home_text_sub": ("Nomi, iniziali\ne piccole scritte", "Names, initials\nand short words"),
    "home_note": ("I ricami vengono salvati come file .PES, il formato delle macchine da ricamo Brother e Baby Lock.",
                  "Designs are saved as .PES files, the format used by Brother and Baby Lock embroidery machines."),

    "choose_topic": ("Scegli un argomento", "Choose a topic"),
    "search_label": ("Cerca:", "Search:"),
    "search": ("Cerca", "Search"),
    "search_hint": ("Scrivi una parola, per esempio: gatto, rosa, cuore",
                    "Type a word, for example: cat, rose, heart"),
    "results_for": ("Risultati per «{q}»", "Results for “{q}”"),
    "no_results": ("Nessun ricamo trovato.\nProva con un'altra parola.", "No designs found.\nTry another word."),
    "designs_count": ("{n} ricami", "{n} designs"),
    "page": ("Pagina {a} di {b}", "Page {a} of {b}"),
    "prev": ("◀  Precedenti", "◀  Previous"),
    "next": ("Successivi  ▶", "Next  ▶"),
    "topics": ("Argomenti", "Topics"),

    "photo_title": ("Trasforma una tua foto in ricamo", "Turn your photo into embroidery"),
    "photo_intro": ("Premi il pulsante qui sotto e scegli una foto o un disegno dal computer.\n\n"
                    "Vengono meglio le immagini semplici: un disegno, un logo, un fiore, "
                    "un animale su sfondo chiaro, con pochi colori.",
                    "Press the button below and choose a photo or a drawing from your computer.\n\n"
                    "Simple pictures work best: a drawing, a logo, a flower, "
                    "an animal on a light background, with few colours."),
    "choose_photo": ("Scegli la foto", "Choose the photo"),
    "change_photo": ("Cambia foto", "Change photo"),
    "pictures": ("Immagini", "Pictures"),

    "step_size": ("1. Quanto grande?", "1. How big?"),
    "size_small": ("Piccolo\n5 cm", "Small\n5 cm"),
    "size_medium": ("Medio\n10 cm", "Medium\n10 cm"),
    "size_large": ("Grande\n13 × 18 cm", "Large\n13 × 18 cm"),
    "step_colors": ("2. Quanti colori?", "2. How many colours?"),
    "colors_few": ("Pochi\n4", "Few\n4"),
    "colors_normal": ("Normale\n6", "Normal\n6"),
    "colors_many": ("Tanti\n10", "Many\n10"),
    "step_background": ("3. Togliere lo sfondo?", "3. Remove the background?"),
    "yes": ("Sì", "Yes"),
    "no": ("No", "No"),
    "working": ("Sto preparando il ricamo…", "Preparing your embroidery…"),
    "info": ("Misura:  {w} × {h} cm\nPunti:  {s}\nTempo:  circa {m} minuti",
             "Size:  {w} × {h} cm\nStitches:  {s}\nTime:  about {m} minutes"),
    "threads_title": ("Fili da usare, in questo ordine:", "Threads to use, in this order:"),
    "brother": ("Brother", "Brother"),
    "large_warning": ("Attenzione: serve un telaio grande (13 × 18 cm).",
                      "Note: this needs a large hoop (13 × 18 cm)."),
    "original": ("Originale", "Original"),
    "save_usb": ("Salva sulla chiavetta USB  ({d})", "Save to the USB stick  ({d})"),
    "save_pc": ("Salva sul computer", "Save on this computer"),
    "no_usb": ("Inserisci una chiavetta USB per salvarci\ndirettamente il ricamo.",
               "Plug in a USB stick to save\nthe design straight onto it."),
    "saved_title": ("Fatto!", "Done!"),
    "saved_usb": ("Il ricamo è stato salvato sulla chiavetta USB con il nome:\n\n{name}\n\n"
                  "Ora togli la chiavetta e inseriscila nella macchina da ricamo.",
                  "The design has been saved on the USB stick as:\n\n{name}\n\n"
                  "Now unplug the stick and put it into your embroidery machine."),
    "saved_pc": ("Il ricamo è stato salvato qui:\n\n{path}\n\n"
                 "Copialo su una chiavetta USB per portarlo alla macchina da ricamo.",
                 "The design has been saved here:\n\n{path}\n\n"
                 "Copy it to a USB stick to take it to your embroidery machine."),
    "ok": ("Ho capito", "OK"),
    "oops": ("Ops!", "Oops!"),
    "error_open": ("Non riesco ad aprire questa foto.\nProva con un'altra immagine (JPG o PNG).",
                   "I can't open this picture.\nPlease try another one (JPG or PNG)."),
    "error_save": ("Non sono riuscito a salvare il file.\nControlla che la chiavetta sia inserita bene e riprova.",
                   "I couldn't save the file.\nCheck that the USB stick is plugged in properly and try again."),
    "error_convert": ("Non riesco a trasformare questa immagine.\nProva con un'altra foto.",
                      "I can't turn this picture into embroidery.\nPlease try another one."),

    "text_title": ("Scrivi un nome", "Write a name"),
    "text_label": ("1. Scrivi qui il nome o le iniziali:", "1. Type the name or the initials here:"),
    "text_font": ("2. Scegli la scrittura:", "2. Choose the lettering:"),
    "text_color": ("3. Scegli il colore:", "3. Choose the colour:"),
    "text_next": ("Vedi il ricamo  ▶", "See the embroidery  ▶"),
    "text_empty": ("Scrivi almeno una lettera.", "Please type at least one letter."),
    "text_default": ("Anna", "Anna"),

    "help_title": ("Come si usa", "How to use it"),
    "help_text": (
        "1.  Nella pagina iniziale scegli cosa vuoi ricamare:\n"
        "      • una tua foto o un disegno,\n"
        "      • un ricamo pronto dal catalogo,\n"
        "      • un nome o delle iniziali.\n\n"
        "2.  Scegli quanto deve essere grande il ricamo.\n"
        "      A sinistra vedi come verrà, punto per punto.\n\n"
        "3.  Inserisci la chiavetta USB nel computer e premi il pulsante verde\n"
        "      «Salva sulla chiavetta USB».\n\n"
        "4.  Togli la chiavetta, inseriscila nella macchina da ricamo\n"
        "      e scegli il file dal menu della macchina.\n\n"
        "5.  Prepara i fili nell'ordine indicato nell'elenco «Fili da usare».\n\n"
        "Per tornare all'inizio premi sempre il pulsante «Inizio» in alto a sinistra.",
        "1.  On the home page choose what you want to embroider:\n"
        "      • your own photo or drawing,\n"
        "      • a ready-made design from the catalogue,\n"
        "      • a name or initials.\n\n"
        "2.  Choose how big the design should be.\n"
        "      On the left you can see how it will look, stitch by stitch.\n\n"
        "3.  Plug the USB stick into the computer and press the green button\n"
        "      “Save to the USB stick”.\n\n"
        "4.  Unplug the stick, put it into the embroidery machine\n"
        "      and pick the file from the machine's menu.\n\n"
        "5.  Get the threads ready in the order shown under “Threads to use”.\n\n"
        "To go back to the start, press the “Home” button at the top left."),
}


class Translator:
    def __init__(self, lang="it"):
        self.lang = lang

    def __call__(self, key, **kw):
        it, en = TEXTS[key]
        s = it if self.lang == "it" else en
        return s.format(**kw) if kw else s
